from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.backend.models.weaver import Weaver, WeaverCreate, WeaverUpdate
from app.backend.models.user import User
from app.backend.deps import get_current_active_user, get_db
from app.core.database import db as db_core
import uuid
from datetime import datetime
import pymongo

router = APIRouter()

@router.post("/", response_model=Weaver)
def create_weaver(
    weaver_in: WeaverCreate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    # Auto-generate Weaver Code (W001, W002...)
    # 1. Start Transaction or just query lock (Mongo doesn't support easy auto-inc without dedicated counters)
    # For MVP, we count existing and add 1. Race condition possible but okay for Phase 1.
    count = db["weavers"].count_documents({"account_id": current_user.account_id})
    new_code = f"W{str(count + 1).zfill(3)}"

    weaver_doc = weaver_in.dict()
    weaver_doc["weaver_id"] = str(uuid.uuid4())
    weaver_doc["account_id"] = current_user.account_id
    weaver_doc["weaver_code"] = new_code
    weaver_doc["created_at"] = datetime.utcnow()
    
    # Initialize balance
    weaver_doc["current_balance"] = weaver_doc.get("opening_balance", 0.0)

    db["weavers"].insert_one(weaver_doc)
    return db_core.serialize_doc(weaver_doc)

@router.get("/", response_model=List[Weaver])
def list_weavers(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    query = {"account_id": current_user.account_id, "status": {"$ne": "inactive"}}
    if search:
        query["$or"] = [
            {"weaver_name": {"$regex": search, "$options": "i"}},
            {"weaver_code": {"$regex": search, "$options": "i"}},
        ]
    
    weavers = list(db["weavers"].find(query).skip(skip).limit(limit).sort("created_at", pymongo.DESCENDING))
    return db_core.serialize_list(weavers)

@router.get("/{weaver_id}", response_model=Weaver)
def get_weaver(
    weaver_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    weaver = db["weavers"].find_one({"weaver_id": weaver_id, "account_id": current_user.account_id})
    if not weaver:
        raise HTTPException(status_code=404, detail="Weaver not found")
    return db_core.serialize_doc(weaver)

@router.put("/{weaver_id}", response_model=Weaver)
def update_weaver(
    weaver_id: str,
    weaver_in: WeaverUpdate,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    query = {"weaver_id": weaver_id, "account_id": current_user.account_id}
    weaver = db["weavers"].find_one(query)
    if not weaver:
        raise HTTPException(status_code=404, detail="Weaver not found")

    update_data = weaver_in.dict(exclude_unset=True)
    if update_data:
        db["weavers"].update_one(query, {"$set": update_data})
        weaver = db["weavers"].find_one(query)
    
    return db_core.serialize_doc(weaver)

@router.delete("/{weaver_id}")
def delete_weaver(
    weaver_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    # Soft delete typically, but PRD says "Soft delete only" in Data Safety Rules.
    # So we update status to inactive or deleted.
    # Or actually, the delete endpoint can just set status='inactive'
    # But usually HTTP DELETE implies removal. I will use Soft Delete logic here.
    query = {"weaver_id": weaver_id, "account_id": current_user.account_id}
    result = db["weavers"].update_one(query, {"$set": {"status": "inactive"}})
    if result.modified_count == 0:
         raise HTTPException(status_code=404, detail="Weaver not found or already inactive")
    return {"message": "Weaver deactivated successfully"}
