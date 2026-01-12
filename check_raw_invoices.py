from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

def check_raw_data():
    uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DATABASE_NAME")
    print(f"Connecting to {db_name}...")
    client = MongoClient(uri)
    db = client[db_name]
    
    # 1. Check all account IDs in invoices
    distinct_accounts = db.invoices.distinct("account_id")
    print(f"Distinct account IDs in invoices: {distinct_accounts}")
    
    # 2. Check admin user's account ID
    admin = db.users.find_one({"email": "admin@billing.com"})
    if admin:
        print(f"Admin User Account ID: {admin['account_id']}")
    else:
        print("Admin user NOT found")
        
    # 3. Print a sample invoice
    sample = db.invoices.find_one()
    if sample:
        print("Sample Invoice Data:")
        # remove large items list for brevity
        if "items" in sample:
            sample["items_count"] = len(sample["items"])
            del sample["items"]
        print(sample)
    else:
        print("No invoices found in collection.")

if __name__ == "__main__":
    check_raw_data()
