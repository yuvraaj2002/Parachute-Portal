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


def add_template_interactive():
    """Add a template interactively by taking user input"""
    print("\n" + "=" * 60)
    print("ADD NEW TEMPLATE - INTERACTIVE MODE")
    print("=" * 60)
    
    # Get template details from user
    print("\nEnter template details:")
    print("-" * 60)
    
    name = input("Template Name: ").strip()
    if not name:
        print("❌ Template name is required!")
        return
    
    description = input("Description: ").strip()
    if not description:
        print("❌ Description is required!")
        return
    
    print("\nAvailable Categories:")
    print("  1. Resupply Agreements")
    print("  2. Intake Forms")
    print("  3. Other")
    category_choice = input("Select category (1-3) or enter custom: ").strip()
    
    category_map = {
        "1": "Resupply Agreements",
        "2": "Intake Forms",
        "3": "Other"
    }
    
    category = category_map.get(category_choice, category_choice)
    if not category:
        print("❌ Category is required!")
        return
    
    print("\nS3 Path can be:")
    print("  - S3 key: pdf_templates/Your_Template.pdf")
    print("  - Full URL: https://dme-portal.s3.amazonaws.com/pdf_templates/Your_Template.pdf")
    s3_path = input("S3 Path: ").strip()
    if not s3_path:
        print("❌ S3 path is required!")
        return
    
    # Confirmation
    print("\n" + "=" * 60)
    print("TEMPLATE SUMMARY")
    print("=" * 60)
    print(f"Name:        {name}")
    print(f"Description: {description}")
    print(f"Category:    {category}")
    print(f"S3 Path:     {s3_path}")
    print("=" * 60)
    
    confirm = input("\nDo you want to create this template? (y/N): ").strip().lower()
    if confirm != 'y':
        print("❌ Operation cancelled.")
        return
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Note: Allowing duplicate names as per user requirement
        
        # Create new template
        template = Templates(
            name=name,
            description=description,
            category=category,
            s3_path=s3_path,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC)
        )
        
        db.add(template)
        db.commit()
        
        print(f"\n✅ Template '{name}' created successfully!")
        print(f"   ID: {template.id}")
        print(f"   Category: {template.category}")
        
    except Exception as e:
        print(f"\n❌ Error creating template: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

def list_templates():
    """List all templates in the database"""
    db = SessionLocal()
    
    try:
        templates = db.query(Templates).all()
        
        if not templates:
            print("\n📭 No templates found in database.")
            return
        
        print(f"\n📋 TEMPLATES IN DATABASE ({len(templates)} total)")
        print("=" * 80)
        
        for i, template in enumerate(templates, 1):
            print(f"\n{i}. {template.name}")
            print(f"   ID:          {template.id}")
            print(f"   Category:    {template.category}")
            print(f"   Description: {template.description}")
            print(f"   S3 Path:     {template.s3_path}")
            print(f"   Created:     {template.created_at}")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error listing templates: {str(e)}")
    finally:
        db.close()

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("TEMPLATES DATABASE MANAGEMENT")
    print("=" * 60)
    
    # Verify database connection
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("✅ Database connection successful.")
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        print("Please check your database configuration in config.py")
        return
    
    # Main menu
    while True:
        print("\n" + "=" * 60)
        print("MENU")
        print("=" * 60)
        print("1. Add new template (interactive)")
        print("2. List all templates")
        print("3. Exit")
        print("=" * 60)
        
        choice = input("\nSelect an option (1-4): ").strip()
        
        if choice == "1":
            add_template_interactive()
        elif choice == "2":
            list_templates()
        elif choice == "3":
            print("\n👋 Goodbye!")
            break
        else:
            print("\n❌ Invalid option. Please select 1-4.")

if __name__ == "__main__":
    main()
