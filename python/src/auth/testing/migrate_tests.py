#!/usr/bin/env python3
"""
Test Migration Script

This script helps migrate tests from the legacy structure to the new modular structure.
It provides utilities for organizing tests and updating imports.
"""

import os
import shutil
import sys
from pathlib import Path

def create_directory_structure():
    """Create the new directory structure if it doesn't exist."""
    directories = [
        'unit',
        'integration', 
        'fixtures',
        'config',
        'data',
        'legacy'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        init_file = Path(directory) / '__init__.py'
        if not init_file.exists():
            init_file.touch()
    
    print("✅ Created directory structure")

def move_files_to_legacy():
    """Move existing test files to legacy directory for backward compatibility."""
    legacy_files = [
        'test_auth_endpoints.py',
        'test_auth_health.py', 
        'test_auth_login.py',
        'test_auth_registration.py',
        'test_auth_unit.py'
    ]
    
    for file in legacy_files:
        if os.path.exists(file):
            shutil.move(file, f'legacy/{file}')
            print(f"✅ Moved {file} to legacy/")
        else:
            print(f"⚠️ File {file} not found")

def move_config_files():
    """Move configuration files to appropriate directories."""
    config_files = {
        'pytest.ini': 'config/',
        'test_init.sql': 'data/',
        'setup_test_db.py': 'data/'
    }
    
    for file, destination in config_files.items():
        if os.path.exists(file):
            shutil.move(file, f'{destination}{file}')
            print(f"✅ Moved {file} to {destination}")
        else:
            print(f"⚠️ File {file} not found")

def update_conftest_location():
    """Move conftest.py to fixtures directory."""
    if os.path.exists('conftest.py'):
        shutil.move('conftest.py', 'fixtures/conftest.py')
        print("✅ Moved conftest.py to fixtures/")
    else:
        print("⚠️ conftest.py not found")

def create_symlink_for_backward_compatibility():
    """Create symlinks for backward compatibility."""
    try:
        # Create symlink for conftest.py in root
        if not os.path.exists('conftest.py'):
            os.symlink('fixtures/conftest.py', 'conftest.py')
            print("✅ Created symlink for conftest.py")
        
        # Create symlink for pytest.ini in root
        if not os.path.exists('pytest.ini'):
            os.symlink('config/pytest.ini', 'pytest.ini')
            print("✅ Created symlink for pytest.ini")
            
    except OSError as e:
        print(f"⚠️ Could not create symlinks: {e}")
        print("   This is normal on Windows or if symlinks are not supported")

def print_migration_summary():
    """Print a summary of the migration."""
    print("\n" + "="*60)
    print("🎉 MIGRATION COMPLETE!")
    print("="*60)
    print("\n📁 New Structure:")
    print("├── unit/           # Unit tests for core functions")
    print("├── integration/    # Integration tests for endpoints") 
    print("├── fixtures/       # Test fixtures and configuration")
    print("├── config/         # Test configuration files")
    print("├── data/           # Test data and database setup")
    print("└── legacy/         # Legacy tests (backward compatibility)")
    
    print("\n🚀 Next Steps:")
    print("1. Run tests to verify everything works:")
    print("   pytest")
    print("   pytest unit/")
    print("   pytest integration/")
    print("   pytest legacy/")
    
    print("\n2. Gradually migrate tests from legacy/ to appropriate directories")
    print("3. Update any import statements in your tests")
    print("4. Update CI/CD pipelines if needed")
    
    print("\n📚 Documentation:")
    print("- See README.md for detailed usage instructions")
    print("- Check pytest.ini for test markers and configuration")

def main():
    """Main migration function."""
    print("🔄 Starting test structure migration...")
    
    # Create new directory structure
    create_directory_structure()
    
    # Move existing files to legacy
    move_files_to_legacy()
    
    # Move configuration files
    move_config_files()
    
    # Update conftest location
    update_conftest_location()
    
    # Create symlinks for backward compatibility
    create_symlink_for_backward_compatibility()
    
    # Print summary
    print_migration_summary()

if __name__ == "__main__":
    main() 