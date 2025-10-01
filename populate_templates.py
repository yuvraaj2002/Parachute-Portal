#!/usr/bin/env python3
"""
Database population script for Templates table
Populates the templates table with the provided template data
"""

import sys
import os
from datetime import datetime, UTC
from sqlalchemy import text

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database_models import SessionLocal, Templates
from config import settings

def populate_templates():
    """Populate the templates table with the provided data"""
    
    # Template data to be inserted
    # NOTE: s3_path should point to PDF template files (not markdown)
    # These PDFs will be downloaded from S3, filled with data using PyMuPDF, and uploaded back to S3
    templates_data = [
        {
            "name": "CGM Resupply Agreement OHS",
            "description": "Continuous Glucose Monitoring resupply agreement for OHS patients",
            "category": "Resupply Agreements",
            "s3_path": "pdf_templates/CGM_Resupply_Agreement_OHS.pdf"  # S3 key path (not full URL)
        },
        {
            "name": "DME Intake Form (Final)",
            "description": "Final version of the comprehensive DME intake form",
            "category": "Intake Forms",
            "s3_path": "pdf_templates/DME_Intake_Form_Final.pdf"
        },
        {
            "name": "DME Intake Form (Victor Contreras)",
            "description": "Specialized DME intake form for Victor Contreras",
            "category": "Intake Forms",
            "s3_path": "pdf_templates/DME_Intake_Form_Victor_Contreras.pdf"
        },
        {
            "name": "Non Medicare DME Intake Form",
            "description": "Specialized intake form for non-Medicare DME patients",
            "category": "Intake Forms",
            "s3_path": "pdf_templates/Non_Medicare_DME_Intake_Form.pdf"
        },
        {
            "name": "Purewick Resupply Agreement OHS",
            "description": "Purewick resupply agreement for OHS patients",
            "category": "Resupply Agreements",
            "s3_path": "https://dme-portal.s3.amazonaws.com/pdf_templates/Purewick_Resupply_Agreement_OHC_Template.pdf"  # Full S3 URL
        },
        {
            "name": "Taylor Cook Non Medicare Intake Form",
            "description": "Non-Medicare intake form for Taylor Cook",
            "category": "Intake Forms",
            "s3_path": "pdf_templates/Taylor_Cook_Non_Medicare_Intake_Form.pdf"
        }
    ]
    
    # Create database session
    db = SessionLocal()
    
    try:
        print("Starting template population...")
        
        # Check if templates already exist
        existing_templates = db.query(Templates).all()
        if existing_templates:
            print(f"Found {len(existing_templates)} existing templates in database.")
            response = input("Do you want to continue? This may create duplicates. (y/N): ")
            if response.lower() != 'y':
                print("Operation cancelled.")
                return
        
        # Insert templates
        inserted_count = 0
        skipped_count = 0
        
        for template_data in templates_data:
            # Check if template with this name already exists
            existing_template = db.query(Templates).filter(
                Templates.name == template_data["name"]
            ).first()
            
            if existing_template:
                print(f"Template '{template_data['name']}' already exists. Skipping...")
                skipped_count += 1
                continue
            
            # Create new template
            template = Templates(
                name=template_data["name"],
                description=template_data["description"],
                category=template_data["category"],
                s3_path=template_data["s3_path"],
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            
            db.add(template)
            inserted_count += 1
            print(f"Added template: {template_data['name']}")
        
        # Commit all changes
        db.commit()
        print(f"\nTemplate population completed successfully!")
        print(f"Inserted: {inserted_count} templates")
        print(f"Skipped: {skipped_count} templates")
        
        # Display all templates in the database
        all_templates = db.query(Templates).all()
        print(f"\nTotal templates in database: {len(all_templates)}")
        print("\nTemplate list:")
        for template in all_templates:
            print(f"- {template.name} ({template.category})")
            if template.s3_path:
                print(f"  S3 Path: {template.s3_path}")
            print(f"  Description: {template.description}")
            print()
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def main():
    """Main function"""
    print("Templates Database Population Script")
    print("=" * 40)
    
    # Verify database connection
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("Database connection successful.")
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        print("Please check your database configuration in config.py")
        return
    
    # Run population
    populate_templates()

if __name__ == "__main__":
    main()
