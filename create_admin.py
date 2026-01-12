import asyncio
from datetime import datetime
import uuid
from pymongo import MongoClient
from app.core.config import settings
from app.core.security import get_password_hash

def create_admin():
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.DATABASE_NAME]
    
    users_collection = db["users"]
    accounts_collection = db["accounts"]
    orgs_collection = db["organizations"]

    email = "admin@billing.com"
    password = "admin123"

    if users_collection.find_one({"email": email}):
        print(f"User {email} already exists.")
        return

    # 1. Create New Account (Multi-tenant Root)
    account_id = str(uuid.uuid4())
    account_doc = {
        "account_id": account_id,
        "subscription_type": "premium",
        "status": "active",
        "created_at": datetime.utcnow()
    }
    accounts_collection.insert_one(account_doc)

    # 2. Create User linked to Account
    user_id = str(uuid.uuid4())
    user_doc = {
        "user_id": user_id,
        "account_id": account_id,
        "email": email,
        "full_name": "Admin User",
        "hashed_password": get_password_hash(password),
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
        "company_name": "Billing Admin Org",
        "created_at": datetime.utcnow()
    }
    orgs_collection.insert_one(org_doc)

    print(f"Admin user created successfully.")
    print(f"Username: {email}")
    print(f"Password: {password}")

if __name__ == "__main__":
    create_admin()
