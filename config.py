import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/safelink_db')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'