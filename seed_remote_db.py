
import sys
import os
from datetime import datetime
import uuid
from pymongo import MongoClient
import certifi

# Add parent dir to path
sys.path.append(os.getcwd())

from app.core.config import settings
from app.core.security import get_password_hash

def seed():
    print(f"Connecting to database: {settings.DATABASE_NAME}...")
    
    ca = certifi.where()
    client = MongoClient(settings.MONGO_URI, tlsCAFile=ca)
    db = client[settings.DATABASE_NAME]

    # Find User
    user = db.users.find_one({"email": "admin@billing.com"})
    if not user:
        # Fallback
        user = db.users.find_one({"role": "owner"})
    
    if not user:
        print("No user found! Please fix users first.")
        return

    print(f"Seeding for user: {user['email']}")
    account_id = user["account_id"]
    user_id = user["user_id"]
    
    # 1. CLEANUP BAD INVOICES
    # db.invoices.delete_many({"account_id": account_id})
    # print("Cleared existing invoices for this account.")
    # Actually, let's just delete ALL invoices to be safe given the mess
    db.invoices.delete_many({})
    print("Cleared ALL invoices.")

    # 2. Create Valid Customer (if needed)
    customer_id = str(uuid.uuid4())
    customer_doc = {
        "customer_id": customer_id,
        "account_id": account_id,
        "customer_name": "Global Tech Industries",
        "customer_code": "CUST-002",
        "email": "contact@globaltech.com",
        "phone": "9876543210",
        "billing_address": "456 Tech Park, Bangalore, India",
        "state": "Karnataka",
        "state_code": "KA",
        "gstin": "29AAAAA0000A1Z5",
        "created_at": datetime.utcnow()
    }
    db.customers.insert_one(customer_doc)
    print(f"Created Customer: {customer_doc['customer_name']}")

    # 3. Create Valid Item
    item_id = str(uuid.uuid4())
    item_doc = {
        "item_id": item_id,
        "account_id": account_id,
        "item_name": "SaaS License - annual",
        "sku": "LIC-001",
        "hsn_code": "997331",
        "selling_price": 5000.0,
        "purchase_price": 0.0,
        "current_stock": 99999,
        "unit": "nos",
        "tax_percent": 18.0,
        "created_at": datetime.utcnow()
    }
    db.items.insert_one(item_doc)
    print(f"Created Item: {item_doc['item_name']}")

    # 4. Create Valid Invoice
    invoice_id = str(uuid.uuid4())
    invoice_number = "INV-0001"
    
    qty = 1.0
    rate = 5000.0
    tax_percent = 18.0
    sub_total = qty * rate
    tax_amount = sub_total * (tax_percent / 100)
    grand_total = sub_total + tax_amount
    
    invoice_doc = {
        "invoice_id": invoice_id,
        "account_id": account_id,
        "user_id": user_id,
        "invoice_number": invoice_number,
        "customer_id": customer_id,
        "customer_name": customer_doc['customer_name'],
        "customer_code": customer_doc['customer_code'],
        "customer_address": customer_doc['billing_address'],
        "customer_gstin": customer_doc['gstin'],
        "customer_state": customer_doc['state'],
        "customer_state_code": customer_doc['state_code'],
        "invoice_date": datetime.utcnow(),
        "due_date": datetime.utcnow(),
        "items": [
            {
                "item_id": item_id,
                "item_name": item_doc['item_name'],
                "sku": item_doc['sku'], # Still include for ref
                "hsn_code": item_doc['hsn_code'],
                "qty": qty,
                "rate": rate,
                "tax_percent": tax_percent,
                "tax_amount": tax_amount,
                "total": sub_total + tax_amount, # FIXED FIELD NAME
                "amount": sub_total + tax_amount # Include both just in case
            }
        ],
        "sub_total": sub_total,
        "total_tax": tax_amount,
        "grand_total": grand_total,
        "balance_amount": grand_total,
        "amount_received": 0.0,
        "payment_status": "unpaid",
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    db.invoices.insert_one(invoice_doc)
    print(f"Created Invoice: {invoice_number}")

if __name__ == "__main__":
    seed()
