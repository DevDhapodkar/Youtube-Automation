import os
import subprocess
import sys
import shutil

def print_step(msg):
    print(f"\n[STEP] {msg}...")

def check_prerequisites():
    print_step("Checking Prerequisites")
    
    if sys.version_info < (3, 10):
        print("❌ Error: Python 3.10 or higher is required.")
        sys.exit(1)
    print("✅ Python 3.10+ found.")

    if not shutil.which("ffmpeg"):
        print("❌ Error: FFmpeg not found. Please install it (brew install ffmpeg / sudo apt install ffmpeg).")
        sys.exit(1)
    print("✅ FFmpeg found.")

    if not shutil.which("node"):
        print("❌ Warning: Node.js not found. Web UI will not be buildable locally.")
    else:
        print("✅ Node.js found.")

def setup_environment():
    print_step("Setting up Environment")
    
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            shutil.copy(".env.example", ".env")
            print("✅ Created .env from .env.example. PLEASE FILL IN YOUR KEYS!")
        else:
            print("❌ Error: .env.example not found.")
    else:
        print("✅ .env file exists.")

    if not os.path.exists("client_secrets.json") and not os.path.exists("service-account-key.json"):
        print("⚠️ Warning: Neither client_secrets.json nor service-account-key.json found.")
        print("   YouTube upload functionality requires one of these from Google Cloud Console.")

def install_dependencies():
    print_step("Installing Dependencies")
    
    # Create Virtual Environment if it doesn't exist
    if not os.path.exists("venv"):
        print("--- Creating virtual environment ---")
        subprocess.check_call([sys.executable, "-m", "venv", "venv"])
        print("✅ Virtual environment created.")

    # Determine pip path based on OS
    pip_path = os.path.join("venv", "bin", "pip") if os.name != "nt" else os.path.join("venv", "Scripts", "pip")
    
    try:
        print("--- Installing Python dependencies in venv ---")
        subprocess.check_call([pip_path, "install", "-r", "requirements.txt"])
        
        if os.path.exists("web"):
            print("--- Installing Web dependencies ---")
            subprocess.check_call(["npm", "install"], cwd="web")
            
        print("✅ All dependencies installed successfully.")
    except Exception as e:
        print(f"❌ Error during installation: {e}")

def create_folders():
    print_step("Creating Directories")
    folders = ["logs", "temp", "assets", "outputs"]
    for folder in folders:
        path = os.path.join(os.getcwd(), folder)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"✅ Created {folder}/")
        else:
            print(f"✅ {folder}/ already exists.")

def main():
    print("==========================================")
    print("🚀 YouTube Automation Agent - Fast Setup")
    print("==========================================\n")
    
    check_prerequisites()
    setup_environment()
    create_folders()
    install_dependencies()
    
    print("\n==========================================")
    print("🎉 Setup Complete!")
    print("1. Fill in your API keys in the .env file.")
    print("2. Ensure client_secrets.json is present.")
    print("3. Start the agent:")
    print("   - Mac/Linux: ./start.sh")
    print("   - Windows: start.bat")
    print("==========================================\n")

if __name__ == "__main__":
    main()
