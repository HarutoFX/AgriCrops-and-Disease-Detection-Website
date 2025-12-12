import os
import time
import random
import json
import logging
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify
from flask_cors import CORS

# ==========================================
# APP & CONFIG
# ==========================================
app = Flask(__name__)
CORS(app)  # during testing: allow all origins. Lock down later.
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB file limit

# Use absolute paths so the host can write to them reliably
ROOT_DIR = os.getcwd()
UPLOAD_FOLDER = os.path.join(ROOT_DIR, 'uploads')
DATABASE = os.path.join(ROOT_DIR, 'crop_portal.db')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ==========================================
# LOGGING
# ==========================================
log_handlers = [logging.StreamHandler()]
try:
    log_handlers.append(logging.FileHandler(os.path.join(ROOT_DIR, 'crop_portal.log')))
except Exception:
    # If file handler fails due to permissions, continue with stream handler only
    pass

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=log_handlers
)
logger = logging.getLogger(__name__)

# ==========================================
# DATABASE INITIALIZATION
# ==========================================
def init_db():
    """Initialize SQLite database with required tables"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
                disease TEXT NOT NULL,
                confidence REAL NOT NULL,
                description TEXT,
                treatment TEXT,
                filename TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_email) REFERENCES users(email)
            )
        ''')
        conn.commit()
        conn.close()
        logger.info("[+] Database initialized successfully at %s", DATABASE)
    except Exception as e:
        logger.exception("Database initialization error: %s", e)

# Run init_db on import so Gunicorn workers inherit an initialized DB (safe)
init_db()

# ==========================================
# MOCK DISEASE DB (replace with model later)
# ==========================================
DISEASE_DB = [
    {"disease": "Potato Early Blight", "confidence": 0.94, "description": "Fungal infection characterized by concentric rings on dark spots.", "treatment": ["Apply copper-based fungicides", "Improve air circulation", "Remove infected leaves"], "severity": "High"},
    {"disease": "Corn Common Rust",    "confidence": 0.88, "description": "Reddish-brown pustules appearing on both leaf surfaces.", "treatment": ["Plant resistant varieties", "Apply fungicides early", "Crop rotation"], "severity": "Medium"},
    {"disease": "Tomato Mosaic Virus","confidence": 0.91, "description": "Mottling and yellowing of leaves with stunted growth.", "treatment": ["Remove infected plants", "Control aphids", "Disinfect tools"], "severity": "High"},
    {"disease": "Healthy",            "confidence": 0.98, "description": "No signs of disease detected. Plant looks vigorous.", "treatment": ["Continue regular watering", "Monitor weekly", "Maintain soil nutrition"], "severity": "None"}
]

# ==========================================
# UTILITIES
# ==========================================
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_analysis_result(user_email, result, filename):
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analysis_results 
            (user_email, disease, confidence, description, treatment, filename)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_email,
            result.get('disease'),
            result.get('confidence'),
            result.get('description'),
            json.dumps(result.get('treatment', [])),
            filename
        ))
        conn.commit()
        conn.close()
        logger.info("Analysis result saved for %s", user_email)
    except Exception as e:
        logger.exception("Error saving analysis result: %s", e)

# ==========================================
# ROUTES
# ==========================================
@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "🌿 Crop Portal AI Backend is Running!",
        "version": "1.1",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/detect', methods=['POST'])
def detect_disease():
    try:
        if 'imageFile' not in request.files:
            logger.warning("No file uploaded")
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['imageFile']
        if file.filename == '':
            logger.warning("Empty filename submitted")
            return jsonify({"error": "No file selected"}), 400

        if not allowed_file(file.filename):
            logger.warning("Invalid file type: %s", file.filename)
            return jsonify({"error": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 400

        user_email = request.form.get('userEmail', 'anonymous')
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{filename}")

        logger.info("Saving file for %s -> %s", user_email, filepath)
        file.save(filepath)

        # Simulate model inference (replace with real model inference)
        time.sleep(2)
        result = random.choice(DISEASE_DB)

        save_analysis_result(user_email, result, filename)

        response = {**result, "timestamp": datetime.now().isoformat(), "filename": filename}
        logger.info("Detection result: %s (%.2f)", result['disease'], result['confidence'])
        return jsonify(response), 200

    except Exception as e:
        logger.exception("Error in detect_disease: %s", e)
        return jsonify({"error": "Server error. Please try again."}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "database_exists": os.path.exists(DATABASE),
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/api/history', methods=['GET'])
def get_analysis_history():
    try:
        user_email = request.args.get('email', 'anonymous')
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, disease, confidence, description, created_at 
            FROM analysis_results 
            WHERE user_email = ? 
            ORDER BY created_at DESC 
            LIMIT 50
        ''', (user_email,))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify({"user": user_email, "results": results, "count": len(results)}), 200
    except Exception as e:
        logger.exception("Error fetching history: %s", e)
        return jsonify({"error": "Failed to fetch history"}), 500

@app.errorhandler(413)
def too_large(e):
    logger.warning("File upload exceeded limit")
    return jsonify({"error": "File too large. Maximum size: 5MB"}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    logger.exception("Internal server error: %s", e)
    return jsonify({"error": "Internal server error"}), 500

# Note: Do NOT run app.run() when using Gunicorn in production.
# For local testing you can still run "python app.py" which will use the block below.
if __name__ == '__main__':
    logger.info("Starting Crop Portal Backend (local dev)...")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
