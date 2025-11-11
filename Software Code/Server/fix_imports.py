"""
Fix Import Paths - Updates all import statements
Location: Software Code/Server/fix_imports.py
Run this to fix all import issues in the project
"""

import re
from pathlib import Path

def fix_file_imports(file_path):
    """Fix imports in a single file"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"   ✗ Error reading {file_path.name}: {e}")
        return False
    
    original_content = content
    changes_made = []
    
    # Fix patterns - order matters!
    fixes = [
        # Pattern 1: from config import
        (r'^from config import', 'from core.config import', 'config'),
        
        # Pattern 2: from tracker import
        (r'^from tracker import', 'from core.tracker import', 'tracker'),
        
        # Pattern 3: from behavior_analyzer import
        (r'^from behavior_analyzer import', 'from core.behavior_analyzer import', 'behavior_analyzer'),
        
        # Pattern 4: from csv_exporter import
        (r'^from csv_exporter import', 'from core.csv_exporter import', 'csv_exporter'),
        
        # Pattern 5: from detection_engine import
        (r'^from detection_engine import', 'from core.detection_engine import', 'detection_engine'),
        
        # Pattern 6: from alert_system import
        (r'^from alert_system import', 'from core.alert_system import', 'alert_system'),
        
        # Pattern 7: from video_processor import
        (r'^from video_processor import', 'from core.video_processor import', 'video_processor'),
        
        # Pattern 8: import config (standalone)
        (r'^import config$', 'import core.config', 'config (standalone)'),
        
        # Pattern 9: import tracker (standalone)
        (r'^import tracker$', 'import core.tracker', 'tracker (standalone)'),
    ]
    
    for pattern, replacement, description in fixes:
        matches = re.findall(pattern, content, re.MULTILINE)
        if matches:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            changes_made.append(description)
    
    # Check if content changed
    if content != original_content:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return changes_made
        except Exception as e:
            print(f"   ✗ Error writing {file_path.name}: {e}")
            return False
    
    return None


def scan_directory(directory, extensions=['.py']):
    """Scan directory for Python files"""
    files = []
    for ext in extensions:
        files.extend(directory.rglob(f'*{ext}'))
    return files


def main():
    """Main function"""
    
    BASE_DIR = Path(__file__).parent
    
    print("🔧 Fixing import paths in all Python files...")
    print("="*70)
    
    # Scan for all Python files in core and utils
    directories_to_scan = [
        BASE_DIR / "core",
        BASE_DIR / "utils",
        BASE_DIR / "routes",
    ]
    
    # Also check specific files in root
    root_files = [
        BASE_DIR / "server.py",
        BASE_DIR / "test_gui.py",
        BASE_DIR / "test.py",
    ]
    
    all_files = []
    
    # Scan directories
    for directory in directories_to_scan:
        if directory.exists():
            files = scan_directory(directory)
            all_files.extend(files)
            print(f"📁 Scanning: {directory.name}/ ({len(files)} files)")
    
    # Add root files
    for file in root_files:
        if file.exists():
            all_files.append(file)
    
    print(f"\n📊 Total files to check: {len(all_files)}")
    print("="*70)
    
    fixed_count = 0
    ok_count = 0
    error_count = 0
    
    for file_path in all_files:
        relative_path = file_path.relative_to(BASE_DIR)
        
        result = fix_file_imports(file_path)
        
        if result is False:
            print(f"✗ ERROR: {relative_path}")
            error_count += 1
        elif result is None:
            print(f"○ OK: {relative_path}")
            ok_count += 1
        else:
            print(f"✓ FIXED: {relative_path}")
            if result:
                for change in result:
                    print(f"    → Fixed import: {change}")
            fixed_count += 1
    
    print("="*70)
    print(f"\n📈 Summary:")
    print(f"   ✓ Fixed: {fixed_count} files")
    print(f"   ○ Already OK: {ok_count} files")
    print(f"   ✗ Errors: {error_count} files")
    
    if fixed_count > 0:
        print(f"\n✅ Successfully fixed {fixed_count} files!")
        print("   You can now run: python test_gui.py")
    elif error_count > 0:
        print(f"\n⚠️  Some files had errors. Please check manually.")
    else:
        print("\n✓ All imports are already correct!")
    
    print("\n💡 If you still get import errors, try:")
    print("   1. Delete all __pycache__ folders")
    print("   2. Run: python setup.py")
    print("   3. Run: python fix_imports.py")


if __name__ == "__main__":
    main()