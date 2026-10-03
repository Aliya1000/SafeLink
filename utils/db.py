from pymongo import MongoClient
from config import Config

def get_db():
    try:
        client = MongoClient(Config.MONGO_URI, serverSelectionTimeoutMS=2000)
        # The next line forces a connection check
        client.server_info() 
        return client.get_database()
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        return None