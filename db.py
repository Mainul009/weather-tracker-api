from pymongo import MongoClient, GEOSPHERE, TEXT
from config import MONGO_URI, DB_NAME

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

locations = db.locations
users = db.users
alerts = db.alerts
blacklist = db.blacklist

def create_indexes():
    locations.create_index([("geo", GEOSPHERE)])                # needed for "nearby" searches
    locations.create_index([("name", TEXT), ("region", TEXT)])  # needed for text search
    locations.create_index("country")
    users.create_index("username", unique=True)                 # no duplicate usernames
    users.create_index("email", unique=True)
    blacklist.create_index("expires", expireAfterSeconds=0)     # auto-deletes old tokens