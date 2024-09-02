from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import pymysql.cursors
from database import get_db_connection
from models import Book
from events.publisher import publish_event
import json
from models import BorrowRequest, ReturnRequest, UploadPayload
from datetime import datetime
from fastapi.responses import JSONResponse
from config import get_current_user

router = APIRouter()

# Add a book
@router.post("/add_book")
async def add_book(book: Book):
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT * FROM books WHERE book_name = %s AND author = %s", (book.book_name, book.author))
        existing_book = cursor.fetchone()

        if existing_book:
            new_total_copies = existing_book['total_copies'] + book.copies
            new_available_copies = existing_book['available_copies'] + book.copies
            existing_contributors = set(name.strip() for name in existing_book['contributors'].split(',') if name.strip())
            if book.contributors not in existing_contributors:
                existing_contributors.add(book.contributors)
            new_contributors = ', '.join(sorted(existing_contributors))

            cursor.execute("""
                UPDATE books
                SET total_copies = %s, available_copies = %s, contributors = %s
                WHERE book_name = %s AND author = %s
            """, (new_total_copies, new_available_copies, new_contributors, book.book_name, book.author))
        else:
            cursor.execute("""
                INSERT INTO books (book_name, author, total_copies, available_copies, contributors)
                VALUES (%s, %s, %s, %s, %s)
            """, (book.book_name, book.author, book.copies, book.copies, book.contributors))

        conn.commit()
    conn.close()
    return {"message": "Book added or updated successfully"}

# List all books
@router.get("/books")
async def get_books():
    
    connection = get_db_connection()
  
    with connection.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute("SELECT * FROM books")
        result = cursor.fetchall()
        for book in result:
            book['borrowers'] = json.loads(book['borrowers']) if book['borrowers'] else []
    connection.close()
    return result

# Borrow a book
@router.post("/borrow")
async def borrow_book(request: BorrowRequest):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT available_copies, borrowers FROM books WHERE book_name = %s", (request.book_name,))
    book = cursor.fetchone()

    if not book:
        cursor.close()
        connection.close()
        return {"detail": "Book not found"}

    available_copies, borrowers_json = book['available_copies'], book['borrowers']
    current_borrowers = json.loads(borrowers_json) if borrowers_json else []
    
    # Check if the user has already borrowed the book
    if any(borrower['name'] == request.borrower for borrower in current_borrowers):
        cursor.close()
        connection.close()
        return {"detail": "User has already borrowed this book"}
    
    if available_copies <= 0:
        cursor.close()
        connection.close()
        return {"detail": "No copies available"}

    # Add the new borrower with the current date
    borrow_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    current_borrowers.append({"name": request.borrower, "borrow_date": borrow_date})
    
    cursor.execute("UPDATE books SET available_copies = %s, borrowers = %s WHERE book_name = %s",
                   (available_copies - 1, json.dumps(current_borrowers), request.book_name))
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Book borrowed successfully", "borrowers": current_borrowers}

# Return a book
@router.post("/return")
async def return_book(request: ReturnRequest):
    connection = get_db_connection()
    cursor = connection.cursor()
    
    cursor.execute("SELECT available_copies, borrowers FROM books WHERE book_name = %s", (request.book_name,))
    book = cursor.fetchone()
    
    if not book:
        cursor.close()
        connection.close()
        return {"detail": "Book not found"}

    available_copies, borrowers_json = book['available_copies'], book['borrowers']
    current_borrowers = json.loads(borrowers_json) if borrowers_json else []
    
    # Find the borrower
    borrower_to_remove = next((borrower for borrower in current_borrowers if borrower['name'] == request.borrower), None)
    
    if not borrower_to_remove:
        cursor.close()
        connection.close()
        return {"detail": "User did not borrow this book"}

    # Remove the borrower from the list
    current_borrowers.remove(borrower_to_remove)
    
    cursor.execute("UPDATE books SET available_copies = %s, borrowers = %s WHERE book_name = %s",
                   (available_copies + 1, json.dumps(current_borrowers), request.book_name))
    connection.commit()
    cursor.close()
    connection.close()
    return {"message": "Book returned successfully"}



@router.delete("/delete_book/{book_name}")
async def delete_book(book_name: str):
    connection = get_db_connection()
    if not connection:
        return {"statusCode": 500, "message": "Database connection error"}

    try:
        with connection.cursor() as cursor:
            # Check if the book exists and if the available_copies are >= 1
            cursor.execute("""
                SELECT available_copies, total_copies
                FROM books
                WHERE book_name = %s
            """, (book_name,))
            book = cursor.fetchone()

            if book is None:
                return {"statusCode": 404, "message": "Book not found"}

            if book['available_copies'] < 1:
                return {"statusCode": 400, "message": "Cannot delete a copy of a book with no available copies"}

            # Decrement both total_copies and available_copies by 1
            cursor.execute("""
                UPDATE books
                SET available_copies = available_copies - 1,
                    total_copies = total_copies - 1
                WHERE book_name = %s
            """, (book_name,))
            connection.commit()

            if cursor.rowcount == 0:
                return {"statusCode": 404, "message": "Book not found after update attempt"}

        return {"statusCode": 200, "message": "One copy of the book deleted successfully from both total and available copies"}
    except Exception as e:
        return {"statusCode": 500, "message": f"Internal server error: {str(e)}"}
    finally:
        connection.close()



# Search for books
@router.get("/search", response_model=List[Book])
async def search_books(book_name: str):
    connection = get_db_connection()
    if not connection:
        return {"statusCode": 500, "message": "Database connection error"}
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT book_name, author FROM books WHERE book_name LIKE %s", (book_name + '%',))
            result = cursor.fetchall()
        return result
    finally:
        connection.close()

# Upload a PDF
@router.post("/upload")
async def upload_pdf(uploadPayload:UploadPayload,current_user: dict = Depends(get_current_user)):
    

    # Update the database
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "INSERT INTO uploaded (user_id, filename, created_at) VALUES (%s, %s, %s)"
            cursor.execute(sql, (uploadPayload.user_id, uploadPayload.filename, datetime.now()))
        connection.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        connection.close()
    
    return JSONResponse(status_code=200, content={"message": "File uploaded successfully", "filename": uploadPayload.filename})

# Delete a PDF
@router.delete("/delete")
async def delete_pdf(payload: UploadPayload,current_user: dict = Depends(get_current_user)):
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            sql = "DELETE FROM uploaded WHERE user_id = %s AND filename = %s"
            cursor.execute(sql, (payload.user_id, payload.filename))
        connection.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        connection.close()
   
    return JSONResponse(status_code=200, content={"message": "File deleted successfully"})