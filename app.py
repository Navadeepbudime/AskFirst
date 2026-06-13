import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = 10

st.set_page_config(page_title="AskFirst AI", layout="wide")

if "active_thread_id" not in st.session_state:
    st.session_state.active_thread_id = None


def get_threads():
    try:
        response = requests.get(f"{BACKEND_URL}/threads", timeout=REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json()
        st.sidebar.error(f"Backend error {response.status_code}: {response.text}")
        return []
    except requests.RequestException as e:
        st.sidebar.error(f"Could not connect to backend: {e}")
        return []


def get_messages(thread_id):
    try:
        response = requests.get(
            f"{BACKEND_URL}/threads/{thread_id}/messages",
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 200:
            return response.json()
        st.error(f"Backend error {response.status_code}: {response.text}")
        return []
    except requests.RequestException as e:
        st.error(f"Could not connect to backend: {e}")
        return []


def create_thread(title="New Chat"):
    try:
        response = requests.post(
            f"{BACKEND_URL}/threads",
            json={"title": title},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 200:
            return response.json().get("thread_id")
        st.sidebar.error(f"Backend error {response.status_code}: {response.text}")
        return None
    except requests.RequestException as e:
        st.sidebar.error(f"Could not connect to backend: {e}")
        return None


def send_message(thread_id, message):
    try:
        response = requests.post(
            f"{BACKEND_URL}/threads/{thread_id}/chat",
            json={"message": message},
            timeout=REQUEST_TIMEOUT,
        )
        if response.status_code == 200:
            return response.json().get("reply")
        return f"Error: Backend returned {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return f"Error: Could not connect to backend ({e})"


with st.sidebar:
    st.title("AskFirst AI")

    if st.button("+ New Chat", use_container_width=True):
        new_id = create_thread()
        if new_id:
            st.session_state.active_thread_id = new_id
            st.rerun()

    st.markdown("---")

    if st.button("Universal Thread (All History)", use_container_width=True):
        st.session_state.active_thread_id = "universal"

    st.markdown("### Your Chats")
    threads = get_threads()
    for thread in threads:
        button_label = thread["title"]
        if st.session_state.active_thread_id == thread["_id"]:
            button_label = f"> {thread['title']}"

        if st.button(button_label, key=thread["_id"], use_container_width=True):
            st.session_state.active_thread_id = thread["_id"]
            st.rerun()


if st.session_state.active_thread_id == "universal":
    st.header("Universal Thread")
    st.caption("A chronological view of all your messages across all threads.")

    messages = get_messages("universal")
    if not messages:
        st.info("No messages yet or backend is unreachable.")
    else:
        for message in messages:
            role = "user" if message["role"] == "user" else "assistant"
            with st.chat_message(role):
                st.caption(f"Thread: {message.get('thread_id', 'Unknown')}")
                st.write(message["content"])

    st.info("Universal thread is read-only. Select or create a specific chat to send messages.")

elif st.session_state.active_thread_id:
    thread_title = "Chat"
    for thread in threads:
        if thread["_id"] == st.session_state.active_thread_id:
            thread_title = thread["title"]
            break

    st.header(thread_title)

    messages = get_messages(st.session_state.active_thread_id)

    for message in messages:
        role = "user" if message["role"] == "user" else "assistant"
        with st.chat_message(role):
            st.write(message["content"])

    if prompt := st.chat_input("Type your message here..."):
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply = send_message(st.session_state.active_thread_id, prompt)
                st.write(reply)
                st.rerun()
else:
    st.title("Welcome to AskFirst AI")
    st.write("Select a chat from the sidebar or start a new one to begin.")
    st.info("Make sure your FastAPI backend and MongoDB are running!")
