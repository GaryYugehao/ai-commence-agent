import os
import json
import uuid

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing import Optional
from pathlib import Path

current_script_dir = Path(__file__).resolve().parent
dotenv_path = current_script_dir.parent / '.idea' / '.env'

load_dotenv(dotenv_path=dotenv_path)
gemini_key = os.getenv('GEMINI_API_KEY')
if gemini_key is None:
    print("API key not found. Please check the .env file.")

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
SESSION_CHATS = {}
MAX_HISTORY_TURNS = 10


# --- API Data Models (Pydantic Schemas) ---
class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    image_url: str
    category: str
    tags: list[str]

class StartSessionPayload(BaseModel):
    user_info: Optional[dict[str, str]] = {"profile": "valued customer"}

class StartSessionResponse(BaseModel):
    session_id: str
    initial_message: str

class ChatPayload(BaseModel):
    message: str
    session_id: str

class ChatResponse(BaseModel):
    message: str

class TextRecommendQuery(BaseModel):
    query: str

class RecommendationResponse(BaseModel):
    recommendations: list[Product]
    message: Optional[str] = None

RUFUS_BASE_PERSONA_PROMPT_TEMPLATE = """You are CommerceAgent, a friendly and helpful shopping assistant for an e-commerce website.
Your name is Rufus.
You are currently assisting a user with the following profile: {user_profile_details}.

Your primary functions are:
1.  General Conversation: Engage in friendly chat and answer general inquiries based on the product descriptions.
2.  Text-Based Product Recommendations: Help users find products from the product database based on their textual descriptions.
3.  Image-Based Product Search: Help users find products from the product database similar to an image they provide.

When a user asks what you can do, clearly state these three capabilities.
Always respond conversationally.
Maintain context from previous messages.
Start the conversation by introducing yourself and asking how I (the user) can be helped. This should be your very first response.
"""

# --- API Endpoints ---
@app.get("/")
async def read_root():
    return {"message": "Welcome to the E-Commerce Service API!"}

@app.post("/api/agent/start_session", response_model=StartSessionResponse, tags=["Chat Agent"])
async def start_session(payload: StartSessionPayload):
    """
    Starts a new chat session with Rufus and returns a session ID and Rufus's initial greeting.
    The persona and user information are instilled at this stage.
    """
    try:
        client = genai.Client(api_key=gemini_key)
        #chat = client.aio.chats.create(model='gemini-2.0-flash')
        #response = await chat.send_message('tell me a story')
    except Exception as e:
        print(f"Error configuring GenerativeAI: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting chat session: {str(e)}")

    session_id = str(uuid.uuid4())
    user_profile_str = ", ".join(f"{k}: {v}" for k, v in payload.user_info.items()) if payload.user_info else "not specified"

    initial_system_prompt_content = RUFUS_BASE_PERSONA_PROMPT_TEMPLATE.format(
        user_profile_details=user_profile_str
    )

    try:
        chat = client.aio.chats.create(model='gemini-1.5-flash')

        response = await chat.send_message(initial_system_prompt_content)

        rufus_greeting = response.text

        SESSION_CHATS[session_id] = chat
        return StartSessionResponse(session_id=session_id, initial_message=rufus_greeting)
    except Exception as e:
        print(f"Error during chat session start with Gemini API: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting chat session: {str(e)}")