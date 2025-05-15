from pathlib import Path
from typing import List, Dict

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class AppSettings(BaseSettings):
    # Core settings
    gemini_api_key: str

    # File paths
    # products_file_path: Path = PROJECT_ROOT / "products.json"
    products_json_path: Path = PROJECT_ROOT / "productinfo" / "products.json"
    products_image_path: Path = PROJECT_ROOT / "productinfo" / "images"

    # CORS settings
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Application specific settings
    max_history_turns: int = 10
    default_user_profile: Dict[str, str] = {"profile": "valued customer"}

    # Model names
    chat_model_name: str = "gemini-1.5-flash"
    text_recommendation_model_name: str = "gemini-1.5-flash"
    image_description_model_name: str = "gemini-1.5-flash"

    # Prompt Templates
    rufus_persona_template: str = """You are CommerceAgent, a friendly and helpful shopping assistant for an e-commerce website.
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

    text_recommendation_prompt_template: str = """You are a product recommendation engine for an e-commerce site.
User query: "{user_query}"
Available products (summary - use ONLY these for recommendations):
{product_context}

Based *only* on the user query and the provided product list, identify up to 3 relevant product IDs that best match the user's query.
If no products from the list are a good match, respond with "NOMATCH".
Otherwise, return only a comma-separated list of product IDs (e.g., "prod101,prod205").
Do not add any other text or explanation. Your response must be ONLY the IDs or NOMATCH.
"""

    image_to_text_prompt: str = """Describe the main product visible in this image.
Focus on its category, type, color, and key features suitable for an e-commerce search query.
For example: 'red cotton t-shirt for sports' or 'black wireless headphones'.
Provide only the description. Do not add any preamble.
If you cannot identify a product, respond with 'CANNOT IDENTIFY'.
"""

    text_reco_from_image_prompt_template: str = """You are a product recommendation engine.
An AI vision model described the main product in an image as: "{image_description}"
Available products (summary - use ONLY these for recommendations):
{product_context}
Based *only* on the AI's image description and the provided product list, identify up to 3 relevant product IDs.
If no products match, respond with "NOMATCH".
Otherwise, return only a comma-separated list of product IDs (e.g., "prod101,prod205").
No other text or explanation.
"""

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / '.idea' / '.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

settings = AppSettings()

if not settings.gemini_api_key:
    print("CRITICAL: GEMINI_API_KEY not found. Please check your.env file or environment variables.")
    # Consider raising SystemExit here if this is a fatal error for startup