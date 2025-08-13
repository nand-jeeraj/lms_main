from flask import Blueprint, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

router = Blueprint("assignment_fetch", __name__)

# MongoDB Connection
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]
assignments_collection = db["assignments"]
scheduled_assignments_collection = db["scheduled_assignments"]

@router.route("/assignments", methods=["POST"])
def create_assignment():
    try:
        assignment = request.get_json()

        if "colid" in assignment:
            try:
                assignment["colid"] = int(assignment["colid"])
            except ValueError:
                return jsonify({"detail": "colid must be an integer"}), 400
            
        # Ensure each question has a type and ID
        for question in assignment["questions"]:
            if not question.get("id"):
                question["id"] = str(ObjectId())
            if not question.get("type"):
                question["type"] = "text_response"
        result = assignments_collection.insert_one(assignment)
        return jsonify({"message": "Assignment created successfully", "id": str(result.inserted_id)})
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

@router.route("/scheduled-assignments", methods=["POST"])
def create_scheduled_assignment():
    try:
        assignment = request.get_json()

        if "colid" in assignment:
            try:
                assignment["colid"] = int(assignment["colid"])
            except ValueError:
                return jsonify({"detail": "colid must be an integer"}), 400

        # Add IDs to each question if not provided
        for question in assignment["questions"]:
            if not question.get("id"):
                question["id"] = str(ObjectId())
        scheduled_assignments_collection.insert_one(assignment)
        return jsonify({"message": "Scheduled assignment created successfully"})
    except Exception as e:
        return jsonify({"detail": str(e)}), 400

@router.route("/assignments", methods=["GET"])
def get_assignments():
    try:
        colid = request.args.get("colid")
        query = {} 
        if colid:
            try:
                query["colid"] = int(colid)
            except ValueError:
                query["colid"] = colid

        assignments = list(assignments_collection.find(query))
        for assignment in assignments:
            assignment["_id"] = str(assignment["_id"])
        return jsonify(assignments)
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

@router.route("/scheduled-assignments", methods=["GET"])
def get_scheduled_assignments():
    try:
        colid = request.args.get("colid")
        query = {}
        if colid:
            try:
                query["colid"] = int(colid)
            except ValueError:
                query["colid"] = colid
        assignments = list(scheduled_assignments_collection.find(query))
        for assignment in assignments:
            assignment["_id"] = str(assignment["_id"])
        return jsonify(assignments)
    except Exception as e:
        return jsonify({"detail": str(e)}), 500
