from datetime import datetime
import uuid
from app.core.database import db
from app.core.security import get_password_hash

def ensure_admin_exists():
    database = db.get_db()
    users_collection = database["users"]
    accounts_collection = database["accounts"]
    orgs_collection = database["organizations"]

    email = "admin@billing.com"
    password = "admin123"

    user = users_collection.find_one({"email": email})

    if not user:
        print("No admin user found. Creating default admin...")
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
            "email": email,
            "full_name": "Admin User",
            "hashed_password": get_password_hash(password),
            "role": "owner",
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        users_collection.insert_one(user_doc)
        user = user_doc
    
    # 3. Ensure Account and Org exist for the user's account_id
    account_id = user["account_id"]
    
    if not accounts_collection.find_one({"account_id": account_id}):
        print(f"Repairing missing account for {email}...")
        accounts_collection.insert_one({
            "account_id": account_id,
            "subscription_type": "free",
            "status": "active",
            "created_at": datetime.utcnow()
        })

    if not orgs_collection.find_one({"account_id": account_id}):
        print(f"Repairing missing organization for {email}...")
        orgs_collection.insert_one({
            "organization_id": str(uuid.uuid4()),
            "account_id": account_id,
            "company_name": "Billing Admin Org",
            "created_at": datetime.utcnow()
        })

    print(f"Default Admin check complete for: {email}")
