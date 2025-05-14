# utils.py
import json
import base64
from typing import List, Dict, Tuple, Optional

from google.genai.types import Part

from schema import Product
from config import settings

def load_products_from_file() -> List:
    """Loads product data from the JSON file specified in settings."""
    try:
        with open(settings.products_file_path, 'r') as f:
            products = json.load(f)
            print(f"INFO: Successfully loaded {len(products)} products from {settings.products_file_path}")
            return products
    except FileNotFoundError:
        print(f"ERROR: Product file not found at {settings.products_file_path}. Returning empty list.")
        return []
    except json.JSONDecodeError:
        print(f"ERROR: Error decoding JSON from {settings.products_file_path}. Returning empty list.")
        return []
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while loading products: {e}")
        return []

def format_products_for_llm(products_db: List, products_sample_size: Optional[int] = None) -> str:
    """
    Formats a sample of products from the database for LLM context.
    If products_sample_size is None, all products are formatted.
    """
    if not products_db:
        return "No product information available."

    sample_products = products_db
    if products_sample_size is not None and products_sample_size < len(products_db):
        sample_products = products_db[:products_sample_size]

    product_texts = []
    for p in sample_products:
        tags_str = ', '.join(p.get('tags',[]))
        product_texts.append(
            f"ID: {p.get('id', 'N/A')}, Name: {p.get('name', 'N/A')}, "
            f"Description: {p.get('description', 'N/A')}, Tags: {tags_str}"
        )
    return "\n".join(product_texts)

def parse_llm_product_ids_and_fetch(
        llm_response_text: str,
        products_db: List
) -> Tuple[List[Product], str]:
    """
    Parses LLM output for product IDs, fetches product details, and generates a status message segment.
    """
    recommended_products_details: List[Product] = []
    status_message_segment = ""

    if not llm_response_text or llm_response_text.upper() == "NOMATCH":
        status_message_segment = " I couldn't find specific products matching that description in our current selection..."
    else:
        recommended_ids = [id_str.strip() for id_str in llm_response_text.split(',') if id_str.strip()]
        if recommended_ids:
            found_details_for_any_id = False
            for prod_id in recommended_ids:
                product_data = next((p for p in products_db if p.get("id") == prod_id), None)
                if product_data:
                    try:
                        recommended_products_details.append(Product(**product_data))
                        found_details_for_any_id = True
                    except Exception as e:
                        print(f"ERROR: Error creating Product object for ID {prod_id}: {e}. Data: {product_data}")

            if recommended_products_details:
                status_message_segment = " here are some recommendations:"
            elif found_details_for_any_id:
                status_message_segment = " I found some potential matches but couldn't fully process their details..."
            else:
                status_message_segment = " I looked for those product IDs but couldn't find them or their details in our records..."
        else:
            status_message_segment = " I wasn't able to pinpoint specific recommendations from the response received..."

    return recommended_products_details, status_message_segment

# def handle_multimodal_data(file_data_model: "FileData") -> Part:
#     """
#     Converts base64 encoded file data to a Google Gemini Part object.
#     """
#     print(f"DEBUG: Handling multimodal data for mime_type: {file_data_model.mime_type}")
#     try:
#         data = base64.b64decode(file_data_model.data)
#         return Part.from_bytes(data=data, mime_type=file_data_model.mime_type)
#     except Exception as e:
#         print(f"ERROR: Unexpected error in handle_multimodal_data: {e}")
#         raise