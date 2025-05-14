import uuid
from contextlib import asynccontextmanager
from typing import List, Dict # Added Dict

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types as genai_types

from config import settings
from schema import (
    Product, StartSessionPayload, StartSessionResponse,
    ChatPayload, ChatResponse, TextRecommendQuery, RecommendationResponse
)
from utils import (
    load_products_from_file, format_products_for_llm,
    parse_llm_product_ids_and_fetch
)

# --- Application Lifecycle (Lifespan Events) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("INFO: Application startup sequence initiated...")

    print("INFO: Initializing Gemini client...")
    try:
        app.state.gemini_client = genai.Client(api_key=settings.gemini_api_key)
        print("INFO: Successfully initialized Gemini client.")
    except Exception as e:
        print(f"CRITICAL: Failed to initialize Gemini client: {e}")
        raise RuntimeError(f"Failed to initialize Gemini client: {e}") from e

    print("INFO: Loading product database...")
    app.state.products_db = load_products_from_file()
    print(f"INFO: Loaded {len(app.state.products_db)} products into app state.")

    app.state.session_chats = {} # Initialize in-memory session chat store
    print("INFO: In-memory session chat store initialized.")

    print("INFO: Application startup complete.")
    yield
    # Shutdown
    print("INFO: Application shutdown sequence initiated...")
    if hasattr(app.state, 'products_db'):
        app.state.products_db.clear()
        print("INFO: Product database cleared from app state.")
    if hasattr(app.state, 'session_chats'):
        app.state.session_chats.clear()
        print("INFO: Session chat store cleared from app state.")
    print("INFO: Application shutdown complete.")


app = FastAPI(
    title="E-Commerce AI Agent API",
    description="API for Rufus, the AI-powered e-commerce assistant.",
    version="1.0.0",
    lifespan=lifespan
)

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependencies ---
def get_gemini_client(request: Request) -> genai.Client:
    if not hasattr(request.app.state, 'gemini_client') or request.app.state.gemini_client is None:
        print("ERROR: Gemini client not available in app.state.")
        raise HTTPException(status_code=503, detail="Gemini service is temporarily unavailable.")
    return request.app.state.gemini_client

def get_products_db(request: Request) -> List[Dict]:
    if not hasattr(request.app.state, 'products_db'):
        print("ERROR: Products DB not available in app.state.")
        raise HTTPException(status_code=503, detail="Product information is temporarily unavailable.")
    return request.app.state.products_db

def get_session_chats(request: Request) -> Dict:
    if not hasattr(request.app.state, 'session_chats'):
        print("ERROR: Session chats not available in app.state.")
        raise HTTPException(status_code=503, detail="Session manager is temporarily unavailable.")
    return request.app.state.session_chats


# --- API Endpoints ---
@app.get("/")
async def read_root():
    """Returns a welcome message for the API."""
    return {"message": "Welcome to the E-Commerce Service API with Rufus!"}

@app.post("/api/agent/start_session", response_model=StartSessionResponse)
async def start_session(
        payload: StartSessionPayload,
        gemini_client: genai.Client = Depends(get_gemini_client),
        session_chats: Dict = Depends(get_session_chats)
):
    """
    Starts a new chat session with Rufus.
    Returns a session ID and Rufus's initial greeting.
    """
    print("--- Attempting to start session ---")
    session_id = str(uuid.uuid4())
    user_profile = payload.user_info if payload.user_info is not None else settings.default_user_profile
    user_profile_str = ", ".join(f"{k}: {v}" for k, v in user_profile.items())

    initial_system_prompt_content = settings.rufus_persona_template.format(
        user_profile_details=user_profile_str
    )
    print(f"DEBUG: Starting session {session_id} for user profile: {user_profile_str}")

    try:
        chat = gemini_client.aio.chats.create(model=settings.chat_model_name)

        response = await chat.send_message(initial_system_prompt_content)
        rufus_greeting = response.text

        session_chats[session_id] = chat
        print(f"INFO: Session {session_id} started. Rufus greeting: '{rufus_greeting[:50]}...'")
        return StartSessionResponse(session_id=session_id, initial_message=rufus_greeting)
    except Exception as e:
        print(f"ERROR: Error during chat session start with Gemini API ({settings.chat_model_name}): {e}")
        raise HTTPException(status_code=500, detail=f"Error starting chat session. Please contact support.")


@app.post("/api/agent/chat", response_model=ChatResponse)
async def chat_with_agent(
        payload: ChatPayload,
        session_chats: Dict = Depends(get_session_chats)
):
    """Handles an ongoing chat message within an existing session."""
    chat_session = session_chats.get(payload.session_id)
    if not chat_session:
        print(f"WARNING: Chat session not found: {payload.session_id}")
        raise HTTPException(status_code=404, detail="Session not found. Please start a new session.")

    print(f"DEBUG: Received message for session {payload.session_id}: '{payload.message[:50]}...'")
    try:
        response = await chat_session.send_message(payload.message)
        print(f"INFO: Response sent for session {payload.session_id}. Response: '{response.text[:50]}...'")
        return ChatResponse(message=response.text)
    except Exception as e:
        print(f"ERROR: Error during chat with Gemini API for session {payload.session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing chat message. Please try again.")


@app.post("/api/agent/recommend-text", response_model=RecommendationResponse)
async def recommend_text_products(
        payload: TextRecommendQuery,
        gemini_client: genai.Client = Depends(get_gemini_client),
        products_db: List = Depends(get_products_db)
):
    """Recommends products based on a textual query."""
    user_query = payload.query
    print(f"INFO: Received text recommendation query: '{user_query}'")

    if not products_db:
        print("WARNING: Product database is empty. Cannot provide text recommendations.")
        return RecommendationResponse(
            recommendations=[],
            message="Rufus: I'm sorry, but our product catalog seems to be empty at the moment."
        )

    product_context = format_products_for_llm(products_db, products_sample_size=len(products_db))

    prompt = settings.text_recommendation_prompt_template.format(
        user_query=user_query,
        product_context=product_context
    )
    print(f"DEBUG: Text recommendation prompt (first 100 chars): {prompt[:100]}...")

    try:
        response = gemini_client.models.generate_content(
            model=settings.text_recommendation_model_name,
            contents=[prompt]
        )
        #response = await model.generate_content(contents=[prompt])
        llm_response_text = response.text.strip()
        print(f"INFO: LLM response for text recommendation: '{llm_response_text}'")

        recommended_products_details, message_segment = parse_llm_product_ids_and_fetch(llm_response_text, products_db)

        rufus_message = f"Rufus: Okay, for your query '{user_query}', I've looked through our products." + message_segment
        print(f"INFO: Final Rufus message for text recommendation: {rufus_message}")
        return RecommendationResponse(recommendations=recommended_products_details, message=rufus_message)

    except Exception as e:
        print(f"ERROR: Error during text recommendation with Gemini API ({settings.text_recommendation_model_name}): {e}")
        raise HTTPException(status_code=500, detail="Error processing text recommendation. Please check server logs.")


@app.post("/api/agent/recommend-image", response_model=RecommendationResponse)
async def recommend_image_products(
        file: UploadFile = File(...),
        gemini_client: genai.Client = Depends(get_gemini_client),
        products_db: List = Depends(get_products_db)
):
    """Recommends products based on an uploaded image."""
    print(f"INFO: Received image recommendation request for file: {file.filename} (type: {file.content_type})")

    if not products_db:
        print("WARNING: Product database is empty. Cannot provide image-based recommendations.")
        return RecommendationResponse(
            recommendations=[],
            message="Rufus: I'm sorry, but our product catalog seems to be empty at the moment."
        )

    try:
        contents = await file.read()
        if not contents:
            print(f"WARNING: Uploaded file {file.filename} is empty.")
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        image_part = genai_types.Part(inline_data=genai_types.Blob(mime_type=file.content_type, data=contents))

        vision_model_payload = [settings.image_to_text_prompt, image_part]
        print("DEBUG: Sending image to vision model for description...")

        vision_response = gemini_client.models.generate_content(
            model=settings.image_description_model_name,
            contents=[vision_model_payload]
        )

        image_description = vision_response.text.strip()
        print(f"INFO: Vision model image description: '{image_description}'")

        if not image_description or "CANNOT IDENTIFY" in image_description.upper():
            message = "Rufus: I'm sorry, I couldn't clearly identify a product in the image you sent."
            print(f"INFO: {message}")
            return RecommendationResponse(recommendations=[], message=message)

        product_context = format_products_for_llm(products_db, products_sample_size=len(products_db))
        text_reco_prompt_from_image = settings.text_reco_from_image_prompt_template.format(
            image_description=image_description,
            product_context=product_context
        )
        print(f"DEBUG: Text recommendation from image prompt (first 100 chars): {text_reco_prompt_from_image[:100]}...")

        text_reco_response = gemini_client.models.generate_content(
            model=settings.text_recommendation_model_name,
            contents=[text_reco_prompt_from_image]
        )

        llm_response_text = text_reco_response.text.strip()
        print(f"INFO: LLM response for image-based text recommendation: '{llm_response_text}'")

        recommended_products_details, message_segment = parse_llm_product_ids_and_fetch(llm_response_text, products_db)

        rufus_message = f"Rufus: Based on the image (which I see as about '{image_description}')," + message_segment
        print(f"INFO: Final Rufus message for image recommendation: {rufus_message}")
        return RecommendationResponse(recommendations=recommended_products_details, message=rufus_message)

    except HTTPException:
        raise
    except Exception as e:
        if "PermissionDenied" in str(e) or "API key" in str(e):
            print(f"ERROR: Gemini API permission or key error during image recommendation: {e}")
            raise HTTPException(status_code=403, detail="Rufus: There seems to be an issue with API access for image processing.")

        print(f"ERROR: Error during image recommendation (model: {settings.image_description_model_name} / {settings.text_recommendation_model_name}): {e}")
        raise HTTPException(status_code=500, detail="Rufus: Sorry, I encountered an error processing the image recommendation.")