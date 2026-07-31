import requests, sys
try:
    r = requests.get('http://localhost:3000/api/me', timeout=5)
    print(r.status_code)
    print(r.text)
except Exception as e:
    print('error', e)
    sys.exit(1)
