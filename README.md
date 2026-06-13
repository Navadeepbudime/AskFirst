# AskFirst

AskFirst is a Streamlit chat UI backed by a FastAPI API, MongoDB, and Gemini.

## Local setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in:

```text
MONGODB_URI=your_mongodb_connection_string
GEMINI_API_KEY=your_gemini_api_key_here
BACKEND_URL=http://127.0.0.1:8000
```

3. Start the backend:

```bash
uvicorn main:app --host 127.0.0.1 --port 8000
```

4. Start the frontend:

```bash
streamlit run app.py --server.address 127.0.0.1 --server.port 8501
```

## Deploy on Render

This repo includes `render.yaml` for a two-service Render deploy:

- `askfirst-backend`: FastAPI API
- `askfirst-frontend`: Streamlit UI

Deployment steps:

1. Push this repo to GitHub.
2. In Render, create a new Blueprint from the GitHub repo.
3. Set these backend environment variables:

```text
MONGODB_URI=your_mongodb_atlas_connection_string
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-latest
```

4. Deploy the backend first and copy its public URL, for example:

```text
https://askfirst-backend.onrender.com
```

5. Set this frontend environment variable:

```text
BACKEND_URL=https://askfirst-backend.onrender.com
```

6. Redeploy the frontend.

For MongoDB, use MongoDB Atlas or another hosted MongoDB service. A local MongoDB URL like `mongodb://localhost:27017` will not work from Render.

## Deploy frontend on Streamlit Community Cloud

Streamlit Community Cloud runs only the Streamlit frontend. Deploy the FastAPI backend separately first, for example on Render.

1. In Streamlit Community Cloud, create an app from this GitHub repo.
2. Set the app entrypoint file to:

```text
app.py
```

3. In Advanced settings, select Python 3.12.
4. Add this secret:

```toml
BACKEND_URL = "https://your-backend-name.onrender.com"
```

5. Deploy or reboot the app.

If dependency installation fails, open "Manage app" and check the terminal log for the exact package error.
