import os
from pymongo import MongoClient
from dotenv import load_dotenv


load_dotenv()


MONGO_URL = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME")


client = MongoClient(MONGO_URL)
db = client[DB_NAME]


quiz_collection = db["quizzes"]
scheduled_quiz_collection = db["scheduled_quizzes"]
assignment_collection = db["assignments"]
scheduled_assignment_collection = db["scheduled_assignments"]
submission_collection = db["submissions"]
assignment_submission_collection = db["assignment_submissions"]


try:
  
    db.list_collection_names()
    print("MongoDB connection successful.")
except Exception as e:
    print("MongoDB connection failed:", e)
