from pymongo import MongoClient
import os

_client = None
_db = None
_reviews_collection = None

def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/skyvela")
        _client = MongoClient(uri)
    return _client

def get_mongo_db():
    global _db
    if _db is None:
        db_name = os.getenv("MONGO_DB_NAME", "skyvela")
        _db = get_mongo_client()[db_name]
    return _db

def get_reviews_collection():
    global _reviews_collection
    if _reviews_collection is None:
        coll_name = os.getenv("MONGO_REVIEWS_COLLECTION", "reviews")
        _reviews_collection = get_mongo_db()[coll_name]
    return _reviews_collection