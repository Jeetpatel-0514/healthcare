import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
api_key = os.environ.get('GEMINI_API_KEY')
print("API KEY:", api_key[:10] if api_key else "None")

try:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents="Hello! Tell me a medical joke.",
        config=types.GenerateContentConfig(
            max_output_tokens=100,
        ),
    )
    print("SUCCESS:", response.text)
except Exception as e:
    print("ERROR:", str(e))
