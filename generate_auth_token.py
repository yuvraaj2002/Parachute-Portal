#!/usr/bin/env python3
"""
Auth Token Generator for Test Accounts

This script creates test users and generates JWT auth tokens for testing the API.
It works with the test emails added via add_test_emails.py

Usage:
    python generate_auth_token.py
"""

import sys
import os
from datetime import datetime, timedelta, UTC

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database_models import engine, User, AllowedEmail
from sqlalchemy.orm import sessionmaker
from services.auth_service import create_access_token, get_password_hash
from config import settings

def create_test_users():
    """Create test users for the allowed emails"""
    
    # Create session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Test user data
        test_users = [
            {
                "first_name": "Test",
                "last_name": "User1",
                "username": "testuser1",
                "email": "testuser1@company.com",
                "password": "testpass123",
                "is_admin": False
            },
            {
                "first_name": "Test",
                "last_name": "User2", 
                "username": "testuser2",
                "email": "testuser2@company.com",
                "password": "testpass123",
                "is_admin": False
            },
            {
                "first_name": "Admin",
                "last_name": "User",
                "username": "admin",
                "email": "admin@company.com",
                "password": "adminpass123",
                "is_admin": True
            }
        ]
        
        created_users = []
        
        for user_data in test_users:
            # Check if user already exists
            existing_user = db.query(User).filter(User.email == user_data["email"]).first()
            
            if existing_user:
                print(f"⚠️  User already exists: {user_data['email']}")
                # Extract user data before session closes
                user_info = {
                    "id": existing_user.id,
                    "email": existing_user.email,
                    "first_name": existing_user.first_name,
                    "last_name": existing_user.last_name,
                    "username": existing_user.username,
                    "is_admin": existing_user.is_admin
                }
                created_users.append(user_info)
            else:
                # Create new user
                hashed_password = get_password_hash(user_data["password"])
                
                user = User(
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=hashed_password,
                    is_active=True,
                    is_admin=user_data["is_admin"],
                    created_at=datetime.now(UTC),
                    updated_at=datetime.now(UTC)
                )
                
                db.add(user)
                db.flush()  # Get the user ID
                
                # Extract user data before session closes
                user_info = {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "username": user.username,
                    "is_admin": user.is_admin
                }
                created_users.append(user_info)
                print(f"✅ Created user: {user_data['email']} (Role: {'Admin' if user_data['is_admin'] else 'Staff'})")
        
        # Commit changes
        db.commit()
        
        # Update allowed emails to mark as registered
        for user_info in created_users:
            allowed_email = db.query(AllowedEmail).filter(AllowedEmail.email == user_info["email"]).first()
            if allowed_email:
                allowed_email.is_registered = True
                allowed_email.user_id = user_info["id"]
                allowed_email.updated_at = datetime.now(UTC)
        
        db.commit()
        print(f"\n🎉 Successfully processed {len(created_users)} users!")
        
        return created_users
        
    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        db.rollback()
        return []
    finally:
        db.close()

def generate_auth_tokens(users):
    """Generate JWT auth tokens for the users"""
    
    if not users:
        print("❌ No users provided for token generation")
        return []
    
    tokens = []
    
    for user_info in users:
        try:
            # Create token data
            token_data = {
                "sub": user_info["email"],
                "user_id": user_info["id"],
                "is_admin": user_info["is_admin"],
                "username": user_info["username"]
            }
            
            # Generate token (expires in 30 minutes by default)
            token = create_access_token(data=token_data)
            
            # Also create a long-lived token (24 hours) for testing
            long_token = create_access_token(
                data=token_data, 
                expires_delta=timedelta(hours=24)
            )
            
            token_info = {
                "user": user_info,
                "token": token,
                "long_token": long_token,
                "expires_in": "30 minutes",
                "long_expires_in": "24 hours"
            }
            
            tokens.append(token_info)
            
            print(f"\n🔑 Generated tokens for {user_info['email']}:")
            print(f"   User ID: {user_info['id']}")
            print(f"   Role: {'Admin' if user_info['is_admin'] else 'Staff'}")
            print(f"   Short Token (30min): {token[:50]}...")
            print(f"   Long Token (24h): {long_token[:50]}...")
            
        except Exception as e:
            print(f"❌ Error generating token for {user_info['email']}: {e}")
    
    return tokens

def save_tokens_to_file(tokens):
    """Save tokens to a file for easy access"""
    
    if not tokens:
        print("❌ No tokens to save")
        return
    
    try:
        with open("test_auth_tokens.txt", "w") as f:
            f.write("=== TEST AUTH TOKENS ===\n")
            f.write(f"Generated at: {datetime.now(UTC).isoformat()}\n")
            f.write("=" * 50 + "\n\n")
            
            for token_info in tokens:
                user = token_info["user"]
                f.write(f"User: {user['first_name']} {user['last_name']} ({user['email']})\n")
                f.write(f"Role: {'Admin' if user['is_admin'] else 'Staff'}\n")
                f.write(f"User ID: {user['id']}\n")
                f.write(f"Username: {user['username']}\n")
                f.write(f"Password: {'adminpass123' if user['is_admin'] else 'testpass123'}\n")
                f.write(f"Short Token (30min): {token_info['token']}\n")
                f.write(f"Long Token (24h): {token_info['long_token']}\n")
                f.write("-" * 50 + "\n\n")
            
            f.write("\n=== USAGE EXAMPLES ===\n")
            f.write("curl -H \"Authorization: Bearer YOUR_TOKEN_HERE\" http://localhost:8000/agent/documents\n")
            f.write("curl -H \"Authorization: Bearer YOUR_TOKEN_HERE\" http://localhost:8000/agent/analyze-document -F \"file=@test.pdf\"\n")
        
        print(f"\n💾 Tokens saved to: test_auth_tokens.txt")
        
    except Exception as e:
        print(f"❌ Error saving tokens to file: {e}")

def main():
    """Main function to create users and generate tokens"""
    
    print("🚀 Auth Token Generator for Test Accounts")
    print("=" * 50)
    
    # Check if JWT secret key is set
    if not settings.jwt_secret_key:
        print("❌ JWT secret key not set in config.py!")
        print("   Please set jwt_secret_key in your config.py file")
        return False
    
    # Create test users
    print("\n📝 Creating test users...")
    users = create_test_users()
    
    if not users:
        print("❌ Failed to create users")
        return False
    
    # Generate auth tokens
    print("\n🔑 Generating auth tokens...")
    tokens = generate_auth_tokens(users)
    
    if not tokens:
        print("❌ Failed to generate tokens")
        return False
    
    # Save tokens to file
    print("\n💾 Saving tokens to file...")
    save_tokens_to_file(tokens)
    
    print("\n✅ Token generation completed successfully!")
    print("\n🧪 You can now use these tokens to test the API:")
    print("   - Use the tokens in the Authorization header")
    print("   - Format: 'Authorization: Bearer YOUR_TOKEN_HERE'")
    print("   - Check test_auth_tokens.txt for all tokens")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)