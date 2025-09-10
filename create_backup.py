#!/usr/bin/env python3
"""
Script to create a zip backup of the current project with current date in filename.
"""

import os
import zipfile
from datetime import datetime
import sys

def create_project_backup():
    """
    Create a zip file of the current project with current date in the filename.
    Excludes common directories that shouldn't be backed up.
    """
    
    # Get current directory (project root)
    project_root = os.getcwd()
    project_name = os.path.basename(project_root)
    
    # Create filename with current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    zip_filename = f"{project_name}_backup_{current_date}.zip"
    
    # Directories and files to exclude
    exclude_dirs = {
        '.git',
        '__pycache__',
        '.venv',
        'venv',
        'env',
        'node_modules',
        '.pytest_cache',
        '.coverage',
        'htmlcov',
        'dist',
        'build',
        '.mypy_cache',
        '.ruff_cache'
    }
    
    exclude_files = {
        '.DS_Store',
        'Thumbs.db',
        '*.pyc',
        '*.pyo',
        '*.pyd',
        '.Python',
        '*.log'
    }
    
    print(f"Creating backup: {zip_filename}")
    print(f"Project root: {project_root}")
    
    try:
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(project_root):
                # Remove excluded directories from dirs list
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
                
                for file in files:
                    # Skip excluded files
                    if any(file.endswith(ext) for ext in ['.pyc', '.pyo', '.pyd']) or file in exclude_files:
                        continue
                    
                    file_path = os.path.join(root, file)
                    
                    # Skip the backup file itself if it exists
                    if file_path == os.path.join(project_root, zip_filename):
                        continue
                    
                    # Calculate relative path for the zip file
                    arcname = os.path.relpath(file_path, project_root)
                    
                    try:
                        zipf.write(file_path, arcname)
                        print(f"Added: {arcname}")
                    except Exception as e:
                        print(f"Warning: Could not add {arcname}: {e}")
        
        print(f"\n✅ Backup created successfully: {zip_filename}")
        print(f"📁 Location: {os.path.abspath(zip_filename)}")
        
        # Get file size
        file_size = os.path.getsize(zip_filename)
        size_mb = file_size / (1024 * 1024)
        print(f"📊 Size: {size_mb:.2f} MB")
        
    except Exception as e:
        print(f"❌ Error creating backup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_project_backup()
