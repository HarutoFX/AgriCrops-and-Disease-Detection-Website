from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime
import time
import random
import os
import logging
import sqlite3
import json

app = Flask(__name__)

# ==========================================
# CONFIGURATION
# ==========================================
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB file limit
UPLOAD_FOLDER = 'uploads'
DATABASE = 'crop_portal.db'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Create upload folder if doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crop_portal.log'),
        logging.StreamHandler()
    ]
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
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Analysis results table
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
        logger.info("[+] Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")

# ==========================================
# DISEASE DATABASE
# ==========================================
DISEASE_DB = [
    {
        "disease": "Potato Early Blight",
        "confidence": 0.94,
        "description": "Fungal infection characterized by concentric rings on dark spots.",
        "treatment": ["Apply copper-based fungicides", "Improve air circulation", "Remove infected leaves"],
        "severity": "High"
    },
    {
        "disease": "Corn Common Rust",
        "confidence": 0.88,
        "description": "Reddish-brown pustules appearing on both leaf surfaces.",
        "treatment": ["Plant resistant varieties", "Apply fungicides early", "Crop rotation"],
        "severity": "Medium"
    },
    {
        "disease": "Tomato Mosaic Virus",
        "confidence": 0.91,
        "description": "Mottling and yellowing of leaves with stunted growth.",
        "treatment": ["Remove infected plants", "Control aphids", "Disinfect tools"],
        "severity": "High"
    },
    {
        "disease": "Healthy",
        "confidence": 0.98,
        "description": "No signs of disease detected. Plant looks vigorous.",
        "treatment": ["Continue regular watering", "Monitor weekly", "Maintain soil nutrition"],
        "severity": "None"
    }
]

# ==========================================
# UTILITY FUNCTIONS
# ==========================================
def allowed_file(filename):
    """Check if file has allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_analysis_result(user_email, result, filename):
    """Save analysis result to database"""
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
        logger.info(f"Analysis result saved for {user_email}")
    except Exception as e:
        logger.error(f"Error saving analysis result: {str(e)}")

# ==========================================
# API ROUTES
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
    """
    Detect crop disease from uploaded image
    - Validates file type and size
    - Simulates AI processing
    - Returns disease diagnosis with treatment
    - Saves result to database
    """
    try:
        # 1. VALIDATION: Check if image was sent
        if 'imageFile' not in request.files:
            logger.warning("Disease detection attempted without file")
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['imageFile']
        
        # 2. VALIDATION: Check filename is not empty
        if file.filename == '':
            logger.warning("Empty filename submitted")
            return jsonify({"error": "No file selected"}), 400
        
        # 3. VALIDATION: Check file extension
        if not allowed_file(file.filename):
            logger.warning(f"Invalid file type: {file.filename}")
            return jsonify({
                "error": f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            }), 400
        
        # 4. Get user email from request (optional)
        user_email = request.form.get('userEmail', 'anonymous')
        
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{filename}")
        
        logger.info(f"Processing image: {file.filename} for user: {user_email}")
        
        # 5. SAVE FILE
        file.save(filepath)
        logger.info(f"File saved to: {filepath}")
        
        # 6. SIMULATE AI PROCESSING TIME
        # (Replace this with actual AI model inference)
        time.sleep(2)
        
        # 7. GET DIAGNOSIS (Mock - replace with real AI model)
        result = random.choice(DISEASE_DB)
        
        # 8. SAVE TO DATABASE
        save_analysis_result(user_email, result, filename)
        
        # 9. RETURN RESPONSE
        response = {
            **result,
            "timestamp": datetime.now().isoformat(),
            "filename": filename
        }
        
        logger.info(f"Detection result: {result['disease']} ({result['confidence']*100}% confidence)")
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Error in detect_disease: {str(e)}", exc_info=True)
        return jsonify({"error": "Server error. Please try again."}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "database": os.path.exists(DATABASE),
        "timestamp": datetime.now().isoformat()
    }), 200

@app.route('/api/history', methods=['GET'])
def get_analysis_history():
    """Get analysis history for a user"""
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
        
        return jsonify({
            "user": user_email,
            "results": results,
            "count": len(results)
        }), 200
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        return jsonify({"error": "Failed to fetch history"}), 500

@app.errorhandler(413)
def too_large(e):
    """Handle file too large error"""
    logger.warning("File upload exceeded 5MB limit")
    return jsonify({"error": "File too large. Maximum size: 5MB"}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500

# ==========================================
# INITIALIZATION
# ==========================================
if __name__ == '__main__':
    init_db()
    logger.info("[*] Starting Crop Portal Backend...")
    logger.info("[+] File Upload Validation: Enabled")
    logger.info("[+] CORS: Enabled")
    logger.info("[+] Max File Size: 5MB")
    logger.info("[+] Allowed formats: PNG, JPG, JPEG, GIF, BMP")
    logger.info("[+] Database: SQLite initialized")
    app.run(debug=True, port=5000)