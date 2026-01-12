from pymongo import MongoClient
from app.core.config import settings
import certifi
import sys

class Database:
    client: MongoClient = None

    def connect(self):
        try:
            ca = certifi.where()
            # Try connecting with SSL certificate verification first
            self.client = MongoClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,
                tls=True,
                tlsCAFile=ca,
                retryWrites=True
            )
            # Verify connection
            self.client.admin.command('ismaster')
            print("Successfully connected to MongoDB Cluster")
        except Exception as e:
            print(f"Primary MongoDB connection failed: {e}")
            try:
                print("Attempting connection with SSL verification bypassed...")
                self.client = MongoClient(
                    settings.MONGO_URI,
                    serverSelectionTimeoutMS=5000,
                    tls=True,
                    tlsAllowInvalidCertificates=True,
                    retryWrites=True
                )
                self.client.admin.command('ismaster')
                print("Connected to MongoDB Cluster (SSL verification bypassed)")
            except Exception as e2:
                print(f"Critical: Failed to connect to MongoDB: {e2}")
                # We don't exit here to allow the app to potentially start, 
                # but DB operations will fail.
                self.client = None

    def get_db(self):
        if not self.client:
            raise Exception("Database client not initialized. Check your MongoDB connection.")
        return self.client[settings.DATABASE_NAME]

    def close(self):
        if self.client:
            self.client.close()

    @staticmethod
    def serialize_doc(doc):
        if doc is None:
            return None
        if "_id" in doc:
            doc["id"] = str(doc["_id"])
            # Remove _id to avoid confusion if we are strictly following a model that uses item_id/user_id etc.
            # But the models often expect these custom IDs anyway.
        return doc

    @staticmethod
    def serialize_list(docs):
        return [Database.serialize_doc(doc) for doc in docs]

db = Database()
