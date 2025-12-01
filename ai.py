import os
from google import genai

gemini_api_key = lambda: os.getenv("GEMINI_API_KEY")

class RetardedClient:
    def generate_content(self):
        return type("Response", (), {"text": "hey, it's alsugo talking. please set a valid google api key "})

try:
    client = genai.Client(api_key=gemini_api_key())
except:
    client = RetardedClient()

def client_unretarder(client):
    if isinstance(client, RetardedClient):
        try:
            client = genai.Client(api_key=gemini_api_key())
        except:
            raise ValueError("please set a valid GEMINI_API_KEY in your env")

def gemini_query(prompt: str) -> str:
    client_unretarder(client)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text
