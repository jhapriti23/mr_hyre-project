"""
MR. HYRE - Database Pre-flight Check & Table Initializer
Author: Human Written & Optimized
"""

import os
import pymysql
from dotenv import load_dotenv
from app import create_app
from app.extensions import db

# .env file load karna
load_dotenv()

def ensure_database_exists():
    """
    Script run hote hi sabse pehle check karegi ki local MySQL instance me 
    mr_hyre naam ka database bana hai ya nahi. Agar nahi hoga, toh create karegi.
    """
    # .env se direct variables pick karna (String split karne ka jhanjhat hi khatam)
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", 3306))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "root@123456789")
    db_name = os.getenv("DB_NAME", "mr_hyre")

    print(f"[!] Target Database Connection Host: {host}:{port}")
    print(f"[!] Attempting root authentication for user: '{user}'")

    # Bina kisi database specification ke baseline MySQL se connect hona
    connection = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        charset="utf8mb4"
    )
    
    try:
        with connection.cursor() as cursor:
            # Safely create database with appropriate professional collations
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
        connection.commit()
        print(f"[+] SUCCESS: Database '{db_name}' verification complete (Ready).")
    except Exception as raw_error:
        print(f"[-] CRITICAL DATABASE ERROR: {raw_error}")
        raise raw_error
    finally:
        connection.close()


if __name__ == "__main__":
    print("=" * 60)
    print("          MR. HYRE DATABASE AUTO-SETUP PIPELINE          ")
    print("=" * 60)
    
    # Step 1: Raw database check
    ensure_database_exists()
    
    # Step 2: Flask App Context call karke models ki saari tables generate karna
    print("[!] Initializing Flask Context for Schema Synchronization...")
    app = create_app(os.environ.get("FLASK_CONFIG", "development"))
    
    with app.app_context():
        try:
            print("[!] Injecting ORM models and establishing tables layout...")
            db.create_all()
            print("[+] SUCCESS: All engine tables and schemas mapped seamlessly!")
            print("=" * 60)
        except Exception as schema_error:
            print(f"[-] SCHEMA GENERATION FAILED: {schema_error}")
            print("=" * 60)