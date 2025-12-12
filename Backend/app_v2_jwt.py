from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
import time
import random
import os
import logging
import sqlite3
import json
import jwt
import functools

app = Flask(__name__)

# ==========================================
# CONFIGURATION
# ==========================================
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB file limit
app.config['JWT_SECRET'] = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
app.config['JWT_ALGORITHM'] = 'HS256'
app.config['JWT_EXPIRATION'] = 24  # hours

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
                password_hash TEXT NOT NULL,
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
# JWT AUTHENTICATION
# ==========================================
def generate_token(email, name):
    """Generate JWT token"""
    try:
        payload = {
            'email': email,
            'name': name,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=app.config['JWT_EXPIRATION'])
        }
        token = jwt.encode(payload, app.config['JWT_SECRET'], algorithm=app.config['JWT_ALGORITHM'])
        return token
    except Exception as e:
        logger.error(f"Token generation error: {str(e)}")
        return None

def verify_token(token):
    """Verify JWT token and return payload"""
    try:
        payload = jwt.decode(token, app.config['JWT_SECRET'], algorithms=[app.config['JWT_ALGORITHM']])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def require_auth(f):
    """Decorator to require JWT authentication"""
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in headers
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"error": "Invalid authorization header"}), 401
        
        if not token:
            return jsonify({"error": "Missing authentication token"}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({"error": "Invalid or expired token"}), 401
        
        # Pass user info to the route
        request.user = payload
        return f(*args, **kwargs)
    
    return decorated

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
# API ROUTES - PUBLIC
# ==========================================
@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "🌿 Crop Portal AI Backend v2.0 (JWT Auth Enabled)",
        "version": "2.0",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "database": os.path.exists(DATABASE),
        "timestamp": datetime.now().isoformat()
    }), 200

# ==========================================
# API ROUTES - AUTHENTICATION
# ==========================================
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('name') or not data.get('password'):
            return jsonify({"error": "Missing required fields: email, name, password"}), 400
        
        email = data['email']
        name = data['name']
        password = data['password']
        
        # Check if user already exists
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        
        if cursor.fetchone():
            conn.close()
            logger.warning(f"Registration attempt with existing email: {email}")
            return jsonify({"error": "User already exists"}), 409
        
        # Insert new user (in production, hash the password!)
        cursor.execute('''
            INSERT INTO users (email, name, password_hash)
            VALUES (?, ?, ?)
        ''', (email, name, password))  # TODO: Use werkzeug.security.generate_password_hash
        
        conn.commit()
        conn.close()
        
        logger.info(f"New user registered: {email}")
        
        # Generate token
        token = generate_token(email, name)
        
        return jsonify({
            "message": "User registered successfully",
            "token": token,
            "user": {"email": email, "name": name}
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({"error": "Registration failed"}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({"error": "Missing email or password"}), 400
        
        email = data['email']
        password = data['password']
        
        # Verify credentials
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
        user = cursor.fetchone()
        conn.close()
        
        if not user or user['password_hash'] != password:  # TODO: Use werkzeug.security.check_password_hash
            logger.warning(f"Failed login attempt for {email}")
            return jsonify({"error": "Invalid credentials"}), 401
        
        logger.info(f"User logged in: {email}")
        
        # Generate token
        token = generate_token(email, user['name'])
        
        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {"email": email, "name": user['name']}
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({"error": "Login failed"}), 500

@app.route('/api/auth/verify', methods=['GET'])
@require_auth
def verify_auth():
    """Verify if token is valid"""
    return jsonify({
        "valid": True,
        "user": request.user
    }), 200

# ==========================================
# API ROUTES - DISEASE DETECTION
# ==========================================
@app.route('/api/detect', methods=['POST'])
@require_auth
def detect_disease():
    """
    Detect crop disease from uploaded image
    - Requires authentication
    - Validates file type and size
    - Simulates AI processing
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
        
        user_email = request.user['email']
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(UPLOAD_FOLDER, f"{timestamp}_{filename}")
        
        logger.info(f"Processing image: {file.filename} for user: {user_email}")
        
        # 5. SAVE FILE
        file.save(filepath)
        logger.info(f"File saved to: {filepath}")
        
        # 6. SIMULATE AI PROCESSING TIME
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

@app.route('/api/history', methods=['GET'])
@require_auth
def get_analysis_history():
    """Get analysis history for authenticated user"""
    try:
        user_email = request.user['email']
        limit = request.args.get('limit', 50, type=int)
        
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, disease, confidence, description, created_at 
            FROM analysis_results 
            WHERE user_email = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_email, limit))
        
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

# ==========================================
# ERROR HANDLERS
# ==========================================
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
    logger.info("[*] Starting Crop Portal Backend v2.0...")
    logger.info("[+] File Upload Validation: Enabled")
    logger.info("[+] JWT Authentication: Enabled")
    logger.info("[+] CORS: Enabled")
    logger.info("[+] Max File Size: 5MB")
    logger.info("[+] Allowed formats: PNG, JPG, JPEG, GIF, BMP")
    logger.info("[+] Database: SQLite initialized")
    logger.info("[!] WARNING: Using demo password hash. Use werkzeug.security in production!")
    app.run(debug=True, port=5000)
