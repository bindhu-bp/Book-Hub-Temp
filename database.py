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
            cursor.execute("CREATE DATABASE IF NOT EXISTS Bookdb")
        
        connection.select_db(DB_CONFIG['database'])
        
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id Varchar(255),
                    name VARCHAR(255),
                    email_id VARCHAR(255) UNIQUE,
                    password VARCHAR(255),
                    role VARCHAR(255)
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
                    collection_id VARCHAR(255) PRIMARY KEY,
                    collection_name VARCHAR(255) NOT NULL UNIQUE,
                    description VARCHAR(255) NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    resource_id VARCHAR(255) PRIMARY KEY,
                    resource_name VARCHAR(255),
                    description VARCHAR(255),
                    link VARCHAR(255),
                    collection_id VARCHAR(255) NOT NULL, 
                    FOREIGN KEY (collection_id) REFERENCES collection(collection_id)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    subscription_id INT AUTO_INCREMENT PRIMARY KEY,
                    email VARCHAR(255) NOT NULL UNIQUE,
                    subscription_arn VARCHAR(255) NOT NULL UNIQUE
                )
            """)
        
        connection.commit()

    except pymysql.MySQLError as e:
        print(f"Error creating database or tables: {e}")
    finally:
        if connection:
            connection.close()

create_database_and_tables()


