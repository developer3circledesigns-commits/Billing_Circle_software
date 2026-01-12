from pymongo import MongoClient
from app.core.config import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.DATABASE_NAME]
users = list(db.users.find())

for user in users:
    print(f"Email: {user.get('email')}, Role: {user.get('role')}, Account: {user.get('account_id')}")
