from fastapi import APIRouter, Depends, HTTPException, status
from app.backend.models.user import User
from app.backend.deps import get_current_active_user, get_db
from app.core.plans import SUBSCRIPTION_PLANS
from datetime import datetime

router = APIRouter()

@router.get("/plans")
def get_plans():
    return SUBSCRIPTION_PLANS

@router.get("/status")
def get_subscription_status(
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    account = db["accounts"].find_one({"account_id": current_user.account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Calculate usage
    usage = {
        "invoices": db["invoices"].count_documents({"account_id": current_user.account_id, "status": {"$ne": "cancelled"}}),
        "quotations": db["quotations"].count_documents({"account_id": current_user.account_id}),
        "items": db["items"].count_documents({"account_id": current_user.account_id, "status": {"$ne": "inactive"}}),
        "users": db["users"].count_documents({"account_id": current_user.account_id})
    }
    
    plan_key = account.get("subscription_type", "free")
    plan_details = SUBSCRIPTION_PLANS.get(plan_key, SUBSCRIPTION_PLANS["free"])
    
    created_at = account.get("created_at")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()

    return {
        "plan": plan_key,
        "details": plan_details,
        "usage": usage,
        "status": account.get("status", "active"),
        "created_at": created_at
    }

@router.post("/upgrade")
def upgrade_subscription(
    plan: str,
    current_user: User = Depends(get_current_active_user),
    db=Depends(get_db)
):
    if current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Only owners can upgrade subscriptions")
    
    if plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan selected")
    
    db["accounts"].update_one(
        {"account_id": current_user.account_id},
        {"$set": {
            "subscription_type": plan,
            "status": "active",
            "updated_at": datetime.utcnow()
        }}
    )
    
    return {"message": f"Successfully upgraded to {SUBSCRIPTION_PLANS[plan]['name']}"}
