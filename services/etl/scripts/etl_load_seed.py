#!/usr/bin/env python3
"""
Load seed data into FightMatch database.

This script reads the seed SQL file and executes it against the database.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Load environment variables
load_dotenv()

# Get database URL
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("Error: DATABASE_URL environment variable not set")
    sys.exit(1)

# Path to seed SQL file (relative to repo root)
REPO_ROOT = Path(__file__).parent.parent.parent
SEED_SQL_PATH = REPO_ROOT / 'supabase' / 'seed.sql'

if not SEED_SQL_PATH.exists():
    print(f"Error: Seed SQL file not found at {SEED_SQL_PATH}")
    sys.exit(1)


def load_seed_data():
    """Load seed data from SQL file."""
    print(f"Loading seed data from {SEED_SQL_PATH}...")
    
    # Read SQL file
    with open(SEED_SQL_PATH, 'r') as f:
        sql_content = f.read()
    
    # Connect to database
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Execute SQL (split by semicolons for better error handling)
        # Note: This is a simplified approach. For production, use a proper SQL parser
        statements = [s.strip() for s in sql_content.split(';') if s.strip()]
        
        for i, statement in enumerate(statements, 1):
            if statement:
                try:
                    cursor.execute(statement)
                    print(f"Executed statement {i}/{len(statements)}")
                except Exception as e:
                    # Some statements might fail if data already exists (ON CONFLICT)
                    if 'duplicate key' in str(e).lower() or 'already exists' in str(e).lower():
                        print(f"  Skipped (already exists): {str(e)[:100]}")
                    else:
                        print(f"  Warning: {str(e)[:100]}")
        
        cursor.close()
        conn.close()
        
        print("Seed data loaded successfully!")
        
    except psycopg2.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    load_seed_data()

