
import sys
import os
from datetime import datetime
import uuid
from pymongo import MongoClient
# Add parent dir to path so we can import app modules if needed, 
# but for simplicity I will use direct pymongo and passlib here to avoid import errors with fastapi deps
# actually, better to use the app code to ensure compatibility with hashing
sys.path.append(os.getcwd())

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

client = MongoClient('mongodb://localhost:27017/')
db = client['billing_db']

def seed():
    # Clear existing (optional, but good for clean state if it was partial)
    # db.users.drop()
    # db.accounts.drop()
    # db.customers.drop()
    # db.items.drop()
    # db.invoices.drop()
    # db.stock_transactions.drop()
    # db.payments.drop()
    
    # 1. Create Account
    account_id = str(uuid.uuid4())
    account_doc = {
        "account_id": account_id,
        "subscription_type": "enterprise", # Give them full access
        "status": "active",
        "created_at": datetime.utcnow()
    }
    db.accounts.insert_one(account_doc)
    print(f"Created Account: {account_id}")

    # 2. Create User
    user_id = str(uuid.uuid4())
    email = "admin@example.com"
    password = "password123"
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
    db.users.insert_one(user_doc)
    print(f"Created User: {email} / {password}")

    # 3. Create Customer
    customer_id = str(uuid.uuid4())
    customer_doc = {
        "customer_id": customer_id,
        "account_id": account_id,
        "customer_name": "John Doe Enterprises",
        "customer_code": "CUST-001",
        "email": "john@example.com",
        "phone": "1234567890",
        "billing_address": "123 Main St, City, Country",
        "state": "California",
        "state_code": "CA",
        "gstin": "22AAAAA0000A1Z5",
        "created_at": datetime.utcnow()
    }
    db.customers.insert_one(customer_doc)
    print(f"Created Customer: {customer_doc['customer_name']}")

    # 4. Create Item
    item_id = str(uuid.uuid4())
    item_doc = {
        "item_id": item_id,
        "account_id": account_id,
        "item_name": "Premium Widget",
        "sku": "WID-001",
        "hsn_code": "1234",
        "selling_price": 100.0,
        "purchase_price": 50.0,
        "current_stock": 1000,
        "unit": "pcs",
        "tax_percent": 18.0,
        "created_at": datetime.utcnow()
    }
    db.items.insert_one(item_doc)
    print(f"Created Item: {item_doc['item_name']}")

    # 5. Create Invoice
    invoice_id = str(uuid.uuid4())
    invoice_number = "INV-0001"
    
    qty = 5
    rate = 100.0
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
        "invoice_date": datetime.utcnow().isoformat(),
        "due_date": datetime.utcnow().isoformat(),
        "items": [
            {
                "item_id": item_id,
                "item_name": item_doc['item_name'],
                "sku": item_doc['sku'],
                "hsn_code": item_doc['hsn_code'],
                "qty": qty,
                "rate": rate,
                "tax_percent": tax_percent,
                "tax_amount": tax_amount,
                "amount": sub_total + tax_amount
            }
        ],
        "sub_total": sub_total,
        "total_tax": tax_amount,
        "grand_total": grand_total,
        "balance_amount": grand_total,
        "amount_received": 0,
        "payment_status": "unpaid",
        "status": "active",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    db.invoices.insert_one(invoice_doc)
    print(f"Created Invoice: {invoice_number}")

if __name__ == "__main__":
    seed()
