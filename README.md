# Smart Healthcare — Backend

This repository contains a simple Express + SQLite backend to support the static frontend pages in this folder.


Quick start (Windows):

Option A — Node.js backend (if you have Node installed):

1. Open a terminal in this project folder.
2. Install dependencies:

```powershell
npm install
```

3. Start the server:

```powershell
npm run start
```

Option B — Python (Flask) backend (works if you have Python 3.8+):

1. Create a venv (recommended) and activate it:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

3. Run the server:

```powershell
python app.py
```

4. Open http://localhost:3000 in your browser.

Notes:
- Both backends use a local SQLite file `data.sqlite` to store users.
- The Flask server serves the static frontend files from the repository root.
- These setups are for local development/demo only. Do not use default secrets or the development server in production.
