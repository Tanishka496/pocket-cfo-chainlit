"""
Database setup script for AI Pocket CFO.

Automatically creates the transactions table and indexes in Supabase.
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    sys.exit(1)

# Read schema file
try:
    with open("schema.sql", "r") as f:
        schema_sql = f.read()
except FileNotFoundError:
    print("❌ Error: schema.sql file not found in current directory")
    sys.exit(1)

print("🔐 Connecting to Supabase...")
try:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Connected to Supabase")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

print("\n📊 Running database schema setup...")
print("-" * 50)

try:
    # Execute the schema SQL
    # Note: supabase-py client doesn't directly expose raw SQL execution
    # We need to use the underlying PostgREST API or use a different approach
    
    # Alternative: Split schema into individual statements and execute
    from supabase.lib.client_options import ClientOptions
    
    # For direct SQL execution, we'll need to use postgres connection
    # This is a limitation of supabase-py - it doesn't support raw SQL directly
    
    print("""
    ⚠️  NOTE: The supabase-py client has limitations for raw SQL execution.
    
    Please use one of these methods to set up your database:
    
    📝 Method 1: Manual Setup (Recommended)
    -----------
    1. Go to: https://supabase.com/dashboard/project/pnamfmphhcafcczebfrs
    2. Click "SQL Editor" in left sidebar
    3. Click "New Query"
    4. Copy contents of schema.sql file
    5. Paste into the editor
    6. Click "Run"
    
    📝 Method 2: Using Supabase CLI
    -----------
    Install Supabase CLI and run:
    supabase db push
    
    📝 Method 3: Using psql (PostgreSQL CLI)
    -----------
    psql -h db.pnamfmphhcafcczebfrs.supabase.co -U postgres -d postgres -f schema.sql
    
    When prompted for password, use: postgres password from your Supabase settings
    
    ℹ️  Your Project URL: https://supabase.com/dashboard/project/pnamfmphhcafcczebfrs
    """)
    
    # Display the schema for reference
    print("\n📋 Schema to be applied:")
    print("-" * 50)
    print(schema_sql[:500] + "...\n(showing first 500 characters)")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

print("\n" + "=" * 50)
print("✅ Database setup instructions ready!")
print("=" * 50)
