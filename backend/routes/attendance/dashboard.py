from flask import Blueprint, jsonify, request
from extensions import mongo
from dependencies import get_current_user
from bson import ObjectId
from datetime import datetime
from pymongo import MongoClient
import os
import traceback
import pytz

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]

dashboard_router = Blueprint("dashboard", __name__, url_prefix="/api")

@dashboard_router.route("/attendance_dashboard", methods=["GET"])
def dashboard():
    try:
        current_user = get_current_user()

        colid = request.args.get("colid")
        program_code = request.args.get("program_code")
        year = request.args.get("year")
        name = request.args.get("name")  
        print('id', colid)
        print('program', program_code)
        print('year', year)
        print('name', name)

        pipeline = []
        match_filter = {}

        if colid:
            match_filter["colid"] = {"$regex": colid, "$options": "i"}

        if program_code:
            match_filter["programcode"] = {"$regex": program_code, "$options": "i"}

        if year:
            try:
                match_filter["admissionyear"] = year
            except ValueError:
                match_filter["admissionyear"] = {"$regex": year, "$options": "i"}

        if name:
            match_filter["name"] = {"$regex": name, "$options": "i"}

        if match_filter:
            pipeline.append({"$match": match_filter})

        print(pipeline)
        pipeline.extend([
            {
                "$group": {
                    "_id": "$name",
                    "count": {"$sum": 1}
                }
            },
            {
                "$sort": {"count": -1}
            }
        ])

        data = list(db.attendance.aggregate(pipeline))
        print('res',data)
        return jsonify(data)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"detail": str(e)}), 500


@dashboard_router.route("/attendance_history", methods=["GET"])
def history():
    try:
        current_user = get_current_user()
        
        colid = request.args.get("colid")
        program_code = request.args.get("program_code")
        year = request.args.get("year")
        name = request.args.get("name")  

        filter_query = {}
        if colid:
            filter_query["colid"] = colid
        
        if program_code:
            filter_query["programcode"] = {"$regex": f"^{program_code}$", "$options": "i"}
        
        
        if year:
                filter_query["admissionyear"] = year

        
        if name:
            filter_query["name"] = {"$regex": f"^{name}$", "$options": "i"}

        print(filter_query)
        recs = list(db.attendance.find(filter_query).sort("timestamp", -1))
        print("Received params:", request.args)


        # IST timezone object
        ist = pytz.timezone('Asia/Kolkata')

        for r in recs:
            r["_id"] = str(r["_id"])
            if isinstance(r.get("timestamp"), datetime):
                
                utc_time = r["timestamp"].replace(tzinfo=pytz.utc)
                ist_time = utc_time.astimezone(ist)
                r["timestamp"] = ist_time.isoformat()
            if "name" not in r and "Student_name" in r:
                r["name"] = r["Student_name"]

        return jsonify(recs)

    except Exception as e:
        traceback.print_exc()
        return jsonify({"detail": f"Internal server error: {str(e)}"}), 500
    

router = dashboard_router
