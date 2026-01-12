from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.backend.models.vendor_payment import VendorPayment, VendorPaymentCreate, VendorPaymentUpdate
from app.backend.models.user import User
from app.backend.deps import get_current_active_user, get_db
from app.core.database import db as db_core
import uuid
from datetime import datetime
import pymongo

router = APIRouter()

@router.post("/", response_model=VendorPayment)
def create_vendor_payment(
    payment_in: VendorPaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    # Auto-generate Payment Number (VPAY-001, VPAY-002...)
    count = db["vendor_payments"].count_documents({"account_id": current_user.account_id})
    payment_number = f"VPAY-{str(count + 1).zfill(3)}"
    
    payment_doc = payment_in.dict()
    payment_doc["payment_id"] = str(uuid.uuid4())
    payment_doc["account_id"] = current_user.account_id
    payment_doc["payment_number"] = payment_number
    payment_doc["created_at"] = datetime.utcnow()
    
    # Update weaver balance
    db["weavers"].update_one(
        {"weaver_id": payment_in.weaver_id, "account_id": current_user.account_id},
        {"$inc": {"current_balance": -payment_in.amount}}
    )
    
    # If payment is for a specific bill, update bill
    if payment_in.bill_id:
        bill = db["purchase_bills"].find_one({
            "bill_id": payment_in.bill_id, 
            "account_id": current_user.account_id
        })
        if bill:
            new_paid = bill.get("paid_amount", 0) + payment_in.amount
            new_balance = bill["total_amount"] - new_paid
            
            # Determine payment status
            if new_balance <= 0:
                p_status = "paid"
                new_balance = 0
            elif new_paid > 0:
                p_status = "partial"
            else:
                p_status = "unpaid"
            
            db["purchase_bills"].update_one(
                {"bill_id": payment_in.bill_id},
                {"$set": {
                    "paid_amount": new_paid,
                    "balance_amount": new_balance,
                    "payment_status": p_status
                }}
            )
    
    db["vendor_payments"].insert_one(payment_doc)
    return db_core.serialize_doc(payment_doc)

@router.get("/", response_model=List[VendorPayment])
def list_vendor_payments(
    skip: int = 0,
    limit: int = 100,
    weaver_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    query = {"account_id": current_user.account_id}
    
    if weaver_id:
        query["weaver_id"] = weaver_id
    
    payments = list(db["vendor_payments"].find(query).skip(skip).limit(limit).sort("payment_date", pymongo.DESCENDING))
    return db_core.serialize_list(payments)

@router.get("/by-weaver/{weaver_id}", response_model=List[VendorPayment])
def get_payments_by_weaver(
    weaver_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Get payment history for a specific weaver"""
    query = {"weaver_id": weaver_id, "account_id": current_user.account_id}
    payments = list(db["vendor_payments"].find(query).sort("payment_date", pymongo.DESCENDING))
    return db_core.serialize_list(payments)

@router.get("/by-bill/{bill_id}", response_model=List[VendorPayment])
def get_payments_by_bill(
    bill_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Get all payments for a specific bill"""
    query = {"bill_id": bill_id, "account_id": current_user.account_id}
    payments = list(db["vendor_payments"].find(query).sort("payment_date", pymongo.DESCENDING))
    return db_core.serialize_list(payments)

@router.delete("/{payment_id}")
def delete_vendor_payment(
    payment_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Delete payment and revert balances"""
    query = {"payment_id": payment_id, "account_id": current_user.account_id}
    payment = db["vendor_payments"].find_one(query)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Revert weaver balance
    db["weavers"].update_one(
        {"weaver_id": payment["weaver_id"], "account_id": current_user.account_id},
        {"$inc": {"current_balance": payment["amount"]}}
    )
    
    # Revert bill payment if applicable
    if payment.get("bill_id"):
        bill = db["purchase_bills"].find_one({
            "bill_id": payment["bill_id"],
            "account_id": current_user.account_id
        })
        if bill:
            new_paid = bill.get("paid_amount", 0) - payment["amount"]
            new_balance = bill["total_amount"] - new_paid
            
            if new_balance <= 0:
                p_status = "paid"
            elif new_paid > 0:
                p_status = "partial"
            else:
                p_status = "unpaid"
            
            db["purchase_bills"].update_one(
                {"bill_id": payment["bill_id"]},
                {"$set": {
                    "paid_amount": new_paid,
                    "balance_amount": new_balance,
                    "payment_status": p_status
                }}
            )
    
    db["vendor_payments"].delete_one(query)
    return {"message": "Payment deleted successfully"}
