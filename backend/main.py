import os
import json
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(dotenv_path='.idea/.env')
gemini_key = os.getenv('GEMINI_API_KEY')
if gemini_key is None:
    print("API key not found. Please check the .env file.")
# --- Gemini Configuration ---
try:
    #client = genai.Client(api_key=gemini_key)
    client = genai.Client(
        api_key=gemini_key,
        http_options=types.HttpOptions(api_version='v1alpha')
    )
    #
    # genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    # gemini_pro_model = genai.GenerativeModel('gemini-pro')
    # gemini_vision_model = genai.GenerativeModel('gemini-pro-vision') # We'll use this later
except Exception as e:
    print(f"Error configuring GenerativeAI: {e}")
app = FastAPI()

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"], # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Data Store & Loading ---
def load_products():
    try:
        with open('products.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

PRODUCTS_DB = load_products()


# --- API Data Models (Pydantic Schemas) ---
class ChatMessage(BaseModel):
    message: str

class TextRecommendQuery(BaseModel):
    query: str

class ProductSchema(BaseModel):
    id: str
    name: str
    description: str
    price: float
    image_url: str
    category: str
    tags: list[str]

    # Example of a Pydantic validator
    # from pydantic import validator
    # @validator('price')
    # def price_must_be_positive(cls, value):
    #     if value <= 0:
    #         raise ValueError('Price must be positive')
    #     return value

class RecommendationResponse(BaseModel):
    recommendations: list[ProductSchema]
    message: str | None = None


# --- API Endpoints ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to the E-Commerce Service API!"}