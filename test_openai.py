import os
from dotenv import load_dotenv
import openai

load_dotenv()
api_key = os.environ.get('OPENAI_API_KEY')
print("API KEY:", api_key[:10] if api_key else "None")

try:
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ],
        max_tokens=10
    )
    print("SUCCESS:", response.choices[0].message.content)
except Exception as e:
    print("ERROR:", str(e))
