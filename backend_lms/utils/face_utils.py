import json
import numpy as np
import face_recognition
from extensions import mongo
from io import BytesIO
from pymongo import MongoClient
import os

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]




def load_known_faces_from_db(colid, program_code, year):
    print(f"Searching for students with colid: {colid}, program_code: {program_code}, year: {year}")

    query = {
        "role": {"$regex": "^student$", "$options": "i"},
        "facedata": {"$exists": True},
        "colid": int(colid) if isinstance(colid, str) else colid,
        "programcode": {"$regex": f"^{program_code}$", "$options": "i"}
        
    }

    if year: 
        query["admissionyear"] = {"$regex": f"^{year}$", "$options": "i"}

    students = db.users.find(query, {"name": 1, "facedata": 1})

    known_data = [
        (np.array(s["facedata"]), s["name"])
        for s in students
        if "facedata" in s and isinstance(s["facedata"], list)
    ]

    known_encs, known_names = zip(*known_data) if known_data else ([], [])

    return list(known_encs), list(known_names)

def recognize_faces_from_bytes(image_bytes, known_encs, known_names):
    try:
       
        img = face_recognition.load_image_file(BytesIO(image_bytes))

        
        face_locations = face_recognition.face_locations(img)
        face_encodings = face_recognition.face_encodings(img, face_locations)

        recognized_names = set()
        unknown_count = 0

        for face_enc in face_encodings:
            if not known_encs:
                unknown_count += 1
                continue

            distances = face_recognition.face_distance(known_encs, face_enc)
            best_match_index = np.argmin(distances)

            if distances[best_match_index] < 0.45:  
                recognized_names.add(known_names[best_match_index])
            else:
                unknown_count += 1

        return list(recognized_names), unknown_count, len(face_encodings)

    except Exception as e:
        print("Recognition failed:", e)
        return [], 0, 0
