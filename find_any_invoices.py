from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

def find_any_invoices():
    uri = os.getenv("MONGO_URI")
    db_name = os.getenv("DATABASE_NAME")
    client = MongoClient(uri)
    db = client[db_name]
    
    count = db.invoices.count_documents({})
    print(f"Total Invoices in '{db_name}': {count}")
    
    if count > 0:
        print("Sample of found invoices:")
        for inv in db.invoices.find().limit(5):
            print(f"- ID: {inv.get('invoice_id')}, Num: {inv.get('invoice_number')}, Account: {inv.get('account_id')}, Status: {inv.get('status')}")
    else:
        # Check other collections to see if any data exists
        print("Checking other collections for any data...")
        for coll in db.list_collection_names():
            if coll not in ['admin', 'local', 'config']:
                c = db[coll].count_documents({})
                if c > 0:
                    print(f"Collection '{coll}' has {c} documents.")

if __name__ == "__main__":
    find_any_invoices()
