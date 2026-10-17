from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from .api.api import api_router

import os

load_dotenv()
app = FastAPI(title="iLovePDF Tools API", version="1.0.0")

# Configure CORS for frontend access
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:3001",
]
frontend_url = os.getenv("FRONTEND_URL")
if frontend_url:
    origins.extend([url.strip() for url in frontend_url.split(",") if url.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the PDF Tools API"}
