"""
Setup Script - Creates necessary directories and checks dependencies
Location: Software Code/Server/setup.py
"""

import os
import sys
from pathlib import Path

def create_directory_structure():
    """Create all necessary directories"""
    
    BASE_DIR = Path(__file__).parent
    
    directories = [
        BASE_DIR / "core",
        BASE_DIR / "routes",
        BASE_DIR / "utils",
        BASE_DIR / "tests",
        BASE_DIR / "models",
        BASE_DIR / "Uploads" / "images",
        BASE_DIR / "Uploads" / "videos",
        BASE_DIR / "processed" / "images",
        BASE_DIR / "processed" / "videos",
        BASE_DIR / "data" / "csv",
        BASE_DIR / "data" / "reports",
        BASE_DIR / "static" / "css",
        BASE_DIR / "static" / "js",
        BASE_DIR / "static" / "assets",
    ]
    
    print("📁 Creating directory structure...")
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {directory.relative_to(BASE_DIR)}")
    
    print("✅ Directory structure created successfully")


def create_init_files():
    """Create __init__.py files in package directories"""
    
    BASE_DIR = Path(__file__).parent
    
    packages = [
        BASE_DIR / "core",
        BASE_DIR / "routes",
        BASE_DIR / "utils",
        BASE_DIR / "tests",
    ]
    
    print("\n📝 Creating __init__.py files...")
    
    for package in packages:
        init_file = package / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"   ✓ {init_file.relative_to(BASE_DIR)}")
        else:
            print(f"   ○ {init_file.relative_to(BASE_DIR)} (already exists)")
    
    print("✅ Package files created successfully")


def check_dependencies():
    """Check if required packages are installed"""
    
    print("\n🔍 Checking dependencies...")
    
    required_packages = [
        ('cv2', 'opencv-python'),
        ('numpy', 'numpy'),
        ('fastapi', 'fastapi'),
        ('uvicorn', 'uvicorn'),
        ('pandas', 'pandas'),
        ('PIL', 'pillow'),
        ('ultralytics', 'ultralytics'),
        ('torch', 'torch'),
    ]
    
    missing_packages = []
    
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print(f"   ✓ {package_name}")
        except ImportError:
            print(f"   ✗ {package_name} - NOT INSTALLED")
            missing_packages.append(package_name)
    
    if missing_packages:
        print("\n⚠️  Missing packages detected!")
        print(f"   Run: pip install {' '.join(missing_packages)}")
        print("   Or: pip install -r requirements.txt")
        return False
    else:
        print("✅ All dependencies installed")
        return True


def download_yolo_model():
    """Download YOLO model if not exists"""
    
    print("\n🤖 Checking YOLO model...")
    
    BASE_DIR = Path(__file__).parent
    model_path = BASE_DIR / "models" / "yolo11x.pt"
    
    if model_path.exists():
        print(f"   ✓ YOLO model found: {model_path}")
        return True
    
    try:
        print("   📥 Downloading YOLO11x model (this may take a few minutes)...")
        from ultralytics import YOLO
        
        model = YOLO('yolo11x.pt')
        print(f"   ✓ Model downloaded successfully")
        return True
    
    except Exception as e:
        print(f"   ✗ Model download failed: {e}")
        print("   💡 Model will be downloaded automatically on first use")
        return False


def create_env_file():
    """Create .env file template"""
    
    BASE_DIR = Path(__file__).parent
    env_file = BASE_DIR / ".env"
    
    if env_file.exists():
        print(f"\n✓ .env file already exists")
        return
    
    print("\n📄 Creating .env template...")
    
    env_content = """# Eyeora AI-CCTV Environment Variables

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000

# MongoDB Configuration (optional)
MONGODB_URI=mongodb://localhost:27017/
DATABASE_NAME=eyeora_db

# Model Configuration
YOLO_MODEL=yolo11x.pt
CONFIDENCE_THRESHOLD=0.4

# Processing Configuration
VIDEO_FPS_PROCESS=10
CROWD_THRESHOLD=10
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"   ✓ Created .env file")


def print_next_steps():
    """Print next steps for the user"""
    
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("   1. Install missing dependencies (if any):")
    print("      pip install -r requirements.txt")
    print("\n   2. Run the test GUI:")
    print("      python test_gui.py")
    print("\n   3. Start the server:")
    print("      python server.py")
    print("\n   4. Test the API:")
    print("      Open http://localhost:8000/docs")
    
    print("\n💡 Tips:")
    print("   - Place test videos in: Uploads/videos/")
    print("   - Place test images in: Uploads/images/")
    print("   - Check results in: processed/")
    print("   - View reports in: data/csv/ and data/reports/")
    
    print("\n" + "="*60)


def main():
    """Main setup function"""
    
    print("="*60)
    print("🚀 Eyeora AI-CCTV Setup")
    print("="*60)
    
    # Create directories
    create_directory_structure()
    
    # Create __init__.py files
    create_init_files()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Create .env file
    create_env_file()
    
    # Download YOLO model (optional)
    if deps_ok:
        download_yolo_model()
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()