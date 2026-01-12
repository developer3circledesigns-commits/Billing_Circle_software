from pymongo import MongoClient
from app.core.config import settings
client = MongoClient(settings.MONGO_URI)
db = client[settings.DATABASE_NAME]
for u in db.users.find():
    print(u.get('email'))
