from pymongo import MongoClient
import os
class Database:
    _instance = None 
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance.MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
            cls._instance.MONGO_DB = os.getenv("MONGO_DB", "telegram_api")
            cls._instance.client = MongoClient(cls._instance.MONGO_URI)
            cls._instance.db = cls._instance.client[cls._instance.MONGO_DB]
            print(f"MongoDB connected to {cls._instance.MONGO_DB} at {cls._instance.MONGO_URI}")
        return cls._instance
    def get_db(self):
        return self.db
    def get_client(self):
        return self.client