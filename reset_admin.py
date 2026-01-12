from pymongo import MongoClient
from app.core.config import settings
from app.core.security import get_password_hash

client = MongoClient(settings.MONGO_URI)
db = client[settings.DATABASE_NAME]
db.users.update_one(
    {"email": "admin@billing.com"},
    {"$set": {"hashed_password": get_password_hash("admin123")}}
)
print("Password reset for admin@billing.com to admin123")
