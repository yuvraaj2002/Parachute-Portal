#!/usr/bin/env python3
"""
Deployment Zip Creator for Mental Health Bot
Creates a clean zip file for EC2 deployment, excluding sensitive files
"""

import os
import zipfile
import shutil
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeploymentZipCreator:
    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.zip_filename = f"dme_portal_deployment_{self.timestamp}.zip"
        
        # Files and directories to exclude
        self.exclude_patterns = [
            # Environment and secrets
            '.env',
            '.env.local',
            '.env.production',
            '.env.staging',
            'secrets.json',
            'config.json',
            
            # Python cache and virtual environments
            '__pycache__',
            '*.pyc',
            '*.pyo',
            '*.pyd',
            '.Python',
            '.venv',
            'venv',
            'env',
            'ENV',
            
            # IDE and editor files
            '.vscode',
            '.idea',
            '*.swp',
            '*.swo',
            '*~',
            '.DS_Store',
            'Thumbs.db',
            
            # Git and version control
            '.git',
            '.gitignore',
            '.gitattributes',
            
            # Logs and temporary files
            '*.log',
            'logs',
            'temp',
            'tmp',
            '*.tmp',
            
            # Database files
            '*.db',
            '*.sqlite',
            '*.sqlite3',
            
            # Node modules (if any)
            'node_modules',
            'package-lock.json',
            'yarn.lock',
            
            # Build and distribution
            'build',
            'dist',
            '*.egg-info',
            
            # Testing
            'testing',
            'tests',
            'test_*.py',
            '*_test.py',
            
            # Documentation
            'docs',
            '*.md',
            'README.md',
            
            # Deployment scripts
            'create_deployment_zip.py',
            'deploy.sh',
            'deploy.py',
            
            # Backup files
            '*.bak',
            '*.backup',
            '*.old',
            
            # OS generated files
            '.DS_Store',
            '.Trashes',
            'ehthumbs.db',
            'Desktop.ini'
        ]
    
    def should_exclude(self, file_path: str) -> bool:
        """Check if a file or directory should be excluded"""
        rel_path = os.path.relpath(file_path, self.project_root)
        
        # Check each exclude pattern
        for pattern in self.exclude_patterns:
            if pattern.startswith('*'):
                # Pattern like *.pyc
                if rel_path.endswith(pattern[1:]):
                    return True
            elif pattern.startswith('.'):
                # Hidden files/directories
                if rel_path.startswith(pattern) or pattern in rel_path.split(os.sep):
                    return True
            else:
                # Exact match or directory
                if rel_path == pattern or pattern in rel_path.split(os.sep):
                    return True
        
        return False
    
    def create_zip(self) -> str:
        """Create the deployment zip file"""
        zip_path = os.path.join(self.project_root, self.zip_filename)
        
        logger.info(f"Creating deployment zip: {self.zip_filename}")
        logger.info(f"Project root: {self.project_root}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.project_root):
                # Remove excluded directories from dirs list to prevent walking into them
                dirs[:] = [d for d in dirs if not self.should_exclude(os.path.join(root, d))]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    if not self.should_exclude(file_path):
                        # Calculate relative path for zip
                        rel_path = os.path.relpath(file_path, self.project_root)
                        
                        # Add file to zip
                        zipf.write(file_path, rel_path)
                        logger.info(f"Added: {rel_path}")
                    else:
                        logger.debug(f"Excluded: {os.path.relpath(file_path, self.project_root)}")
        
        logger.info(f"Deployment zip created successfully: {zip_path}")
        logger.info(f"Zip file size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB")
        
        return zip_path
    
    def get_included_files_summary(self) -> dict:
        """Get a summary of what's included in the zip"""
        included_files = []
        excluded_files = []
        
        for root, dirs, files in os.walk(self.project_root):
            # Check directories
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                rel_path = os.path.relpath(dir_path, self.project_root)
                if self.should_exclude(dir_path):
                    excluded_files.append(f"{rel_path}/")
                else:
                    included_files.append(f"{rel_path}/")
            
            # Check files
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.project_root)
                if self.should_exclude(file_path):
                    excluded_files.append(rel_path)
                else:
                    included_files.append(rel_path)
        
        return {
            'included': sorted(included_files),
            'excluded': sorted(excluded_files),
            'total_included': len(included_files),
            'total_excluded': len(excluded_files)
        }

def main():
    """Main function to create deployment zip"""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create zip creator instance
    creator = DeploymentZipCreator(script_dir)
    
    try:
        # Create the zip file
        zip_path = creator.create_zip()
        
        # Get summary
        summary = creator.get_included_files_summary()
        
        # Print summary
        print("\n" + "="*60)
        print("DEPLOYMENT ZIP SUMMARY")
        print("="*60)
        print(f"Zip file: {creator.zip_filename}")
        print(f"Location: {zip_path}")
        print(f"Total files included: {summary['total_included']}")
        print(f"Total files excluded: {summary['total_excluded']}")
        
        print("\n" + "-"*40)
        print("INCLUDED FILES/DIRECTORIES:")
        print("-"*40)
        for item in summary['included'][:20]:  # Show first 20
            print(f"✅ {item}")
        if len(summary['included']) > 20:
            print(f"... and {len(summary['included']) - 20} more files")
        
        print("\n" + "-"*40)
        print("EXCLUDED FILES/DIRECTORIES:")
        print("-"*40)
        for item in summary['excluded'][:20]:  # Show first 20
            print(f"❌ {item}")
        if len(summary['excluded']) > 20:
            print(f"... and {len(summary['excluded']) - 20} more files")
        
        print("\n" + "="*60)
        print("DEPLOYMENT READY!")
        print("="*60)
        print(f"📦 Zip file created: {creator.zip_filename}")
        print(f"🚀 Ready to upload to EC2 instance")
        print(f"💡 Tip: Use 'scp' or drag & drop to your EC2 instance")
        
    except Exception as e:
        logger.error(f"Failed to create deployment zip: {e}")
        print(f"❌ Error creating deployment zip: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
