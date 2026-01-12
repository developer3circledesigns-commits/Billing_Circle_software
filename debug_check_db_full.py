
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

client = MongoClient('mongodb://localhost:27017/')
db = client['billing_db']

print(f"Users: {db['users'].count_documents({})}")
if db['users'].count_documents({}) > 0:
    print("Sample User:", db['users'].find_one({}, {'password_hash': 0}))

print(f"Customers: {db['customers'].count_documents({})}")
print(f"Items: {db['items'].count_documents({})}")
print(f"Invoices: {db['invoices'].count_documents({})}")
