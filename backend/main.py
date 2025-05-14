import base64
import os
import json
import uuid

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from google.genai.types import Part
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

class FileData(BaseModel):
    data: str
    mime_type: str

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
@app.get("/", tags=["General"])
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

@app.post("/api/agent/chat", response_model=ChatResponse, tags=["Chat Agent"])
async def chat_with_agent(payload: ChatPayload):
    if payload.session_id not in SESSION_CHATS:
        raise HTTPException(status_code=404, detail="Session not found.")

    chat = SESSION_CHATS[payload.session_id]
    try:
        response = await chat.send_message(payload.message)

        return ChatResponse(message=response.text)
    except Exception as e:
        print(f"Error during chat with Gemini API: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat message: {str(e)}")

def format_products_for_llm(products_sample_size=10):
    if not PRODUCTS_DB:
        return "No product information available."
    sample_products = PRODUCTS_DB[:products_sample_size]
    product_texts = []
    for p in sample_products:
        product_texts.append(f"ID: {p['id']}, Name: {p['name']}, Description: {p['description']}, Tags: {', '.join(p['tags'])}")
    return "\n".join(product_texts)

@app.post("/api/agent/recommend-text", response_model=RecommendationResponse, tags=["Product Recommendations"])
async def recommend_text_products(payload: TextRecommendQuery):
    global TEXT_GEN_MODEL_FULL_NAME
    client = genai.Client(api_key=gemini_key)
    if not client:
        raise HTTPException(status_code=503, detail="Gemini client is not initialized.")

    user_query = payload.query
    product_context = format_products_for_llm(len(PRODUCTS_DB))

    prompt = f"""You are a product recommendation engine for an e-commerce site.
    User query: "{user_query}"
    Available products (summary - use ONLY these for recommendations):
    {product_context}

    Based *only* on the user query and the provided product list, identify up to 3 relevant product IDs that best match the user's query.
    If no products from the list are a good match, respond with "NOMATCH".
    Otherwise, return only a comma-separated list of product IDs (e.g., "prod101,prod205").
    Do not add any other text or explanation. Your response must be ONLY the IDs or NOMATCH.
    """
    try:
        # Get a model instance from the global client for this one-off task
        TEXT_GEN_MODEL_FULL_NAME = "gemini-2.0-flash"
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt]
        )
        llm_response_text = response.text.strip()

        recommended_products_details = []
        rufus_message = f"Rufus: Okay, for your query '{user_query}', I've looked through our products."

        if llm_response_text.upper() == "NOMATCH" or not llm_response_text:
            rufus_message += " I couldn't find specific products matching that description..."
        else:
            recommended_ids = [id_str.strip() for id_str in llm_response_text.split(',') if id_str.strip()]
            if recommended_ids:
                for prod_id in recommended_ids:
                    product_data = next((p for p in PRODUCTS_DB if p.get("id") == prod_id), None)
                    if product_data:
                        recommended_products_details.append(Product(**product_data))
                if recommended_products_details:
                    rufus_message += " Here are some recommendations:"
                else:
                    rufus_message += " I found some potential matches but couldn't retrieve their details..."
            else:
                rufus_message += " I wasn't able to pinpoint specific recommendations..."
        return RecommendationResponse(recommendations=recommended_products_details, message=rufus_message)
    except Exception as e:
        error_message = f"Error during text recommendation with Gemini API ({TEXT_GEN_MODEL_FULL_NAME}): {type(e).__name__} - {e}"
        print(error_message)
        raise HTTPException(status_code=500, detail="Error processing text recommendation. Please check server logs.")

def handle_multimodal_data(file_data: FileData) -> Part:
    """Converts Multimodal data to a Google Gemini Part object.

    Args:
        file_data: FileData object with base64 data and MIME type.

    Returns:
        Part: A Google Gemini Part object containing the file data.
    """
    data = base64.b64decode(file_data.data)  # decode base64 string to bytes
    return Part.from_bytes(data=data, mime_type=file_data.mime_type)

@app.post("/api/agent/recommend-image", response_model=RecommendationResponse, tags=["Product Recommendations"])
async def recommend_image_products(file: UploadFile = File(...)):
    global TEXT_GEN_MODEL_FULL_NAME
    client = genai.Client(api_key=gemini_key)
    try:
        # my_file = client.files.upload(file="path/to/sample.jpg")
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # For client.get_model().generate_content_async(), image parts need to be google.generativeai.types.Part
        image_part = types.Part(inline_data=types.Blob(mime_type=file.content_type, data=contents))

        vision_prompt_text = """Describe the main product visible in this image.
        Focus on its category, type, color, and key features suitable for an e-commerce search query.
        For example: 'red cotton t-shirt for sports' or 'black wireless headphones'.
        Provide only the description. Do not add any preamble.
        If you cannot identify a product, respond with 'CANNOT IDENTIFY'.
        """

        vision_model_payload = [vision_prompt_text, image_part] # List of strings and Parts

        # Get a vision model instance from the global client
        # vision_model = gemini_client.get_model(model_name=VISION_MODEL_FULL_NAME)
        # vision_response = await vision_model.generate_content_async(vision_model_payload)
        # image_description = vision_response.text.strip()

        TEXT_GEN_MODEL_FULL_NAME = "gemini-2.0-flash"
        vision_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=vision_model_payload
        )
        image_description = vision_response.text.strip()

        if not image_description or "CANNOT IDENTIFY" in image_description.upper():
            return RecommendationResponse(
                recommendations=[],
                message="Rufus: I'm sorry, I couldn't clearly identify a product in the image..."
            )

        product_context = format_products_for_llm(len(PRODUCTS_DB))
        text_reco_prompt_from_image = f"""You are a product recommendation engine.
        An AI vision model described the main product in an image as: "{image_description}"
        Available products (summary - use ONLY these for recommendations):
        {product_context}
        Based *only* on the AI's image description and the provided product list, identify up to 3 relevant product IDs.
        If no products match, respond with "NOMATCH".
        Otherwise, return only a comma-separated list of product IDs (e.g., "prod101,prod205").
        No other text or explanation.
        """

        text_reco_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[text_reco_prompt_from_image]
        )
        llm_response_text = text_reco_response.text.strip()

        recommended_products_details = []
        rufus_message = f"Rufus: Based on the image (which I see as about '{image_description}'), "

        if llm_response_text.upper() == "NOMATCH" or not llm_response_text:
            rufus_message += "I couldn't find matching products in our current selection..."
        else:
            recommended_ids = [id_str.strip() for id_str in llm_response_text.split(',') if id_str.strip()]
            if recommended_ids:
                for prod_id in recommended_ids:
                    product_data = next((p for p in PRODUCTS_DB if p.get("id") == prod_id), None)
                    if product_data:
                        recommended_products_details.append(Product(**product_data))
                if recommended_products_details:
                    rufus_message += "here are some recommendations:"
                else:
                    rufus_message += "I found some potential matches but couldn't retrieve their full details..."
            else:
                rufus_message += "I wasn't able to pinpoint specific recommendations..."
        return RecommendationResponse(recommendations=recommended_products_details, message=rufus_message)
    except HTTPException:
        raise
    except Exception as e:
        error_message = f"Error during image recommendation: {type(e).__name__} - {e}"
        print(error_message)
        # Add more specific error checks if known for genai.Client API
        if "PermissionDenied" in str(e) or "API key" in str(e): # Example
            raise HTTPException(status_code=403, detail="Rufus: There seems to be an issue with API access.")
        raise HTTPException(status_code=500, detail="Rufus: Sorry, I encountered an error processing the image recommendation.")
