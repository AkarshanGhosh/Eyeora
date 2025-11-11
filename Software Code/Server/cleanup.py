"""
Cleanup Script - Remove cache files and temporary data
Location: Software Code/Server/cleanup.py
"""

import shutil
from pathlib import Path

def remove_pycache(directory):
    """Remove all __pycache__ directories"""
    removed_count = 0
    
    for pycache in directory.rglob('__pycache__'):
        try:
            shutil.rmtree(pycache)
            print(f"   ✓ Removed: {pycache.relative_to(directory)}")
            removed_count += 1
        except Exception as e:
            print(f"   ✗ Failed to remove {pycache}: {e}")
    
    return removed_count


def remove_pyc_files(directory):
    """Remove all .pyc files"""
    removed_count = 0
    
    for pyc in directory.rglob('*.pyc'):
        try:
            pyc.unlink()
            print(f"   ✓ Removed: {pyc.relative_to(directory)}")
            removed_count += 1
        except Exception as e:
            print(f"   ✗ Failed to remove {pyc}: {e}")
    
    return removed_count


def main():
    """Main cleanup function"""
    
    BASE_DIR = Path(__file__).parent
    
    print("🧹 Cleaning up cache files...")
    print("="*60)
    
    # Remove __pycache__ directories
    print("\n📁 Removing __pycache__ directories...")
    cache_count = remove_pycache(BASE_DIR)
    
    # Remove .pyc files
    print("\n📄 Removing .pyc files...")
    pyc_count = remove_pyc_files(BASE_DIR)
    
    print("\n" + "="*60)
    print(f"✅ Cleanup complete!")
    print(f"   Removed {cache_count} __pycache__ directories")
    print(f"   Removed {pyc_count} .pyc files")
    
    if cache_count > 0 or pyc_count > 0:
        print("\n💡 Cache cleaned! Now run:")
        print("   python fix_imports.py")
        print("   python test_gui.py")
    else:
        print("\n✓ No cache files found")


if __name__ == "__main__":
    main()