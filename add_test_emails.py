#!/usr/bin/env python3
"""Script to add test user emails to allowed_emails table"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database_models import engine, AllowedEmail
from sqlalchemy.orm import sessionmaker
from datetime import datetime, UTC

def add_test_emails():
    """Add test user emails to allowed_emails table"""
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Test data
        test_emails = [
            {
                "email": "testuser1@company.com",
                "role": "staff",
                "is_registered": False
            },
            {
                "email": "testuser2@company.com", 
                "role": "staff",
                "is_registered": False
            },
            {
                "email": "admin@company.com",
                "role": "admin", 
                "is_registered": False
            }
        ]
        
        # Check if emails already exist
        existing_emails = db.query(AllowedEmail.email).all()
        existing_emails = [email[0] for email in existing_emails]
        
        added_count = 0
        for email_data in test_emails:
            if email_data["email"] not in existing_emails:
                # Create new allowed email entry
                allowed_email = AllowedEmail(
                    email=email_data["email"],
                    role=email_data["role"],
                    is_registered=email_data["is_registered"],
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )
                
                db.add(allowed_email)
                added_count += 1
                print(f"✅ Added: {email_data['email']} (Role: {email_data['role']})")
            else:
                print(f"⚠️  Already exists: {email_data['email']}")
        
        # Commit changes
        db.commit()
        print(f"\n🎉 Successfully added {added_count} new test emails!")
        
        # Show all allowed emails
        print("\n📋 Current allowed emails:")
        all_emails = db.query(AllowedEmail).all()
        for email in all_emails:
            print(f"  - {email.email} (Role: {email.role}, Registered: {email.is_registered})")
            
    except Exception as e:
        print(f"❌ Error adding test emails: {e}")
        db.rollback()
        return False
    finally:
        db.close()
    
    return True

if __name__ == "__main__":
    print("🚀 Adding test user emails to allowed_emails table...")
    print("=" * 50)
    
    if add_test_emails():
        print("\n✅ Script completed successfully!")
        print("\n🧪 You can now test the signup endpoint with these emails:")
        print("  - testuser1@company.com")
        print("  - testuser2@company.com") 
        print("  - admin@company.com")
    else:
        print("\n❌ Script failed!")
