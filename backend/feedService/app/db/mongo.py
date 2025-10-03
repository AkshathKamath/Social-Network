from pymongo import MongoClient
from app.config import settings

mongo_client: MongoClient = MongoClient(settings.mongo_url)

def get_mongo() -> MongoClient:
    return mongo_client