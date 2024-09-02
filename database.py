# database.py

import pymysql.cursors
from config import DB_CONFIG

def get_db_connection():
    return pymysql.connect(**DB_CONFIG)

def create_database_and_tables():
    connection = None
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS bookhub")
        
        connection.select_db(DB_CONFIG['database'])
        
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(255),
                    email_id VARCHAR(255) UNIQUE,
                    password VARCHAR(255),
                    role VARCHAR(255) DEFAULT 'visitor'
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    book_name VARCHAR(255) NOT NULL,
                    author VARCHAR(255) NOT NULL,
                    total_copies INT DEFAULT 0,
                    available_copies INT DEFAULT 0,
                    borrowers TEXT,
                    contributors TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS collection (
                    collection_name VARCHAR(255)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    collection_name VARCHAR(244),
                    resource_name VARCHAR(244),
                    description VARCHAR(244),
                    link VARCHAR(244)
                )
            """)
        
        connection.commit()

    except pymysql.MySQLError as e:
        print(f"Error creating database or tables: {e}")
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    create_database_and_tables()
