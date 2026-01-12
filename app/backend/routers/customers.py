from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.backend.models.customer import Customer, CustomerCreate, CustomerUpdate
from app.backend.models.user import User
from app.backend.deps import get_current_active_user, get_db
from app.core.database import db as db_core
import uuid
from datetime import datetime
import pymongo

router = APIRouter()

@router.post("/", response_model=Customer)
def create_customer(
    customer_in: CustomerCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    # Auto-generate Customer Code (C001, C002...)
    count = db["customers"].count_documents({"account_id": current_user.account_id})
    new_code = f"C{str(count + 1).zfill(3)}"

    customer_doc = customer_in.dict()
    customer_doc["customer_id"] = str(uuid.uuid4())
    customer_doc["account_id"] = current_user.account_id
    customer_doc["customer_code"] = new_code
    customer_doc["created_at"] = datetime.utcnow()
    
    # Initialize balance
    customer_doc["current_balance"] = customer_doc.get("opening_balance", 0.0)

    db["customers"].insert_one(customer_doc)
    return db_core.serialize_doc(customer_doc)

@router.get("/", response_model=List[Customer])
def list_customers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    query = {"account_id": current_user.account_id, "status": {"$ne": "inactive"}}
    if search:
        query["$or"] = [
            {"customer_name": {"$regex": search, "$options": "i"}},
            {"customer_code": {"$regex": search, "$options": "i"}},
            {"contact_number": {"$regex": search, "$options": "i"}},
        ]
    
    customers = list(db["customers"].find(query).skip(skip).limit(limit).sort("created_at", pymongo.DESCENDING))
    return db_core.serialize_list(customers)

@router.get("/{customer_id}", response_model=Customer)
def get_customer(
    customer_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    customer = db["customers"].find_one({"customer_id": customer_id, "account_id": current_user.account_id})
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return db_core.serialize_doc(customer)

@router.put("/{customer_id}", response_model=Customer)
def update_customer(
    customer_id: str,
    customer_in: CustomerUpdate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    query = {"customer_id": customer_id, "account_id": current_user.account_id}
    customer = db["customers"].find_one(query)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    update_data = customer_in.dict(exclude_unset=True)
    if update_data:
        db["customers"].update_one(query, {"$set": update_data})
        customer = db["customers"].find_one(query)
    
    return db_core.serialize_doc(customer)

@router.delete("/{customer_id}")
def delete_customer(
    customer_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    query = {"customer_id": customer_id, "account_id": current_user.account_id}
    result = db["customers"].update_one(query, {"$set": {"status": "inactive"}})
    if result.modified_count == 0:
         raise HTTPException(status_code=404, detail="Customer not found")
    return {"message": "Customer deactivated successfully"}
