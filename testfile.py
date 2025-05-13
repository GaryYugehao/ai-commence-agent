from google import genai
from google.genai import types
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='.idea/.env')
gemini_key = os.getenv('GEMINI_API_KEY')
if gemini_key is None:
    print("API key not found. Please check the .env file.")

#client = genai.Client(api_key=gemini_key)
client = genai.Client(
    api_key=gemini_key,
    http_options=types.HttpOptions(api_version='v1alpha')
)


response = client.models.generate_content(
    model="gemini-2.0-flash", contents="Explain how AI works in a few words"
)
print(response.text)