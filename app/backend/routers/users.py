from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from app.backend.models.user import User, UserInvite
from app.backend.deps import get_current_active_user, get_db
from app.core.database import db as db_core
from app.core.security import get_password_hash
import uuid
from datetime import datetime

router = APIRouter()

@router.get("/me", response_model=User)
def read_user_me(current_user: User = Depends(get_current_active_user)):
    return db_core.serialize_doc(current_user.dict())

@router.get("/", response_model=List[User])
def list_users(
    role: Optional[str] = Query(None),
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    query = {"account_id": current_user.account_id}
    if role:
        query["role"] = role
    
    users = list(db["users"].find(query))
    return db_core.serialize_list(users)

@router.post("/", response_model=User)
async def create_user(
    user_in: UserInvite,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    # Only owners and managers can create users
    if current_user.role not in ["owner", "manager"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    # 1. Check Plan Limits
    from app.backend.deps import check_plan_limit
    current_count = db["users"].count_documents({"account_id": current_user.account_id})
    await check_plan_limit(current_user.account_id, "users", current_count)

    # 2. Check if user already exists
    if db["users"].find_one({"email": user_in.email}):
        raise HTTPException(status_code=400, detail="User already exists")

    user_id = str(uuid.uuid4())
    user_doc = {
        "user_id": user_id,
        "account_id": current_user.account_id,
        "email": user_in.email,
        "full_name": user_in.full_name,
        "hashed_password": get_password_hash(user_in.password),
        "role": user_in.role,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    db["users"].insert_one(user_doc)
    return db_core.serialize_doc(user_doc)

@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    # Only owners can delete users
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can delete users")

    # Prevent self-deletion
    if user_id == current_user.user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    result = db["users"].delete_one({"user_id": user_id, "account_id": current_user.account_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted successfully"}
