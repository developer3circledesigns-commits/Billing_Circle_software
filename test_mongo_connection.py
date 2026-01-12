from app.core.database import db
from app.core.config import settings
import os
from dotenv import load_dotenv

def test_connection():
    load_dotenv()
    print(f"Testing MongoDB connection for database: {settings.DATABASE_NAME}")
    masked_uri = settings.MONGO_URI.split('@')[-1] if '@' in settings.MONGO_URI else settings.MONGO_URI
    print(f"Using URI: {masked_uri}")
    
    try:
        db.connect()
        if db.client:
            # Test database access
            database = db.get_db()
            collections = database.list_collection_names()
            print(f"Successfully connected! Collections in '{settings.DATABASE_NAME}': {collections}")
        else:
            print("Failed to initialize database client.")
    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    test_connection()
