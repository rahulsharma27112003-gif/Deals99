#!/usr/bin/env python
"""
Start script for Deals99 Full Stack E-commerce Platform
This script will start both the backend and frontend servers
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import django
        import rest_framework
        print("✅ Django and DRF are installed")
        return True
    except ImportError:
        print("❌ Django and DRF are not installed")
        print("Please run: pip install -r backend/requirements.txt")
        return False

def start_backend():
    """Start the Django backend server"""
    print("\n🚀 Starting Django backend server...")
    
    # Change to backend directory
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return None
    
    os.chdir(backend_dir)
    
    # Check if database exists, if not run setup
    if not Path("db.sqlite3").exists():
        print("📦 Setting up database and sample data...")
        try:
            subprocess.run([sys.executable, "setup.py"], check=True)
            print("✅ Database setup completed")
        except subprocess.CalledProcessError as e:
            print(f"❌ Database setup failed: {e}")
            return None
    
    # Start Django server
    try:
        process = subprocess.Popen([
            sys.executable, "run_server.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(3)
        
        # Check if server is running
        if process.poll() is None:
            print("✅ Backend server started at http://localhost:8000")
            return process
        else:
            print("❌ Failed to start backend server")
            return None
            
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return None

def start_frontend():
    """Start the frontend server"""
    print("\n🌐 Starting frontend server...")
    
    # Change to frontend directory
    frontend_dir = Path("../Deals99_FullFrontend[1]/Deals99_FullFrontend[1]/Deals99_FullFrontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return None
    
    os.chdir(frontend_dir)
    
    try:
        # Start HTTP server
        process = subprocess.Popen([
            sys.executable, "-m", "http.server", "3000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait a moment for server to start
        time.sleep(2)
        
        if process.poll() is None:
            print("✅ Frontend server started at http://localhost:3000")
            return process
        else:
            print("❌ Failed to start frontend server")
            return None
            
    except Exception as e:
        print(f"❌ Error starting frontend: {e}")
        return None

def open_browser():
    """Open browser to the application"""
    print("\n🌐 Opening browser...")
    time.sleep(2)
    webbrowser.open("http://localhost:3000")

def main():
    """Main function to start the project"""
    print("🎉 Welcome to Deals99 Full Stack E-commerce Platform!")
    print("=" * 60)
    
    # Check requirements
    if not check_python_version():
        return
    
    if not check_dependencies():
        return
    
    # Start backend
    backend_process = start_backend()
    if not backend_process:
        return
    
    # Start frontend
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        return
    
    # Open browser
    open_browser()
    
    print("\n" + "=" * 60)
    print("🎉 Deals99 is now running!")
    print("\n📱 Frontend: http://localhost:3000")
    print("🔧 Backend API: http://localhost:8000/api/")
    print("👨‍💼 Admin Panel: http://localhost:3000/admin.html")
    print("\n🔑 Admin Credentials:")
    print("   Username: admin")
    print("   Password: admin123")
    print("\nPress Ctrl+C to stop the servers")
    print("=" * 60)
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping servers...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Servers stopped. Goodbye!")

if __name__ == "__main__":
    main()
