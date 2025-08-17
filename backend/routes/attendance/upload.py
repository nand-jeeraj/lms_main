import base64
import traceback
from flask import Blueprint, request, jsonify
from datetime import datetime
from pymongo import MongoClient
from utils.face_utils import load_known_faces_from_db, recognize_faces_from_bytes
from dependencies import get_current_user
import os

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]

upload_router = Blueprint("upload", __name__, url_prefix="/api")

@upload_router.route("/attendance_upload", methods=["POST"])
def upload():
    try:
        current_user = get_current_user()
        print("Current user object:", current_user)

        if not current_user:
            return jsonify({"error": "Unauthorized"}), 401

        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
        
        colid = request.form.get("colid")
        program_code = request.form.get("program_code")
        year = request.form.get('year')

        print("colid:", colid)

        file = request.files['image']
        image_bytes = file.read()

       
        known_encs, known_names = load_known_faces_from_db(colid,program_code,year)

        
        present, unknown, total = recognize_faces_from_bytes(
            image_bytes, known_encs, known_names
        )
        for name in present:
          student = db.users.find_one({"name": name, "role": "Student"})
          db.uploaded_photos.insert_one({
            "colid": colid,
            "programcode": program_code,
            "timestamp": datetime.utcnow(),
            "image_base64": base64.b64encode(image_bytes).decode(),
            "present_Students": present,
            "unknown_faces": unknown,
            "total_faces": total,
            "year":year
        })

        
        for name in present:
            if name == "Unknown":
                continue

           
            student = db.users.find_one({"name": name, "role": "Student"})
            if student:
                attendance_record = {
                    "colid": colid,  
                    "name": student["name"],
                    "timestamp": datetime.utcnow(),
                    "program": student.get("program", "UNKNOWN"),       
                    "programcode": student.get("programcode", "UNKNOWN"),
                    "admissionyear": student.get("admissionyear", "UNKNOWN"),
                    "course": student.get("course", "UNKNOWN"),
                    "coursecode": student.get("coursecode", "UNKNOWN"),
                    "faculty": current_user.get("name", "UNKNOWN"),     
                    "period": "",                                 
                    "attendance": 1,
                    "user": student.get("user", "UNKNOWN"),
                    "classid": student.get("classid", "UNKNOWN"),
                    "student": student.get("student", "UNKNOWN"),
                    "regno": student.get("regno", "UNKNOWN"),
                    "att": student.get("att", "UNKNOWN"),
                    "classdate": datetime.utcnow().strftime("%Y-%m-%d"),
                    "semester": student.get("semester", "UNKNOWN"),
                    "section": student.get("section", "UNKNOWN"),
                    "status1":student.get("status1", "UNKNOWN"),
                    "comments": student.get("comments", "UNKNOWN"),
                }

                
                db.attendance.insert_one(attendance_record)

        return jsonify({
            "message": "Attendance captured successfully",
            "present": present,
            "unknown": unknown,
            "total": total
        }), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": "Upload failed",
            "details": str(e)
        }), 500



router = upload_router
