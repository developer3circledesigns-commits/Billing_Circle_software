from pymongo import MongoClient
from app.core.config import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.DATABASE_NAME]
user = db.users.find_one({"email": "admin@billing.com"})

if user:

    print(f"User found: {user['email']}")
    print(f"Account ID: {user.get('account_id', 'NOT SET')}")

else:
    print("User 'admin@billing.com' not found in database.")
