from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from routes.auth.user import DummyUser
from datetime import datetime  
import os
import face_recognition
import numpy as np
import re
from PIL import Image
from pymongo import MongoClient
import os
from cv2 import cvtColor, COLOR_BGR2RGB
import cv2
from PIL import Image
import io

client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("DB_NAME")]

router = Blueprint("auth", __name__, url_prefix="/api")

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def is_valid_password(password):
    return len(password) >= 6  

@router.route("/register", methods=["POST"])
def register():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')
    image_file = request.files.get('image')
    colid_raw = request.form.get('colid')
    programcode = request.form.get('programcode')
    admissionyear = request.form.get('admissionyear')
   

    if not all([name, email, password, role, image_file, colid_raw,programcode]):
        return jsonify({'error': 'All fields including college ID are required'}), 400

    if role not in ["Student", "faculty"]:
        return jsonify({'error': 'Invalid role specified'}), 400
    
    if not (admissionyear.isdigit() and len(admissionyear) == 4):
        return jsonify({'error': 'Admission year must be a valid 4-digit year'}), 400
    
    if not colid_raw.isdigit():
        return jsonify({'error': 'College ID must be a numeric value'}), 400

    colid = int(colid_raw)

    if db.users.find_one({'email': email}):
        return jsonify({'error': 'User already exists'}), 400

    try:
     
        file_bytes = np.frombuffer(image_file.read(), np.uint8)
        image_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if image_bgr is None:
            return jsonify({'error': 'Invalid image format'}), 400

        img_array = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(img_array)

        if len(encodings) == 0:
            return jsonify({'error': 'No face detected in the image'}), 400

        face_encoding = encodings[0].tolist()
    except Exception as e:
        return jsonify({'error': 'Image processing failed', 'details': str(e)}), 500

    hashed_password = generate_password_hash(password)

    db.users.insert_one({
        'email': email,
        'name': name,
        'password': hashed_password,
        'role': role,
        'colid': colid,
        'programcode': programcode,
        'status': 1,
        'facedata': face_encoding,
        'regno': 'Unknown',
        'admissionyear': admissionyear,
        'semester': 'Unknown',
        'section': 'Unknown',
        'gender': 'Unknown',
        'department': 'Unknown',
        'photo': 'Unknown',
        'expotoken': None,
        'category': 'Unknown',
        'address': 'Unknown',
        'quota': 'Unknown',
        'user': 'Unknown',
        'addedby': 'Unknown',
        'status1': 'Unknown',
        'comments': 'Unknown',
        'lastlogin': None
    })

    return jsonify({'message': 'User registered successfully'}), 201

@router.route("/login", methods=["POST"])
def login():
        data = request.get_json()
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'}), 400

        user = db.users.find_one({"email": email})
        if user and check_password_hash(user["password"], password):
            login_user(DummyUser(user["_id"]))

            return jsonify({
                'success': True,
                'message': 'Login successful',
                'name': user.get('name'),
                'role': user.get('role', 'student'),
                'user_id': str(user["_id"]),
                'colid': user.get('colid'),
                'token': "dummy-session-token"  
            }), 200
        
        return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

@router.route("/logout", methods=["POST"])
def logout():
    logout_user()
    return jsonify({"success": True})

@router.route("/check-auth")
def check_auth():
    if current_user.is_authenticated:
        return jsonify({"status": "ok"})
    return jsonify({"status": "unauthorized"}), 401
