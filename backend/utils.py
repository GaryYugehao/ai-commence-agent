import json
from typing import List, Dict, Tuple, Optional
from pathlib import Path

from fastapi import UploadFile, HTTPException
from google import genai
from google.genai import types as genai_types
from pydantic import ValidationError
from schema import Product

def load_products_from_file(file_path: Path) -> List:
    """Loads product data from the JSON file specified in settings."""
    try:
        with open(file_path, 'r') as f:
            products = json.load(f)
            print(f"INFO: Successfully loaded {len(products)} products from {file_path}")
            return products
    except FileNotFoundError:
        print(f"ERROR: Product file not found at {file_path}. Returning empty list.")
        return []
    except json.JSONDecodeError:
        print(f"ERROR: Error decoding JSON from {file_path}. Returning empty list.")
        return []
    except Exception as e:
        print(f"ERROR: An unexpected error occurred while loading products: {e}")
        return []

def format_products_for_llm(products_db: List[Dict]) -> str:
    """
    Formats all products from the database for LLM context.
    """
    if not products_db:
        return "No product information available."

    product_texts = []
    for p in products_db:
        tags_str = ', '.join(p.get('tags', []))
        product_texts.append(
            f"ID: {p.get('id', 'N/A')}, Name: {p.get('name', 'N/A')}, "
            f"Description: {p.get('description', 'N/A')}, Tags: {tags_str}"
        )
    return "\n".join(product_texts)

def parse_llm_product_ids_and_fetch(
        llm_response_text: str,
        products_db: List[Dict]
) -> Tuple[List[Product], str]:
    """
    Parses LLM output for product IDs, fetches product details from products_db,
    and generates a corresponding status message segment.

    Args:
        llm_response_text: The text response from the LLM, expected to be
                           comma-separated product IDs or "NOMATCH".
        products_db: A list of dictionaries, where each dictionary represents a product
                     and contains at least an "id" key.

    Returns:
        A tuple containing:
            - A list of successfully parsed and fetched Product objects.
            - A string message segment indicating the outcome.
    """
    if not llm_response_text or llm_response_text.strip().upper() == "NOMATCH":
        return [], " I couldn't find specific products matching that description in our current selection..."

    raw_ids = llm_response_text.split(',')
    recommended_ids = [id_str.strip() for id_str in raw_ids if id_str.strip()]

    if not recommended_ids:
        return [], " I wasn't able to pinpoint specific recommendations from the response received..."

    # products_map = {p.get("id"): p for p in products_db if p.get("id")}
    # used only for giant product_db

    recommended_products_details: List[Product] = []
    found_product_data_for_any_id = False

    for prod_id in recommended_ids:
        # used only for giant product_db
        # product_data = products_map.get(prod_id)
        product_data = next((p for p in products_db if p.get("id") == prod_id), None)

        if product_data:
            found_product_data_for_any_id = True
            try:
                recommended_products_details.append(Product(**product_data))
            except ValidationError as ve:
                print(f"ERROR: Validation error creating Product object for ID {prod_id}: {ve}. Data: {product_data}")
            except Exception as e:
                print(f"ERROR: Unexpected error creating Product object for ID {prod_id}: {e}. Data: {product_data}")
        else:
            print(f"INFO: Product ID '{prod_id}' recommended by LLM but not found in products_db.")

    if recommended_products_details:
        status_message_segment = " here are some recommendations:"
    elif found_product_data_for_any_id:
        status_message_segment = " I found some potential matches but couldn't fully process their details..."
    else:
        status_message_segment = " I looked for those product IDs but couldn't find them in our records..."

    return recommended_products_details, status_message_segment

async def _get_recommendations_from_llm(
        prompt: str,
        model_name: str,
        gemini_client: genai.Client,
        products_db: List[Dict]
) -> (List[Product], str):
    """Sends a prompt to a Gemini model and processes the response for product recommendations.

    Args:
        prompt: Text prompt for the language model.
        model_name: Name of the Gemini model to use.
        gemini_client: Initialized Gemini API client.
        products_db: List of product dictionaries for detail fetching.

    Returns:
        A tuple containing a list of `Product` objects and a message segment string,
        or `None` if an error occurs during the LLM call.
    """
    try:
        response = gemini_client.models.generate_content(
            model=model_name,
            contents=[prompt]
        )
        llm_response_text = response.text.strip()
        print(f"INFO: LLM response for model {model_name}: '{llm_response_text}'")
        return parse_llm_product_ids_and_fetch(llm_response_text, products_db)
    except Exception as e:
        print(f"ERROR: Error during LLM call with model {model_name}: {e}")
        raise


async def _get_image_description_from_llm(
        file: UploadFile,
        gemini_client: genai.Client,
        prompt_template: str,
        model_name: str
) -> Optional[str]:
    """Reads an image file and gets its description from a Gemini vision model.

    Args:
        file: Uploaded image file.
        gemini_client: Initialized Gemini API client.
        prompt_template: Text prompt for the vision model.
        model_name: Name of the Gemini vision model.

    Returns:
        The image description string if successful.
        Returns `None` if the file is empty, image cannot be identified,
        a permission/API key error occurs, or any other error during processing.
    """
    contents = await file.read()
    if not contents:
        print(f"WARNING: Uploaded file {file.filename} is empty.")
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        image_part = genai_types.Part(inline_data=genai_types.Blob(mime_type=file.content_type, data=contents))
        vision_model_payload = [prompt_template, image_part]
        print(f"DEBUG: Sending image to vision model ({model_name}) for description...")

        vision_response = gemini_client.models.generate_content(
            model=model_name,
            contents=[vision_model_payload]
        )
        image_description = vision_response.text.strip()
        print(f"INFO: Vision model image description: '{image_description}'")

        if not image_description or "CANNOT IDENTIFY" in image_description.upper():
            print(f"INFO: Vision model could not identify a product in the image or returned an empty description.")
            return None

        return image_description
    except Exception as e:
        if "PermissionDenied" in str(e) or "API key" in str(e):
            print(f"ERROR: Gemini API permission or key error during image description: {e}")
            raise HTTPException(status_code=403, detail="Rufus: There seems to be an issue with API access for image processing.")
        print(f"ERROR: Error during image description with model {model_name}: {e}")
        raise