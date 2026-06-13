import os
import asyncio
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = "askfirst_ai_chat"
DB_TIMEOUT_SECONDS = 3

client = AsyncIOMotorClient(
    MONGODB_URI,
    connectTimeoutMS=3000,
    serverSelectionTimeoutMS=3000,
)
db = client[DB_NAME]

# Collections
threads_collection = db.get_collection("threads")
messages_collection = db.get_collection("messages")

def get_db():
    return db

async def ping_database():
    await asyncio.wait_for(client.admin.command("ping"), timeout=DB_TIMEOUT_SECONDS)

async def create_thread(title: str = "New Chat"):
    thread = {
        "title": title,
        "created_at": datetime.now(timezone.utc)
    }
    result = await threads_collection.insert_one(thread)
    return str(result.inserted_id)

async def get_threads():
    threads = []
    cursor = threads_collection.find({}).sort("created_at", -1)
    async for document in cursor:
        document["_id"] = str(document["_id"])
        threads.append(document)
    return threads

async def get_thread(thread_id: str):
    if not ObjectId.is_valid(thread_id):
        return None

    thread = await threads_collection.find_one({"_id": ObjectId(thread_id)})
    if thread:
        thread["_id"] = str(thread["_id"])
    return thread

async def add_message(thread_id: str, role: str, content: str):
    message = {
        "thread_id": thread_id,
        "role": role,  # 'user' or 'model'
        "content": content,
        "created_at": datetime.now(timezone.utc)
    }
    await messages_collection.insert_one(message)
    return message

async def get_messages(thread_id: str):
    messages = []
    # If thread_id is "universal", fetch all messages chronologically
    if thread_id == "universal":
        cursor = messages_collection.find({}).sort("created_at", 1)
    else:
        cursor = messages_collection.find({"thread_id": thread_id}).sort("created_at", 1)
        
    async for document in cursor:
        document["_id"] = str(document["_id"])
        messages.append(document)
    return messages

async def get_universal_memory_context(current_thread_id: str, limit: int = 20):
    """
    Fetch recent messages from ALL threads EXCEPT the current one, 
    to provide the AI with 'universal memory' background context.
    """
    pipeline = [
        {"$match": {"thread_id": {"$ne": current_thread_id}}},
        {"$sort": {"created_at": -1}},
        {"$limit": limit},
        {"$sort": {"created_at": 1}} # Sort back to chronological
    ]
    
    cursor = messages_collection.aggregate(pipeline)
    messages = []
    async for doc in cursor:
        messages.append(f"{doc['role'].upper()}: {doc['content']}")
        
    return "\n".join(messages)

async def update_thread_title(thread_id: str, title: str):
    if not ObjectId.is_valid(thread_id):
        return

    await threads_collection.update_one(
        {"_id": ObjectId(thread_id)},
        {"$set": {"title": title}}
    )
