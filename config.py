import os
from dotenv import load_dotenv

load_dotenv()   # reads the .env file

MONGO_URI = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017")
DB_NAME = "weatherDB"
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
TOKEN_HOURS = 2   # how long a login lasts
