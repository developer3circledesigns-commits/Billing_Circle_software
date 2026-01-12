
from pymongo import MongoClient
from app.core.config import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.DATABASE_NAME]

collections = ["users", "categories", "weavers", "customers", "items", "quotations", "invoices"]

with open("verification_results.txt", "w") as f:
    f.write(f"{'Collection':<20} | {'Count':<10}\n")
    f.write("-" * 35 + "\n")
    for col in collections:
        count = db[col].count_documents({})
        f.write(f"{col:<20} | {count:<10}\n")
    print("Verification complete. Check verification_results.txt")

