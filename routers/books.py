from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models.book_models import Book, BorrowRequest, ReturnRequest, SubscriptionRequest
from services.book_service import add_book, get_books, borrow_book, return_book, delete_book, search_books, subscribe_user
from events.publisher import publish_event
from datetime import datetime
from fastapi.responses import JSONResponse
from config import get_current_user
import logging

router = APIRouter()

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@router.post("/add_book")
async def add_book_route(book: Book, current_user: dict = Depends(get_current_user)):
    contributor = current_user['user_id']
    added_book = add_book(book, contributor)
    await publish_event('BookAdded', {'New Book Added to BookHub': book.book_name})
    logger.info("Published 'BookAdded' event for book: %s", book.book_name)
    return added_book

@router.get("/books")
async def get_books_route(current_user: dict = Depends(get_current_user)):
    return get_books()

@router.post("/borrow")
async def borrow_book_route(request: BorrowRequest, current_user: dict = Depends(get_current_user)):
    user_id = current_user['user_id']
    return borrow_book(request, user_id)

@router.post("/return")
async def return_book_route(request: ReturnRequest, current_user: dict = Depends(get_current_user)):
    return return_book(request)

@router.delete("/delete_book/{book_name}")
async def delete_book_route(book_name: str, current_user: dict = Depends(get_current_user)):
    return delete_book(book_name)

@router.get("/search", response_model=List[Book])
async def search_books_route(book_name: str):
    return search_books(book_name)

# Subscribe to the get notified
@router.post("/subscribe")
async def subscribe(subscription: SubscriptionRequest):
    try:
        response = subscribe_user(subscription.email)
        return {"message": "Subscription successful", "response": response}, 200
    except Exception as e:
        return {"message": f"Subscription failed: {str(e)}"}, 400