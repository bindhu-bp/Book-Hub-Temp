# main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
from dotenv import load_dotenv
from routers import authentication, books, collections, resources, users
from database import create_database_and_tables
from events.publisher import publish_event


app = FastAPI()

# Mangum handler for AWS Lambda deployment
handler = Mangum(app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # Include OPTIONS method
    allow_headers=["*"],
)

# Include routers
app.include_router(authentication.router)
app.include_router(books.router)
app.include_router(collections.router)
app.include_router(resources.router)
app.include_router(users.router)

# Initialize the database and tables on startup
create_database_and_tables()
