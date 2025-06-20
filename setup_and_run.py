#!/usr/bin/env python3
"""
Setup and run script for the AI Rota System
This script handles installation and running of the system
"""

import subprocess
import sys
import os
from pathlib import Path
import platform

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    
    # Try to install uv first
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "uv"])
        print("✓ uv installed successfully")
        
        # Try to use uv for faster installation
        try:
            subprocess.check_call(["uv", "pip", "install", "-r", "requirements.txt"])
            print("✓ Dependencies installed via uv")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("! uv installation failed, falling back to pip")
    except subprocess.CalledProcessError:
        print("! Could not install uv, using pip")
    
    # Fallback to regular pip
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed via pip")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path(".env")
    if not env_file.exists():
        print("Creating .env file...")
        with open(env_file, "w") as f:
            f.write("# OpenAI API Configuration\n")
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
            f.write("\n# Application Configuration\n")
            f.write("DEBUG=True\n")
            f.write("LOG_LEVEL=INFO\n")
        print("✓ .env file created - please add your OpenAI API key")
        return False
    return True

def create_sample_data():
    """Create sample data file"""
    print("Creating sample data...")
    
    try:
        # Import and run the sample data creation
        from sample_data import create_sample_excel_file
        excel_path = create_sample_excel_file()
        print(f"✓ Sample data created: {excel_path}")
        return True
    except Exception as e:
        print(f"! Could not create sample data: {e}")
        return False

def start_server():
    """Start the FastAPI server"""
    print("Starting AI Rota System server...")
    print("Server will be available at: http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        # Import uvicorn and start the server
        import uvicorn
        uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
    except ImportError:
        print("✗ uvicorn not installed. Please install dependencies first.")
        return False
    except KeyboardInterrupt:
        print("\nServer stopped by user")
        return True
    except Exception as e:
        print(f"✗ Error starting server: {e}")
        return False

def run_tests():
    """Run the test suite"""
    print("Running tests...")
    
    try:
        from test_assignment import main
        import asyncio
        asyncio.run(main())
        return True
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False

def main():
    """Main setup and run function"""
    print("AI Rota System for Healthcare")
    print("============================")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.system()} {platform.release()}")
    print()
    
    # Check if this is the first run
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        print("Available commands:")
        print("  setup    - Install dependencies and create initial files")
        print("  test     - Run test suite")
        print("  start    - Start the API server")
        print("  sample   - Create sample data")
        print("")
        command = input("Enter command (or press Enter for 'setup'): ").lower() or "setup"
    
    if command == "setup":
        print("\n=== Setting up AI Rota System ===")
        
        # Install dependencies
        if not install_dependencies():
            print("✗ Setup failed - could not install dependencies")
            return 1
        
        # Create .env file
        has_api_key = create_env_file()
        
        # Create sample data
        create_sample_data()
        
        print("\n✓ Setup completed successfully!")
        print("\nNext steps:")
        if not has_api_key:
            print("1. Add your OpenAI API key to the .env file")
        print("2. Run: python setup_and_run.py start")
        print("3. Visit http://localhost:8000/docs to see the API")
        
    elif command == "test":
        print("\n=== Running Tests ===")
        if not run_tests():
            return 1
            
    elif command == "start":
        print("\n=== Starting Server ===")
        if not start_server():
            return 1
            
    elif command == "sample":
        print("\n=== Creating Sample Data ===")
        if not create_sample_data():
            return 1
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 