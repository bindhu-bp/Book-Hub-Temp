import pymysql
from database import get_db_connection
from models.book_models import Book, BorrowRequest, ReturnRequest
from datetime import datetime
import json, os, boto3
from fastapi import HTTPException
import uuid
from typing import Dict
import logging

# Initialize AWS clients
sns_client = boto3.client('sns')

# Fetch the SNS Topic ARN and Event Bus Name from environment variables
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')

def add_book(book: Book, contributor: str):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM books WHERE book_name = %s AND author = %s", (book.book_name, book.author))
            existing_book = cursor.fetchone()

            if existing_book:
                # Update total and available copies
                new_total_copies = existing_book['total_copies'] + book.copies
                new_available_copies = existing_book['available_copies'] + book.copies
                
                # Update contributors list
                existing_contributors = set(name.strip() for name in existing_book['contributor'].split(',') if name.strip())
                existing_contributors.add(contributor.strip())  
                
                new_contributors = ', '.join(sorted(existing_contributors))  
                
                # Update the database record
                cursor.execute("""
                    UPDATE books
                    SET total_copies = %s, available_copies = %s, contributor = %s
                    WHERE book_name = %s AND author = %s
                """, (new_total_copies, new_available_copies, new_contributors, book.book_name, book.author))
            else:
                # Insert new record for a book that doesn't exist yet
                cursor.execute("""
                    INSERT INTO books (book_name, author, total_copies, available_copies, contributor)
                    VALUES (%s, %s, %s, %s, %s)
                """, (book.book_name, book.author, book.copies, book.copies, contributor))

            connection.commit()
            return {"message": "Book added or updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding/updating book: {str(e)}")
    finally:
        connection.close()

def get_books():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT book_name, author, total_copies, available_copies, contributor, borrowers FROM books")
            result = cursor.fetchall() 
            
            for book in result:
                book['borrowers'] = json.loads(book['borrowers']) if 'borrowers' in book and book['borrowers'] else []
                
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving books: {str(e)}")
    finally:
        connection.close()

def return_book(request: ReturnRequest):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT available_copies, borrowers FROM books WHERE book_name = %s", (request.book_name,))
            book = cursor.fetchone()
            if not book:
                raise HTTPException(status_code=404, detail="Book not found")

            available_copies, borrowers_json = book['available_copies'], book['borrowers']
            current_borrowers = json.loads(borrowers_json) if borrowers_json else []

            borrower_to_remove = next((borrower for borrower in current_borrowers if borrower['name'] == request.borrower), None)
            if not borrower_to_remove:
                raise HTTPException(status_code=400, detail="User did not borrow this book")

            current_borrowers.remove(borrower_to_remove)
            cursor.execute("UPDATE books SET available_copies = %s, borrowers = %s WHERE book_name = %s",
                           (available_copies + 1, json.dumps(current_borrowers), request.book_name))
            connection.commit()
            return {"message": "Book returned successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error returning book: {str(e)}")
    finally:
        connection.close()

def delete_book(book_name: str):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT available_copies, total_copies FROM books WHERE book_name = %s", (book_name,))
            book = cursor.fetchone()
            if book is None:
                raise HTTPException(status_code=404, detail="Book not found")
            if book['available_copies'] < 1:
                raise HTTPException(status_code=400, detail="Cannot delete a copy of a book with no available copies")

            cursor.execute("UPDATE books SET available_copies = available_copies - 1, total_copies = total_copies - 1 WHERE book_name = %s", (book_name,))
            connection.commit()

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Book not found after update attempt")
            if book['total_copies'] == 1:
                cursor.execute("DELETE FROM books WHERE book_name = %s", (book_name,))
                connection.commit()
                return {"statusCode": 200, "message": "Book deleted successfully as total copies reached zero"}
            return {"statusCode": 200, "message": "One copy of the book deleted successfully from both total and available copies"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting book: {str(e)}")
    finally:
        connection.close()

def search_books(book_name: str):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT book_name, author FROM books WHERE book_name LIKE %s", (book_name + '%',))
            result = cursor.fetchall()
            return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching books: {str(e)}")
    finally:
        connection.close()


def subscribe_user(email):
    """Subscribes a user to the SNS topic."""
    if not SNS_TOPIC_ARN:
        return {"message": "SNS_TOPIC_ARN environment variable is not set"}, 500
    
    response = sns_client.subscribe(
        TopicArn=SNS_TOPIC_ARN,
        Protocol='email',
        Endpoint=email
    )
    return response


def borrow_book(request: BorrowRequest, user_id: str):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT available_copies, borrowers FROM books WHERE book_name = %s", (request.book_name,))
            book = cursor.fetchone()

            if not book:
                raise HTTPException(status_code=404, detail="Book not found")

            available_copies, borrowers_json = book['available_copies'], book['borrowers']
            current_borrowers = json.loads(borrowers_json) if borrowers_json else []

            if any(borrower['user_id'] == user_id for borrower in current_borrowers):
                raise HTTPException(status_code=400, detail="User has already borrowed this book")

            if available_copies <= 0:
                raise HTTPException(status_code=400, detail="No copies available")

            borrow_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            current_borrowers.append({"user_id": user_id, "borrow_date": borrow_date})

            cursor.execute("SELECT name FROM users WHERE user_id = %s", (user_id,))
            borrower = cursor.fetchone()

            if not borrower:
                raise HTTPException(status_code=404, detail="Borrower not found")

            borrower_name = borrower['name']

            
            cursor.execute("UPDATE books SET available_copies = %s, borrowers = %s WHERE book_name = %s",
                           (available_copies - 1, json.dumps(current_borrowers), request.book_name))
            connection.commit()

            return {"message": "Book borrowed successfully", "borrower": {"user_id": user_id, "name": borrower_name, "borrow_date": borrow_date}}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error borrowing book: {str(e)}")
    finally:
        connection.close()




