from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.backend.models.item import Item, ItemCreate, ItemUpdate
from app.backend.models.user import User
from app.backend.deps import get_current_active_user, get_db
from app.core.database import db as db_core
import uuid
from datetime import datetime
import pymongo

router = APIRouter()

@router.post("/", response_model=Item)
async def create_item(
    item_in: ItemCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    # Check Plan Limits
    from app.backend.deps import check_plan_limit
    current_count = db["items"].count_documents({"account_id": current_user.account_id, "status": {"$ne": "inactive"}})
    await check_plan_limit(current_user.account_id, "items", current_count)

    item_doc = item_in.dict()
    item_doc["item_id"] = str(uuid.uuid4())
    item_doc["account_id"] = current_user.account_id
    item_doc["created_at"] = datetime.utcnow()
    
    # Initialize stock
    item_doc["current_stock"] = item_doc.get("opening_stock", 0.0)

    db["items"].insert_one(item_doc)
    return db_core.serialize_doc(item_doc)

@router.get("/", response_model=List[Item])
def list_items(
    search: Optional[str] = None,
    category_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    query = {"account_id": current_user.account_id, "status": {"$ne": "inactive"}}
    if search:
        query["$or"] = [
            {"item_name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
        ]
    if category_id:
        query["category_id"] = category_id
    
    items = list(db["items"].find(query).sort("item_name", pymongo.ASCENDING))
    return db_core.serialize_list(items)

@router.get("/{item_id}", response_model=Item)
def get_item(
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    item = db["items"].find_one({"item_id": item_id, "account_id": current_user.account_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_core.serialize_doc(item)

@router.put("/{item_id}", response_model=Item)
def update_item(
    item_id: str,
    item_in: ItemUpdate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    print(f"DEBUG: Entering update_item for {item_id}")
    query = {"item_id": item_id, "account_id": current_user.account_id}
    old_item = db["items"].find_one(query)
    if not old_item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = item_in.dict(exclude_unset=True)
    
    # If opening stock is updated, we might want to update current stock too
    # but only if there are no stock movements/transactions yet.
    if "opening_stock" in update_data:
        # Check if any stock transactions exist for this item
        transaction_count = db["stock_transactions"].count_documents({"item_id": item_id, "account_id": current_user.account_id})
        
        curr = float(old_item.get("current_stock") or 0)
        old_open = float(old_item.get("opening_stock") or 0)
        
        # Sync current stock if no transactions yet OR if they were identical before
        if transaction_count == 0 or curr == old_open:
             update_data["current_stock"] = update_data["opening_stock"]

    update_data["updated_at"] = datetime.utcnow()
    db["items"].update_one(query, {"$set": update_data})
    
    return db_core.serialize_doc(db["items"].find_one(query))

@router.delete("/{item_id}")
def delete_item(
    item_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    # In a real app, check if item has transaction history
    db["items"].update_one(
        {"item_id": item_id, "account_id": current_user.account_id},
        {"$set": {"status": "inactive"}}
    )
    return {"message": "Item deactivated"}
