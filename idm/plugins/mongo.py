from django.conf import settings
from pymongo import MongoClient

mongo_client = MongoClient(
    settings.PROVIDER['UserInfoProvider']['MONGO_HOST'],
)
mongo_db = mongo_client[settings.PROVIDER['UserInfoProvider']['MONGO_DATABASE']]

user = settings.PROVIDER['UserInfoProvider']['MONGO_USER']
password = settings.PROVIDER['UserInfoProvider']['MONGO_PASS']

if user:
    mongo_db.authenticate(user, password, source='admin')
