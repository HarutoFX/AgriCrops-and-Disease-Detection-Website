#!/usr/bin/env python3
"""
🌿 Crop Portal - Quick Start Script
Run this to setup and start the application
"""

import os
import sys
import subprocess
import platform

def run_command(cmd, description):
    """Run a command and report status"""
    print(f"\n{'='*60}")
    print(f"📌 {description}")
    print(f"{'='*60}")
    try:
        subprocess.run(cmd, shell=True)
        print(f"✅ {description} - SUCCESS")
        return True
    except Exception as e:
        print(f"❌ {description} - FAILED: {e}")
        return False

def main():
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║                                                        ║
    ║          🌿 CROP PORTAL - QUICK START GUIDE           ║
    ║                                                        ║
    ║    Instant Crop Disease Diagnosis with AI            ║
    ║                                                        ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    # Detect OS
    os_name = platform.system()
    print(f"📱 Operating System: {os_name}")
    
    # Step 1: Install dependencies
    print("\n" + "="*60)
    print("STEP 1: Installing Python Dependencies")
    print("="*60)
    
    backend_dir = "Backend"
    if os.path.exists(backend_dir):
        pip_cmd = "pip install -r Backend/requirements.txt"
        print(f"📦 Running: {pip_cmd}")
        os.system(pip_cmd)
    else:
        print("❌ Backend directory not found!")
        return
    
    # Step 2: Show instructions
    print("\n" + "="*60)
    print("STEP 2: Starting Backend Server")
    print("="*60)
    print("""
    Choose one of the following:
    
    Option A: Basic Version (Recommended for testing)
    ────────────────────────────────────────────────
    cd Backend
    python app.py
    
    Option B: Advanced Version (With JWT Authentication)
    ─────────────────────────────────────────────────────
    cd Backend
    python app_v2_jwt.py
    
    The server will start on: http://localhost:5000
    """)
    
    # Step 3: Show frontend instructions
    print("\n" + "="*60)
    print("STEP 3: Starting Frontend Server")
    print("="*60)
    print("""
    In a NEW terminal window:
    
    cd Frontend
    
    Option A: Using Python (Recommended)
    ────────────────────────────────────
    python -m http.server 5500
    
    Option B: Using Node.js (if installed)
    ──────────────────────────────────────
    npx http-server -p 5500
    
    Option C: Using VS Code Live Server Extension
    ──────────────────────────────────────────────
    Right-click index.html → Open with Live Server
    
    The frontend will be at: http://localhost:5500
    """)
    
    # Step 4: Testing instructions
    print("\n" + "="*60)
    print("STEP 4: Testing the Application")
    print("="*60)
    print("""
    1. Open http://localhost:5500 in your browser
    2. Click "Start Detection" button
    3. Upload a crop leaf image (PNG, JPG, GIF, BMP)
    4. Click "Analyze Image"
    5. See the disease diagnosis!
    
    🎯 Test Images:
    • Healthy leaf
    • Diseased leaf (potato blight, rust, virus, etc.)
    • Any crop image (>1px, <5MB)
    """)
    
    # Step 5: API Endpoints
    print("\n" + "="*60)
    print("STEP 5: API Endpoints (For Advanced Testing)")
    print("="*60)
    print("""
    📍 Public Endpoints:
    ──────────────────
    GET  http://localhost:5000/
    GET  http://localhost:5000/api/health
    
    📍 Protected Endpoints (App version only):
    ─────────────────────────────────────────
    POST http://localhost:5000/api/detect
    GET  http://localhost:5000/api/history
    
    📍 Authentication (JWT version only):
    ────────────────────────────────────
    POST http://localhost:5000/api/auth/register
    POST http://localhost:5000/api/auth/login
    GET  http://localhost:5000/api/auth/verify
    """)
    
    # Step 6: Debugging
    print("\n" + "="*60)
    print("STEP 6: Debugging & Troubleshooting")
    print("="*60)
    print("""
    📋 View Logs:
    ────────────
    tail -f Backend/crop_portal.log
    
    📊 Check Database:
    ─────────────────
    sqlite3 Backend/crop_portal.db
    
    🔍 View Uploaded Files:
    ──────────────────────
    ls Backend/uploads/
    
    💻 Test API with curl:
    ─────────────────────
    curl http://localhost:5000/api/health
    
    ⚡ Common Issues:
    ───────────────
    - Port 5000/5500 already in use? → Change port in code
    - CORS error? → Make sure both servers are running
    - File upload fails? → Check file size (<5MB) and format
    """)
    
    # Step 7: Documentation
    print("\n" + "="*60)
    print("STEP 7: Documentation & Resources")
    print("="*60)
    print("""
    📖 Read These Files:
    ──────────────────
    ✓ IMPROVEMENTS.md   → Detailed feature documentation
    ✓ SETUP_GUIDE.md    → Complete setup instructions
    ✓ Backend/app.py    → Backend code with comments
    ✓ Frontend/script.js → Frontend code with comments
    
    🌐 Stack:
    ────────
    Frontend: HTML5, Bootstrap, JavaScript, CSS3
    Backend:  Flask, Python, SQLite, JWT
    Database: SQLite (crop_portal.db)
    
    🔐 Security:
    ──────────
    ✓ File validation (type & size)
    ✓ JWT authentication (v2)
    ✓ CORS protection
    ✓ SQL injection prevention
    ✓ Secure logging
    """)
    
    # Summary
    print("\n" + "="*60)
    print("✅ SETUP COMPLETE!")
    print("="*60)
    print("""
    Next Steps:
    1. Run: cd Backend && python app.py
    2. In another terminal: cd Frontend && python -m http.server 5500
    3. Open: http://localhost:5500
    4. Upload an image and analyze!
    
    Enjoy your Crop Portal! 🌿
    """)

if __name__ == "__main__":
    main()
