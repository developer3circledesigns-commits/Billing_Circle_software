from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.backend.models.purchase_bill import PurchaseBill, PurchaseBillCreate, PurchaseBillUpdate
from app.backend.models.user import User
from app.backend.deps import get_current_active_user, get_db
from app.core.database import db as db_core
import uuid
from datetime import datetime
import pymongo

router = APIRouter()

@router.post("/", response_model=PurchaseBill)
def create_purchase_bill(
    bill_in: PurchaseBillCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Create a new purchase bill, update weaver balance, increment item stock, 
    and log stock transactions.
    """
    # 1. Improved Bill Numbering
    last_bill = db["purchase_bills"].find_one(
        {"account_id": current_user.account_id},
        sort=[("created_at", pymongo.DESCENDING)]
    )
    
    new_num = 1
    if last_bill and "bill_number" in last_bill:
        try:
            parts = last_bill["bill_number"].split('-')
            if len(parts) > 1:
                new_num = int(parts[1]) + 1
            else:
                new_num = db["purchase_bills"].count_documents({"account_id": current_user.account_id}) + 1
        except (ValueError, IndexError):
            new_num = db["purchase_bills"].count_documents({"account_id": current_user.account_id}) + 1
    
    bill_number = f"BILL-{str(new_num).zfill(4)}"
    
    bill_doc = bill_in.dict()
    bill_doc.update({
        "bill_id": str(uuid.uuid4()),
        "account_id": current_user.account_id,
        "bill_number": bill_number,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "balance_amount": bill_in.total_amount,
        "paid_amount": 0.0
    })
    
    # 2. Update weaver outstanding balance
    db["weavers"].update_one(
        {"weaver_id": bill_in.weaver_id, "account_id": current_user.account_id},
        {"$inc": {"current_balance": bill_doc["total_amount"]}}
    )
    
    # 3. Increment Stock and Log Transactions
    for item in bill_in.items:
        db["items"].update_one(
            {"item_id": item.item_id, "account_id": current_user.account_id},
            {
                "$inc": {"current_stock": item.qty},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Stock Transaction Log
        stock_transaction = {
            "transaction_id": str(uuid.uuid4()),
            "item_id": item.item_id,
            "item_name": item.item_name,
            "bill_id": bill_doc["bill_id"],
            "bill_number": bill_number,
            "account_id": current_user.account_id,
            "transaction_type": "in",
            "quantity": item.qty,
            "transaction_date": datetime.utcnow(),
            "notes": f"Purchased via bill {bill_number}"
        }
        db["stock_transactions"].insert_one(stock_transaction)

    db["purchase_bills"].insert_one(bill_doc)
    return db_core.serialize_doc(bill_doc)

@router.get("/", response_model=List[PurchaseBill])
def list_purchase_bills(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    payment_status: Optional[str] = None,
    weaver_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """List bills with filtering. Overdue status is calculated dynamically in UI or separate worker."""
    query = {"account_id": current_user.account_id}
    
    if search:
        query["$or"] = [
            {"bill_number": {"$regex": search, "$options": "i"}},
            {"weaver_name": {"$regex": search, "$options": "i"}},
            {"vendor_bill_number": {"$regex": search, "$options": "i"}},
        ]
    
    if payment_status:
        query["payment_status"] = payment_status
    
    if weaver_id:
        query["weaver_id"] = weaver_id
    
    bills = list(db["purchase_bills"].find(query)
                .skip(skip)
                .limit(limit)
                .sort("created_at", pymongo.DESCENDING))
    
    return db_core.serialize_list(bills)

@router.get("/overdue", response_model=List[PurchaseBill])
def get_overdue_bills(
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Get all overdue bills"""
    query = {
        "account_id": current_user.account_id,
        "payment_status": {"$in": ["unpaid", "partial"]},
        "due_date": {"$lt": datetime.utcnow()}
    }
    bills = list(db["purchase_bills"].find(query).sort("due_date", pymongo.ASCENDING))
    return db_core.serialize_list(bills)

@router.get("/{bill_id}", response_model=PurchaseBill)
def get_purchase_bill(
    bill_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    bill = db["purchase_bills"].find_one({"bill_id": bill_id, "account_id": current_user.account_id})
    if not bill:
        raise HTTPException(status_code=404, detail="Purchase Bill not found")
    return db_core.serialize_doc(bill)

@router.put("/{bill_id}", response_model=PurchaseBill)
async def update_purchase_bill(
    bill_id: str,
    bill_in: PurchaseBillUpdate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Update purchase bill details, including items and stock adjustments.
    Update weaver balance accordingly.
    """
    try:
        query = {"bill_id": bill_id, "account_id": current_user.account_id}
        old_bill = db["purchase_bills"].find_one(query)
        
        if not old_bill:
            raise HTTPException(status_code=404, detail="Purchase Bill not found")
        
        update_data = bill_in.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        # Handle Weaver Balance Reversal for OLD amount
        if "total_amount" in update_data and update_data["total_amount"] != old_bill["total_amount"]:
            diff = update_data["total_amount"] - old_bill["total_amount"]
            db["weavers"].update_one(
                {"weaver_id": old_bill["weaver_id"], "account_id": current_user.account_id},
                {"$inc": {"current_balance": diff}}
            )

        # Handle Item and Stock Updates
        if "items" in update_data:
            # 1. Revert stock for all OLD items
            for old_item in old_bill.get("items", []):
                db["items"].update_one(
                    {"item_id": old_item["item_id"], "account_id": current_user.account_id},
                    {"$inc": {"current_stock": -old_item["qty"]}} # Note: In Bills, inward stock is POSITIVE. So we INC with NEGATIVE qty to revert.
                )
                # Log Reversal
                db["stock_transactions"].insert_one({
                    "transaction_id": str(uuid.uuid4()),
                    "item_id": old_item["item_id"],
                    "item_name": old_item["item_name"],
                    "bill_id": bill_id,
                    "account_id": current_user.account_id,
                    "transaction_type": "out", # Reverting an inward transaction is an 'out' movement
                    "quantity": old_item["qty"],
                    "transaction_date": datetime.utcnow(),
                    "notes": f"Stock reverted for bill update: {old_bill.get('bill_number')}"
                })

            # 2. Add stock for NEW items
            for new_item in update_data["items"]:
                db["items"].update_one(
                    {"item_id": new_item["item_id"], "account_id": current_user.account_id},
                    {"$inc": {"current_stock": new_item["qty"]}},
                    upsert=True # Just in case, though items should exist
                )
                # Log New Addition
                db["stock_transactions"].insert_one({
                    "transaction_id": str(uuid.uuid4()),
                    "item_id": new_item["item_id"],
                    "item_name": new_item["item_name"],
                    "bill_id": bill_id,
                    "account_id": current_user.account_id,
                    "transaction_type": "in",
                    "quantity": new_item["qty"],
                    "transaction_date": datetime.utcnow(),
                    "notes": f"Stock added for bill update: {old_bill.get('bill_number')}"
                })

        if update_data:
            db["purchase_bills"].update_one(query, {"$set": update_data})
        
        updated_bill = db["purchase_bills"].find_one(query)
        return db_core.serialize_doc(updated_bill)
        
    except Exception as e:
        print(f"Error updating purchase bill: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating purchase bill: {str(e)}"
        )

@router.delete("/{bill_id}")
def delete_purchase_bill(
    bill_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Delete bill and adjust weaver balance"""
    query = {"bill_id": bill_id, "account_id": current_user.account_id}
    bill = db["purchase_bills"].find_one(query)
    if not bill:
        raise HTTPException(status_code=404, detail="Purchase Bill not found")
    
    # Adjust weaver balance
    db["weavers"].update_one(
        {"weaver_id": bill["weaver_id"], "account_id": current_user.account_id},
        {"$inc": {"current_balance": -bill["balance_amount"]}}
    )
    
    db["purchase_bills"].delete_one(query)
    return {"message": "Purchase Bill deleted successfully"}

@router.get("/by-weaver/{weaver_id}", response_model=List[PurchaseBill])
def get_bills_by_weaver(
    weaver_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Get all bills for a specific weaver"""
    query = {"weaver_id": weaver_id, "account_id": current_user.account_id}
    bills = list(db["purchase_bills"].find(query).sort("created_at", pymongo.DESCENDING))
    return db_core.serialize_list(bills)
