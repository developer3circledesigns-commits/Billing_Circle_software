
from pymongo import MongoClient
from app.core.config import settings

client = MongoClient(settings.MONGO_URI)
db = client[settings.DATABASE_NAME]

TARGET_ACCOUNT_ID = "acc_sample_01"
user_email = "admin@billing.com"

result = db.users.update_one(
    {"email": user_email},
    {"$set": {"account_id": TARGET_ACCOUNT_ID}}
)

if result.modified_count > 0:
    print(f"Successfully updated account_id for {user_email} to {TARGET_ACCOUNT_ID}")
else:
    print(f"User {user_email} not found or already has the correct account_id")

# Verify
user = db.users.find_one({"email": user_email})
print(f"Current Account ID: {user.get('account_id')}")
