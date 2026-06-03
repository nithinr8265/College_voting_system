"""
create_admin.py — Run this once to create your first admin account.

Usage:
    python create_admin.py

It will prompt for username + password, hash the password with bcrypt,
and insert the record into Supabase admins table.
"""

import os
import getpass
import bcrypt
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

def main():
    print("=" * 50)
    print("  SWC Election Platform — Create Admin User")
    print("=" * 50)

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        print("\n❌ ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return

    supabase = create_client(url, key)

    username = input("\nEnter admin username: ").strip()
    if not username:
        print("❌ Username cannot be empty.")
        return

    password = getpass.getpass("Enter admin password (hidden): ").strip()
    if len(password) < 6:
        print("❌ Password must be at least 6 characters.")
        return

    confirm = getpass.getpass("Confirm password: ").strip()
    if password != confirm:
        print("❌ Passwords do not match.")
        return

    # Hash with bcrypt
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    try:
        res = supabase.table("admins").insert({
            "username":      username,
            "password_hash": hashed,
        }).execute()

        if res.data:
            print(f"\n✅ Admin '{username}' created successfully!")
            print("   You can now log in at /admin/login")
        else:
            print("\n❌ Insert returned no data. Check Supabase table permissions.")

    except Exception as e:
        print(f"\n❌ Error creating admin: {e}")
        print("   Make sure the 'admins' table exists (run schema.sql in Supabase first).")

if __name__ == "__main__":
    main()
