from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.backend.models.user import UserCreate, Token, UserInDB
from datetime import timedelta
from app.core.config import settings
import uuid
from datetime import datetime

router = APIRouter()

@router.post("/signup", response_model=Token)
def signup(user_in: UserCreate):
    database = db.get_db()
    users_collection = database["users"]
    accounts_collection = database["accounts"]
    orgs_collection = database["organizations"]

    # RESTRICTION: Only allow the first user to be created via /signup
    # This prevents unauthorized user creation once the system is set up.
    if users_collection.count_documents({}) > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Signup is disabled. An administrator already exists.",
        )

    # Check if user already exists (redundant but safe)
    if users_collection.find_one({"email": user_in.email}):
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )

    # 1. Create New Account (Multi-tenant Root)
    account_id = str(uuid.uuid4())
    account_doc = {
        "account_id": account_id,
        "subscription_type": "free",
        "status": "active",
        "created_at": datetime.utcnow()
    }
    accounts_collection.insert_one(account_doc)

    # 2. Create User linked to Account
    user_id = str(uuid.uuid4())
    user_doc = {
        "user_id": user_id,
        "account_id": account_id,
        "email": user_in.email,
        "full_name": user_in.full_name,
        "hashed_password": get_password_hash(user_in.password),
        "role": "owner",
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    users_collection.insert_one(user_doc)

    # 3. Create Default Organization
    org_id = str(uuid.uuid4())
    org_doc = {
        "organization_id": org_id,
        "account_id": account_id,
        "company_name": user_in.organization_name,
        "created_at": datetime.utcnow()
    }
    orgs_collection.insert_one(org_doc)

    # 4. Generate Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user_id, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    database = db.get_db()
    users_collection = database["users"]
    
    user_doc = users_collection.find_one({"email": form_data.username})
    if not user_doc or not verify_password(form_data.password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user_doc.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user_doc["user_id"], expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

from app.backend.models.user import User
from app.backend.deps import get_current_active_user

@router.get("/organization")
def get_organization(
    current_user: User = Depends(get_current_active_user),
):
    database = db.get_db()
    org = database["organizations"].find_one({"account_id": current_user.account_id})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    org["_id"] = str(org["_id"])
    return org

@router.put("/organization")
def update_organization(
    org_update: dict,
    current_user: User = Depends(get_current_active_user),
):
    # Only owners/managers can update org
    if current_user.role not in ["owner", "manager"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    database = db.get_db()
    orgs_collection = database["organizations"]
    
    # We restrict update to specific fields for safety
    allowed_fields = ["company_name", "gstin", "email", "phone", "address"]
    update_data = {k: v for k, v in org_update.items() if k in allowed_fields}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
        
    result = orgs_collection.update_one(
        {"account_id": current_user.account_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Organization not found")
        
    return {"message": "Organization updated successfully"}
