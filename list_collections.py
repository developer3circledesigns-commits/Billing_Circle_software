from pymongo import MongoClient
from app.core.config import settings

try:
    client = MongoClient(settings.MONGO_URI)
    db = client[settings.DATABASE_NAME]
    collections = db.list_collection_names()
    print("Collections found:", collections)
except Exception as e:
    print(f"Error accessing database: {e}")
