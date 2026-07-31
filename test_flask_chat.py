import sys
from app import app

client = app.test_client()
response = client.post('/api/chat', json={'message': 'hello'})
print(response.status_code)
print(response.data)
