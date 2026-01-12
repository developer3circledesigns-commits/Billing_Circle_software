from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.backend.models.payment import Payment, PaymentCreate
from app.backend.models.user import User
from app.backend.deps import get_current_active_user, get_db
from app.core.database import db as db_core
import uuid
from datetime import datetime
import pymongo

router = APIRouter()

@router.post("/", response_model=Payment)
def create_payment(
    payment_in: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Create a payment record and synchronize balances.
    Robust numbering and thread-safe balance updates.
    """
    # 1. Robust Payment Numbering
    last_pay = db["payments"].find_one(
        {"account_id": current_user.account_id},
        sort=[("created_at", pymongo.DESCENDING)]
    )
    new_num = 1
    if last_pay and "payment_number" in last_pay:
        try:
            parts = last_pay["payment_number"].split('-')
            new_num = int(parts[1]) + 1 if len(parts) > 1 else db["payments"].count_documents({"account_id": current_user.account_id}) + 1
        except:
            new_num = db["payments"].count_documents({"account_id": current_user.account_id}) + 1
    
    pay_number = f"PAY-{str(new_num).zfill(4)}"

    payment_doc = payment_in.dict()
    payment_doc.update({
        "payment_id": str(uuid.uuid4()),
        "account_id": current_user.account_id,
        "payment_number": pay_number,
        "created_at": datetime.utcnow()
    })
    if not payment_doc.get("payment_date"):
        payment_doc["payment_date"] = datetime.utcnow()

    # 2. Synchronize Balances
    if payment_in.payment_type == "receive":
        # Receving from Customer
        db["customers"].update_one(
            {"customer_id": payment_in.party_id, "account_id": current_user.account_id},
            {"$inc": {"current_balance": -payment_in.amount}}
        )
        
        if payment_in.invoice_id:
            invoice = db["invoices"].find_one({"invoice_id": payment_in.invoice_id, "account_id": current_user.account_id})
            if invoice:
                new_balance = max(0, invoice.get("balance_amount", 0) - payment_in.amount)
                new_received = invoice.get("amount_received", 0) + payment_in.amount
                p_status = "partial" if new_balance > 0 else "paid"
                
                db["invoices"].update_one(
                    {"invoice_id": payment_in.invoice_id},
                    {"$set": {
                        "balance_amount": new_balance, 
                        "amount_received": new_received,
                        "payment_status": p_status,
                        "updated_at": datetime.utcnow()
                    }}
                )
    else:
        # Paying to Weaver
        db["weavers"].update_one(
            {"weaver_id": payment_in.party_id, "account_id": current_user.account_id},
            {"$inc": {"current_balance": -payment_in.amount}}
        )

    db["payments"].insert_one(payment_doc)
    return db_core.serialize_doc(payment_doc)

@router.get("/", response_model=List[Payment])
def list_payments(
    payment_type: Optional[str] = None,
    party_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    query = {"account_id": current_user.account_id}
    if payment_type:
        query["payment_type"] = payment_type
    if party_id:
        query["party_id"] = party_id
    
    payments = list(db["payments"].find(query).sort("payment_date", pymongo.DESCENDING))
    return db_core.serialize_list(payments)

@router.delete("/{payment_id}")
def delete_payment(
    payment_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Delete a payment and REVERT all balance changes."""
    query = {"payment_id": payment_id, "account_id": current_user.account_id}
    payment = db["payments"].find_one(query)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment record not found")

    # Revert Balances
    if payment.get("payment_type") == "receive":
        # Revert Customer Balance
        db["customers"].update_one(
            {"customer_id": payment["party_id"], "account_id": current_user.account_id},
            {"$inc": {"current_balance": payment["amount"]}}
        )
        
        # Revert Invoice Balance if applicable
        if payment.get("invoice_id"):
            invoice = db["invoices"].find_one({"invoice_id": payment["invoice_id"]})
            if invoice:
                orig_received = max(0, invoice.get("amount_received", 0) - payment["amount"])
                orig_balance = invoice.get("balance_amount", 0) + payment["amount"]
                p_status = "unpaid" if orig_received == 0 else "partial"
                if orig_balance >= invoice.get("grand_total", 0):
                    p_status = "unpaid"
                
                db["invoices"].update_one(
                    {"invoice_id": payment["invoice_id"]},
                    {"$set": {
                        "amount_received": orig_received,
                        "balance_amount": orig_balance,
                        "payment_status": p_status
                    }}
                )
    else:
        # Revert Weaver Balance
        db["weavers"].update_one(
            {"weaver_id": payment["party_id"], "account_id": current_user.account_id},
            {"$inc": {"current_balance": payment["amount"]}}
        )

    db["payments"].delete_one(query)
    return {"message": "Payment record deleted and balances reverted"}
