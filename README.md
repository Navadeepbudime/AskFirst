# AskFirst AI Chat Application 🚀

**🔴 Live Demo:** [https://askfirst-j2xf2v3qcj7udg3vmgxwti.streamlit.app/](https://askfirst-j2xf2v3qcj7udg3vmgxwti.streamlit.app/)

A modern, full-stack AI chat application built with **Streamlit** (Frontend), **FastAPI** (Backend), and **MongoDB** (Database), powered by **Google Gemini**.

## ✨ Features
- **Universal Memory**: The AI remembers context from your past conversations across different chat threads.
- **Multiple Threads**: Create, manage, and seamlessly switch between different chat threads.
- **Universal Thread View**: A chronological view of your entire chat history across all threads.
- **Thread Management**: Automatically renames threads based on the first message, and allows you to delete unwanted chats.
- **Clean UI**: A sleek, professional chat interface built with Streamlit.

## 🛠️ Tech Stack
- **Frontend**: [Streamlit](https://streamlit.io/)
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: [MongoDB](https://www.mongodb.com/) (using Async Motor)
- **AI Model**: Google Gemini (`gemini-pro`)

## 💻 Local Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/Navadeepbudime/AskFirst.git
   cd AskFirst
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**
   Rename `.env.example` to `.env` and fill in your credentials:
   ```env
   MONGODB_URI=your_mongodb_connection_string
   GEMINI_API_KEY=your_gemini_api_key
   BACKEND_URL=http://localhost:8000
   ```

4. **Start the FastAPI Backend**
   Open a terminal and run:
   ```bash
   uvicorn main:app --reload
   ```

5. **Start the Streamlit Frontend**
   Open a second terminal and run:
   ```bash
   streamlit run app.py
   ```

## 🌐 Deployment
This application is designed to be deployed separately for maximum performance:
- **Database**: Host a free cluster on [MongoDB Atlas](https://www.mongodb.com/atlas).
- **Backend**: Deploy `main.py` as a Web Service on [Render](https://render.com/). Add `GEMINI_API_KEY` and `MONGODB_URI` to your environment variables.
- **Frontend**: Deploy `app.py` on [Streamlit Community Cloud](https://share.streamlit.io/). Add `BACKEND_URL` to your Streamlit secrets, pointing to your live Render backend URL.
