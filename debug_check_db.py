
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# Adjust connection string if needed, checking standard local mongo
client = MongoClient('mongodb://localhost:27017/')
db = client['billing_db']
collection = db['invoices']

count = collection.count_documents({})
print(f"Total invoices in database: {count}")

if count > 0:
    print("Sample invoice:")
    print(collection.find_one())
else:
    print("Invoices collection is empty.")
