from pydantic import BaseModel

# class Book(BaseModel):
#     book_name: str
#     author: str
#     contributors: str
#     copies: int

class Book(BaseModel):
    book_name: str
    author: str
    copies: int

class BorrowRequest(BaseModel):
    book_name: str

class ReturnRequest(BaseModel):
    book_name: str
    borrower: str

class SubscriptionRequest(BaseModel):
    email: str