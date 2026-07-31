import subprocess
import time
import requests

proc = subprocess.Popen(['.\\.venv\\Scripts\\python.exe', 'app.py'])
time.sleep(3)
try:
    resp = requests.get('http://localhost:3000/')
    print("SERVER RUNNING, STATUS:", resp.status_code)
except Exception as e:
    print("ERROR CONNECTING:", e)

proc.terminate()
