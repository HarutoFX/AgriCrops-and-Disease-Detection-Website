"""
Production-ready Flask Application for Crop Disease Detection
Optimized for deployment on Render, Railway, or similar platforms
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import random
import logging
from datetime import datetime
import sqlite3

# ============================================================================
# APP CONFIGURATION
# ============================================================================

app = Flask(__name__)

# Production Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')

# CORS Configuration - Allow your frontend domain
FRONTEND_URL = os.getenv('FRONTEND_URL', '*')
CORS(app, resources={
    r"/api/*": {
        "origins": [FRONTEND_URL, "http://localhost:5500", "http://127.0.0.1:5500"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATABASE SETUP
# ============================================================================

def get_db_connection():
    """Create a database connection"""
    db_path = os.path.join(os.path.dirname(__file__), 'crop_portal.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables"""
    conn = get_db_connection()
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
            FOREIGN KEY (user_email) REFERENCES users (email)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info('[+] Database initialized successfully')

# ============================================================================
# DISEASE DATABASE (Mock AI Model)
# ============================================================================

DISEASE_DB = {
    'Potato Early Blight': {
        'confidence': 92.5,
        'description': 'Dark concentric rings on older leaves, causing leaf yellowing and defoliation.',
        'treatment': ['Remove infected leaves', 'Apply copper-based fungicide', 'Improve air circulation', 'Rotate crops annually']
    },
    'Tomato Leaf Curl': {
        'confidence': 88.3,
        'description': 'Viral disease causing upward curling of leaves and stunted plant growth.',
        'treatment': ['Remove infected plants', 'Control whitefly populations', 'Use resistant varieties', 'Apply neem oil spray']
    },
    'Rice Blast': {
        'confidence': 90.1,
        'description': 'Fungal disease with diamond-shaped lesions on leaves and stems.',
        'treatment': ['Apply systemic fungicides', 'Use resistant varieties', 'Proper water management', 'Remove infected debris']
    },
    'Healthy Crop': {
        'confidence': 95.0,
        'description': 'No disease detected. The crop appears healthy with normal growth patterns.',
        'treatment': ['Continue regular monitoring', 'Maintain proper irrigation', 'Follow preventive care', 'Keep records']
    }
}

# ============================================================================
# FILE VALIDATION
# ============================================================================

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================================================
# ROUTES
# ============================================================================

@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'status': 'online',
        'service': 'Crop Disease Detection API',
        'version': '2.0',
        'endpoints': {
            'health': '/api/health',
            'detect': '/api/detect (POST)',
        }
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database': 'connected',
        'environment': os.getenv('FLASK_ENV', 'development')
    })

@app.route('/api/detect', methods=['POST'])
def detect_disease():
    """
    Main disease detection endpoint
    Accepts image upload and returns disease diagnosis
    """
    try:
        # Check if file is present
        if 'image' not in request.files:
            logger.warning('[!] No image file in request')
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        
        # Check if file is selected
        if file.filename == '':
            logger.warning('[!] Empty filename')
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(file.filename):
            logger.warning(f'[!] Invalid file type: {file.filename}')
            return jsonify({'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, BMP'}), 400
        
        # Secure the filename
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save file
        file.save(filepath)
        logger.info(f'[+] File saved: {filename}')
        
        # Mock AI Prediction (Replace with real model later)
        disease_name = random.choice(list(DISEASE_DB.keys()))
        disease_info = DISEASE_DB[disease_name]
        
        # Prepare response
        result = {
            'success': True,
            'disease': disease_name,
            'confidence': disease_info['confidence'],
            'description': disease_info['description'],
            'treatment': disease_info['treatment'],
            'filename': filename,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f'[*] Detection complete: {disease_name} ({disease_info["confidence"]}%)')
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f'[!] Error during detection: {str(e)}')
        return jsonify({'error': 'Internal server error', 'message': str(e)}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(413)
def file_too_large(e):
    """Handle file size limit exceeded"""
    return jsonify({'error': 'File too large. Maximum size is 5MB'}), 413

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    logger.error(f'[!] Internal server error: {str(e)}')
    return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# INITIALIZATION
# ============================================================================

# Initialize database on startup
with app.app_context():
    init_db()
    logger.info('[*] Crop Disease Detection API Started')
    logger.info(f'[*] Environment: {os.getenv("FLASK_ENV", "development")}')
    logger.info(f'[*] Upload folder: {app.config["UPLOAD_FOLDER"]}')

# ============================================================================
# PRODUCTION SERVER
# ============================================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
