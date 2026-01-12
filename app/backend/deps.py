from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from app.core.config import settings
from app.backend.models.user import TokenData, User
from app.core.database import db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

def get_db():
    return db.get_db()

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except (JWTError, ValidationError):
        raise credentials_exception
    
    database = get_db()
    user = database["users"].find_one({"user_id": token_data.user_id})
    if user is None:
        raise credentials_exception
    
    # Fetch subscription info
    account = database["accounts"].find_one({"account_id": user["account_id"]})
    if account:
        user["subscription"] = {
            "plan": account.get("subscription_type", "free"),
            "status": account.get("status", "active")
        }
        
    return User(**user)

async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def check_plan_limit(account_id: str, limit_key: str, current_count: int):
    from app.core.plans import SUBSCRIPTION_PLANS
    database = db.get_db()
    account = database["accounts"].find_one({"account_id": account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    plan_key = account.get("subscription_type", "free")
    plan = SUBSCRIPTION_PLANS.get(plan_key, SUBSCRIPTION_PLANS["free"])
    limit = plan["limits"].get(limit_key)
    
    if limit != -1 and current_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You have reached the limit for {limit_key} in your {plan['name']} plan. Please upgrade to continue."
        )
