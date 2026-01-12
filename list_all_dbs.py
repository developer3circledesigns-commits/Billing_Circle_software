from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

def list_dbs():
    uri = os.getenv("MONGO_URI")
    client = MongoClient(uri)
    print("Databases on this cluster:")
    for db_name in client.list_database_names():
        db = client[db_name]
        try:
            collections = db.list_collection_names()
            if "invoices" in collections:
                count = db.invoices.count_documents({})
                print(f"DATABASE: {db_name} | INVOICES: {count}")
            elif db_name not in ['admin', 'local', 'config']:
                print(f"DATABASE: {db_name} | (No invoices collection)")
        except:
            pass

if __name__ == "__main__":
    list_dbs()
