
import random
import time
from datetime import datetime, timedelta
from typing import List
import uuid


from pymongo import MongoClient
from faker import Faker
from app.core.config import settings

# Setup Faker
fake = Faker('en_IN')  # Use Indian locale for relevance

# MongoDB Setup
MONGO_URI = settings.MONGO_URI
DATABASE_NAME = settings.DATABASE_NAME
ACCOUNT_ID = "acc_sample_01"

try:
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    print(f"Connected to MongoDB: {DATABASE_NAME}")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    exit(1)


# Helper Functions
def generate_id():
    return str(uuid.uuid4())

def random_date(start_year=2023, end_year=2025):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    return start + timedelta(days=random.randrange(delta.days))

def get_random_doc(collection_name):
    pipeline = [{"$sample": {"size": 1}}]
    result = list(db[collection_name].aggregate(pipeline))
    if result:
        return result[0]
    return None

def get_random_docs(collection_name, size=1):
    pipeline = [{"$sample": {"size": size}}]
    return list(db[collection_name].aggregate(pipeline))

# ----------------- Generators -----------------

def seed_users(n=10):
    print(f"Seeding {n} Users...")
    users = []
    for _ in range(n):
        users.append({
            "user_id": generate_id(),
            "account_id": ACCOUNT_ID,
            "email": fake.email(),
            "hashed_password": "hashed_password_placeholder",
            "full_name": fake.name(),
            "role": random.choice(["admin", "staff", "viewer"]),
            "status": "active",
            "created_at": datetime.utcnow()
        })
    if users:
        db.users.insert_many(users)
    print(f"Inserted {len(users)} users.")

def seed_categories(n=50):
    print(f"Seeding {n} Categories...")
    categories = []
    for _ in range(n):
        categories.append({
            "category_id": generate_id(),
            "account_id": ACCOUNT_ID,
            "category_name": fake.word().capitalize() + " " + fake.word().capitalize(),
            "description": fake.sentence(),
            "status": "active",
            "created_at": random_date()
        })
    if categories:
        db.categories.insert_many(categories)
    print(f"Inserted {len(categories)} categories.")

def seed_weavers(n=1000):
    print(f"Seeding {n} Weavers...")
    weavers = []
    for i in range(n):
        weavers.append({
            "weaver_id": generate_id(),
            "account_id": ACCOUNT_ID,
            "weaver_code": f"WVR-{1000+i}",
            "weaver_name": fake.company(),
            "display_name": fake.company_suffix(),
            "contact_number": fake.phone_number(),
            "email": fake.email(),
            "address": fake.address(),
            "gstin": fake.bothify(text='##?????####?#?#'),
            "pan_number": fake.bothify(text='?????####?'),
            "vendor_type": random.choice(["manufacturer", "distributor", "service_provider"]),
            "tax_registration_type": random.choice(["registered", "unregistered"]),
            "tds_applicable": random.choice([True, False]),
            "tds_percentage": random.choice([0.0, 2.0, 5.0, 10.0]),
            "bank_name": fake.bank(),
            "account_name": fake.name(),
            "account_number": fake.bban(),
            "ifsc_code": fake.swift(),
            "preferred_payment_mode": random.choice(["bank_transfer", "cheque", "cash"]),
            "opening_balance": round(random.uniform(0, 10000), 2),
            "status": "active",
            "created_at": random_date()
        })
        if len(weavers) >= 500: # Batch insert
            db.weavers.insert_many(weavers)
            weavers = []
    if weavers:
        db.weavers.insert_many(weavers)
    print(f"Seeding Weavers completed.")

def seed_customers(n=1000):
    print(f"Seeding {n} Customers...")
    customers = []
    for i in range(n):
        customers.append({
            "customer_id": generate_id(),
            "account_id": ACCOUNT_ID,
            "customer_code": f"CUST-{1000+i}",
            "customer_type": random.choice(["business", "individual"]),
            "customer_name": fake.name(),
            "company_name": fake.company(),
            "display_name": fake.name(),
            "contact_number": fake.phone_number(),
            "email": fake.email(),
            "billing_address": fake.address(),
            "shipping_address": fake.address(),
            "gstin": fake.bothify(text='##?????####?#?#'),
            "currency": "INR",
            "status": "active",
            "created_at": random_date()
        })
        if len(customers) >= 500:
            db.customers.insert_many(customers)
            customers = []
    if customers:
        db.customers.insert_many(customers)
    print(f"Seeding Customers completed.")

def seed_items(n=1000):
    print(f"Seeding {n} Items...")
    items = []
    categories = list(db.categories.find({}, {"category_id": 1}))
    cat_ids = [c["category_id"] for c in categories] if categories else [generate_id()]

    for i in range(n):
        start_date = random_date()
        items.append({
            "item_id": generate_id(),
            "account_id": ACCOUNT_ID,
            "item_name": fake.word().capitalize() + " " + fake.color_name(),
            "item_type": random.choice(["goods", "service"]),
            "sku": fake.bothify(text='SKU-####-????'),
            "category_id": random.choice(cat_ids),
            "hsn_code": fake.bothify(text='####'),
            "unit": random.choice(["PCS", "KG", "MTR", "BOX"]),
            "tax_preference": "taxable",
            "tax_rate": random.choice([0.0, 5.0, 12.0, 18.0, 28.0]),
            "purchase_price": round(random.uniform(100, 5000), 2),
            "selling_price": round(random.uniform(150, 8000), 2),
            "reorder_level": random.randint(5, 50),
            "current_stock": random.randint(0, 500),
            "status": "active",
            "description": fake.text(max_nb_chars=50),
            "created_at": start_date
        })
        if len(items) >= 500:
            db.items.insert_many(items)
            items = []
    if items:
        db.items.insert_many(items)
    print(f"Seeding Items completed.")

def seed_quotations(n=1000):
    print(f"Seeding {n} Quotations...")
    quotations = []
    customers = list(db.customers.find({}, {"customer_id": 1, "customer_name": 1}))
    all_items = list(db.items.find({}, {"item_id": 1, "item_name": 1, "selling_price": 1}))
    
    if not customers or not all_items:
        print("Skipping quotations: No customers or items found.")
        return

    for i in range(n):
        cust = random.choice(customers)
        q_date = random_date()
        
        # Generate random items
        q_items = []
        sub_total = 0
        total_tax = 0
        
        num_items = random.randint(1, 5)
        selected_items = random.sample(all_items, k=min(num_items, len(all_items)))
        
        for item in selected_items:
            qty = random.randint(1, 10)
            rate = item.get("selling_price", 100)
            amount = qty * rate
            tax = amount * 0.18 # Assuming 18%
            q_items.append({
                "item_id": item["item_id"],
                "item_name": item["item_name"],
                "qty": qty,
                "unit": "PCS",
                "rate": rate,
                "amount": amount,
                "tax_percent": 18.0,
                "tax_amount": tax,
                "total": amount + tax
            })
            sub_total += amount
            total_tax += tax
            
        quotations.append({
            "quotation_id": generate_id(),
            "account_id": ACCOUNT_ID,
            "quotation_number": f"QT-{1000+i}",
            "customer_id": cust["customer_id"],
            "customer_name": cust["customer_name"],
            "quote_date": q_date,
            "valid_until": q_date + timedelta(days=30),
            "items": q_items,
            "sub_total": round(sub_total, 2),
            "total_tax": round(total_tax, 2),
            "grand_total": round(sub_total + total_tax, 2),
            "status": random.choice(["draft", "sent", "accepted", "declined"]),
            "created_at": q_date
        })
        
        if len(quotations) >= 500:
            db.quotations.insert_many(quotations)
            quotations = []
            
    if quotations:
        db.quotations.insert_many(quotations)
    print(f"Seeding Quotations completed.")

def seed_invoices(n=1000):
    print(f"Seeding {n} Invoices...")
    invoices = []
    customers = list(db.customers.find({}, {"customer_id": 1, "customer_name": 1}))
    all_items = list(db.items.find({}, {"item_id": 1, "item_name": 1, "selling_price": 1}))

    if not customers or not all_items:
        return

    for i in range(n):
        cust = random.choice(customers)
        inv_date = random_date()
        
        # Generate random items
        inv_items = []
        sub_total = 0
        total_tax = 0
        
        num_items = random.randint(1, 5)
        selected_items = random.sample(all_items, k=min(num_items, len(all_items)))
        
        for item in selected_items:
            qty = random.randint(1, 10)
            rate = item.get("selling_price", 100)
            tax_amount = (qty * rate) * 0.18
            total_line = (qty * rate) + tax_amount
            
            inv_items.append({
                "item_id": item["item_id"],
                "item_name": item["item_name"],
                "qty": qty,
                "unit": "PCS",
                "rate": rate,
                "tax_percent": 18.0,
                "tax_amount": tax_amount,
                "total": total_line
            })
            sub_total += (qty * rate)
            total_tax += tax_amount

        grand_total = sub_total + total_tax
        status = random.choice(["active", "paid", "cancelled"])
        payment_status = "paid" if status == "paid" else random.choice(["unpaid", "partial"])
        balance = 0 if payment_status == "paid" else (grand_total if payment_status == "unpaid" else grand_total / 2)

        invoices.append({
            "invoice_id": generate_id(),
            "account_id": ACCOUNT_ID,
            "invoice_number": f"INV-{1000+i}",
            "customer_id": cust["customer_id"],
            "customer_name": cust["customer_name"],
            "invoice_date": inv_date,
            "due_date": inv_date + timedelta(days=15),
            "items": inv_items,
            "sub_total": round(sub_total, 2),
            "total_tax": round(total_tax, 2),
            "grand_total": round(grand_total, 2),
            "payment_status": payment_status,
            "balance_amount": round(balance, 2),
            "status": status,
            "created_at": inv_date
        })

        if len(invoices) >= 500:
            db.invoices.insert_many(invoices)
            invoices = []

    if invoices:
        db.invoices.insert_many(invoices)
    print(f"Seeding Invoices completed.")

# Run Seeders
if __name__ == "__main__":
    print("Starting Data Seeding...")
    seed_users(10)
    seed_categories(50)
    seed_weavers(1000)
    seed_customers(1000)
    seed_items(1000)
    seed_quotations(1000)
    seed_invoices(1000)
    # Skipping Bills/POs for brevity but can be added similarly logic
    print("Data Seeding Completed Successfully!")
