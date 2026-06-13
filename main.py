import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from google.api_core.exceptions import NotFound
from dotenv import load_dotenv

from database import (
    create_thread, 
    get_threads, 
    get_thread,
    add_message, 
    get_messages, 
    get_universal_memory_context,
    ping_database,
    update_thread_title
)

load_dotenv()

app = FastAPI(title="AskFirst AI Chat Backend")

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
MODEL_FALLBACKS = [
    GEMINI_MODEL,
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-flash-latest",
]

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


async def require_database():
    try:
        await ping_database()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {e}") from e


def normalize_model_name(model_name: str):
    return model_name.removeprefix("models/")


def model_supports_generate_content(model):
    return "generateContent" in getattr(model, "supported_generation_methods", [])


def get_available_text_model():
    configured_models = [normalize_model_name(model) for model in MODEL_FALLBACKS if model]

    available_models = [
        normalize_model_name(model.name)
        for model in genai.list_models()
        if model_supports_generate_content(model)
    ]

    for model_name in configured_models:
        if model_name in available_models:
            return model_name

    for model_name in available_models:
        if "flash" in model_name:
            return model_name

    if available_models:
        return available_models[0]

    raise RuntimeError("No Gemini models that support generateContent are available for this API key.")


def generate_reply(history, prompt):
    last_error = None

    for model_name in dict.fromkeys(MODEL_FALLBACKS):
        try:
            model = genai.GenerativeModel(model_name=normalize_model_name(model_name))
            chat = model.start_chat(history=history)
            return chat.send_message(prompt).text
        except NotFound as e:
            last_error = e

    fallback_model = get_available_text_model()
    model = genai.GenerativeModel(model_name=fallback_model)
    chat = model.start_chat(history=history)
    try:
        return chat.send_message(prompt).text
    except Exception as e:
        raise last_error or e

class ChatRequest(BaseModel):
    message: str

class ThreadCreate(BaseModel):
    title: str = "New Chat"

@app.get("/health")
async def api_health():
    database_status = "ok"
    available_model = None
    try:
        await ping_database()
    except Exception as e:
        database_status = f"unavailable: {e}"

    if GEMINI_API_KEY:
        try:
            available_model = get_available_text_model()
        except Exception as e:
            available_model = f"unavailable: {e}"

    return {
        "status": "ok",
        "database": database_status,
        "gemini_configured": bool(GEMINI_API_KEY),
        "gemini_model": GEMINI_MODEL,
        "available_gemini_model": available_model,
    }

@app.post("/threads")
async def api_create_thread(request: ThreadCreate):
    await require_database()
    thread_id = await create_thread(request.title)
    return {"thread_id": thread_id, "title": request.title}

@app.get("/threads")
async def api_get_threads():
    await require_database()
    return await get_threads()

@app.get("/threads/{thread_id}/messages")
async def api_get_messages(thread_id: str):
    await require_database()
    return await get_messages(thread_id)

@app.post("/threads/{thread_id}/chat")
async def api_chat(thread_id: str, request: ChatRequest):
    # Verify thread exists if not universal (though we shouldn't chat in universal directly)
    if thread_id == "universal":
        raise HTTPException(status_code=400, detail="Cannot chat directly in the universal thread.")
    
    await require_database()
    thread = await get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured.")

    # 1. Save user message to DB
    await add_message(thread_id, "user", request.message)

    # 2. Retrieve thread history to continue the conversation
    thread_messages = await get_messages(thread_id)
    
    # Format history for Gemini SDK
    history = []
    for msg in thread_messages:
        # Don't include the message we just added in history, 
        # as we'll send it as the current message.
        if msg["content"] != request.message or msg != thread_messages[-1]:
             history.append({
                 "role": "user" if msg["role"] == "user" else "model",
                 "parts": [msg["content"]]
             })

    # 3. Retrieve Universal Memory Context
    universal_context = await get_universal_memory_context(thread_id, limit=20)
    
    context_prefix = (
        "[System Note: You are a helpful AI assistant with 'Universal Memory'. "
        "You can recall past conversations the user had with you in other threads.]\n"
    )
    if universal_context:
        context_prefix += f"[Recent context from other threads:\n{universal_context}]\n\n"

    try:
        # Inject context to avoid needing system_instruction (which gemini-pro doesn't support)
        if len(history) > 0:
            history[0]["parts"][0] = context_prefix + history[0]["parts"][0]
            ai_reply = await asyncio.to_thread(generate_reply, history, request.message)
        else:
            ai_reply = await asyncio.to_thread(generate_reply, [], context_prefix + request.message)

        # 5. Save AI response to DB
        await add_message(thread_id, "model", ai_reply)

        # 6. Update thread title if it's the first message
        if len(thread_messages) == 1 and thread["title"] == "New Chat":
            new_title = request.message[:30] + "..." if len(request.message) > 30 else request.message
            await update_thread_title(thread_id, new_title)

        return {"reply": ai_reply}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
