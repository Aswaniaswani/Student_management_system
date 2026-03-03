from pymongo import MongoClient
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password

def get_db():
    client = MongoClient(
        host=settings.MONGO_DB['HOST'],
        port=settings.MONGO_DB['PORT']
    )
    db = client[settings.MONGO_DB['NAME']]
    return db, client

def hash_password(password):
    return make_password(password)

def verify_password(password, hashed):
    return check_password(password, hashed)