from datetime import datetime
import uuid
from app.core.database import db
from app.core.security import get_password_hash
from app.core.config import settings
from dotenv import load_dotenv

def seed_users():
    load_dotenv()
    db.connect()
    if not db.client:
        print("Could not connect to database. Please check your IP Whitelist in Atlas.")
        return

    database = db.get_db()
    users_collection = database["users"]
    accounts_collection = database["accounts"]
    
    # Create a shared account for these demo users
    account_id = str(uuid.uuid4())
    account_doc = {
        "account_id": account_id,
        "subscription_type": "enterprise",
        "status": "active",
        "created_at": datetime.utcnow()
    }
    
    try:
        accounts_collection.insert_one(account_doc)
        print(f"Created demo account: {account_id}")
    except Exception as e:
        print(f"Account creation skipped or failed: {e}")

    demo_users = [
        ("admin@billing.com", "Admin@123", "Super Admin", "owner"),
        ("manager@billing.com", "Manager@123", "General Manager", "manager"),
        ("sales@billing.com", "Sales@123", "Sales Executive", "staff"),
        ("billing@billing.com", "Billing@123", "Billing Operations", "staff"),
        ("accountant@billing.com", "Account@123", "Lead Accountant", "staff")
    ]

    for email, password, name, role in demo_users:
        if users_collection.find_one({"email": email}):
            print(f"User {email} already exists. Skipping.")
            continue
            
        user_id = str(uuid.uuid4())
        user_doc = {
            "user_id": user_id,
            "account_id": account_id,
            "email": email,
            "full_name": name,
            "hashed_password": get_password_hash(password),
            "role": role,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        users_collection.insert_one(user_doc)
        print(f"Created user: {name} ({email}) with role: {role}")

    print("\nSeeding completed successfully!")

if __name__ == "__main__":
    seed_users()
