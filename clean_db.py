#!/usr/bin/env python3
"""Temporary script to clean alembic_version table"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database_models import engine
from sqlalchemy import text

def clean_alembic_version():
    """Clean the alembic_version table"""
    try:
        with engine.connect() as connection:
            # Delete all records from alembic_version table
            result = connection.execute(text("DELETE FROM alembic_version"))
            connection.commit()
            print(f"✅ Cleaned alembic_version table. Deleted {result.rowcount} records.")
            
    except Exception as e:
        print(f"❌ Error cleaning alembic_version table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧹 Cleaning alembic_version table...")
    if clean_alembic_version():
        print("✅ Database cleaned successfully!")
    else:
        print("❌ Failed to clean database")
