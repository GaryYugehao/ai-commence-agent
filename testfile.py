from google import genai
from google.genai import types
import os
from dotenv import load_dotenv
import asyncio

load_dotenv(dotenv_path='.idea/.env')
gemini_key = os.getenv('GEMINI_API_KEY')
if gemini_key is None:
    print("API key not found. Please check the .env file.")

#client = genai.Client(api_key=gemini_key)
# client = genai.Client(
#     api_key=gemini_key,
#     http_options=types.HttpOptions(api_version='v1alpha')
# )

async def handle_chat():
    client = genai.Client(api_key=gemini_key)
    # chat = client.chats.create(model="gemini-2.0-flash")
    chat = client.aio.chats.create(model='gemini-2.0-flash')

    response = await chat.send_message("I have 2 dogs in my house.")
    print(response.text)

    response = await chat.send_message("How many paws are in my house?")
    print(response.text)

    for message in chat.get_history():
        print(f'role - {message.role}',end=": ")
        print(message.parts[0].text)

loop = asyncio.get_event_loop()
loop.run_until_complete(handle_chat())

# response = client.models.generate_content(
#     model="gemini-2.0-flash", contents="Explain how AI works in a few words"
# )
# print(response.text)