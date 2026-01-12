from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.backend.models.purchase_order import PurchaseOrder, PurchaseOrderCreate, PurchaseOrderUpdate
from app.backend.models.user import User
from app.backend.deps import get_current_active_user, get_db
from app.core.database import db as db_core
import uuid
from datetime import datetime
import pymongo

router = APIRouter()

@router.post("/", response_model=PurchaseOrder)
def create_purchase_order(
    po_in: PurchaseOrderCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    # Auto-generate PO Number (PO-001, PO-002...)
    count = db["purchase_orders"].count_documents({"account_id": current_user.account_id})
    po_number = f"PO-{str(count + 1).zfill(3)}"
    
    po_doc = po_in.dict()
    po_doc["po_id"] = str(uuid.uuid4())
    po_doc["account_id"] = current_user.account_id
    po_doc["po_number"] = po_number
    po_doc["created_at"] = datetime.utcnow()
    po_doc["updated_at"] = datetime.utcnow()
    
    # Calculate pending qty from items
    total_qty = sum(item["qty"] for item in po_doc["items"])
    po_doc["pending_qty"] = total_qty
    po_doc["received_qty"] = 0.0
    
    db["purchase_orders"].insert_one(po_doc)
    return db_core.serialize_doc(po_doc)

@router.get("/", response_model=List[PurchaseOrder])
def list_purchase_orders(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    status: Optional[str] = None,
    weaver_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    query = {"account_id": current_user.account_id}
    
    if search:
        query["$or"] = [
            {"po_number": {"$regex": search, "$options": "i"}},
            {"weaver_name": {"$regex": search, "$options": "i"}},
        ]
    
    if status:
        query["status"] = status
    
    if weaver_id:
        query["weaver_id"] = weaver_id
    
    pos = list(db["purchase_orders"].find(query).skip(skip).limit(limit).sort("created_at", pymongo.DESCENDING))
    return db_core.serialize_list(pos)

@router.get("/{po_id}", response_model=PurchaseOrder)
def get_purchase_order(
    po_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    po = db["purchase_orders"].find_one({"po_id": po_id, "account_id": current_user.account_id})
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    return db_core.serialize_doc(po)

@router.put("/{po_id}", response_model=PurchaseOrder)
async def update_purchase_order(
    po_id: str,
    po_in: PurchaseOrderUpdate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """
    Update purchase order details, including item list and pending qty recalculation.
    """
    try:
        query = {"po_id": po_id, "account_id": current_user.account_id}
        old_po = db["purchase_orders"].find_one(query)
        if not old_po:
            raise HTTPException(status_code=404, detail="Purchase Order not found")
        
        update_data = po_in.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        if "items" in update_data:
            # Recalculate total and pending qty
            total_qty = sum(item["qty"] for item in update_data["items"])
            update_data["pending_qty"] = max(0, total_qty - old_po.get("received_qty", 0))
            # In a real app, you might want to compare item-by-item received status, 
            # but for this MVP, we use the aggregate.
        
        if update_data:
            db["purchase_orders"].update_one(query, {"$set": update_data})
            po = db["purchase_orders"].find_one(query)
        
        return db_core.serialize_doc(po)
    except Exception as e:
        print(f"Error updating PO: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating PO: {str(e)}"
        )

@router.put("/{po_id}/status", response_model=PurchaseOrder)
def update_po_status(
    po_id: str,
    new_status: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Update PO status: draft -> sent -> confirmed -> received"""
    query = {"po_id": po_id, "account_id": current_user.account_id}
    po = db["purchase_orders"].find_one(query)
    if not po:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    
    update_data = {
        "status": new_status,
        "updated_at": datetime.utcnow()
    }
    
    # If marking as received, update inventory and log transactions
    if new_status == "received":
        for item in po["items"]:
            db["items"].update_one(
                {"item_id": item["item_id"], "account_id": current_user.account_id},
                {"$inc": {"current_stock": item["qty"]}}
            )
            
            # Stock Transaction Log
            stock_transaction = {
                "transaction_id": str(uuid.uuid4()),
                "item_id": item["item_id"],
                "item_name": item["item_name"],
                "po_id": po_id,
                "po_number": po.get("po_number"),
                "account_id": current_user.account_id,
                "transaction_type": "in",
                "quantity": item["qty"],
                "transaction_date": datetime.utcnow(),
                "notes": f"Received via PO {po.get('po_number')}"
            }
            db["stock_transactions"].insert_one(stock_transaction)
            
        update_data["received_qty"] = po.get("pending_qty", 0)
        update_data["pending_qty"] = 0.0
    
    db["purchase_orders"].update_one(query, {"$set": update_data})
    po = db["purchase_orders"].find_one(query)
    
    return db_core.serialize_doc(po)

@router.delete("/{po_id}")
def delete_purchase_order(
    po_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Soft delete - mark as cancelled"""
    query = {"po_id": po_id, "account_id": current_user.account_id}
    result = db["purchase_orders"].update_one(
        query, 
        {"$set": {"status": "cancelled", "updated_at": datetime.utcnow()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Purchase Order not found")
    return {"message": "Purchase Order cancelled successfully"}

@router.get("/by-weaver/{weaver_id}", response_model=List[PurchaseOrder])
def get_pos_by_weaver(
    weaver_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    """Get all purchase orders for a specific weaver"""
    query = {"weaver_id": weaver_id, "account_id": current_user.account_id}
    pos = list(db["purchase_orders"].find(query).sort("created_at", pymongo.DESCENDING))
    return db_core.serialize_list(pos)
