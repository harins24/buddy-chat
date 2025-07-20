# Buddy Chat: AI-Powered Student Context Chatbot

## Project Overview

Buddy Chat is a Python Flask-based REST API project that demonstrates how to:
- Ingest student data into a PostgreSQL vector database (with pgvector extension)
- Generate vector embeddings for each student using a local LLM (deepseek-r1:14b)
- Retrieve relevant student context using vector similarity search
- Use the context to answer questions via the LLM
- Stream LLM responses and interact with the data via REST APIs

## Features
- **/api/echo**: Streams LLM responses for a given prompt
- **/api/hello**: Returns a simple greeting
- **/api/ask**: Accepts a question, retrieves relevant student context from the vector DB, and gets a context-aware answer from the LLM
- Automatic ingestion of students.json into the vector DB on app startup

## Prerequisites
- Docker and Docker Compose installed
- (Optional) Local LLM server running at `http://localhost:11434` with model `deepseek-r1:14b`

## How to Run

1. **Clone the repository** (if not already done)

2. **Build and start all services using Docker Compose:**
   ```sh
   docker compose up --build
   ```
   This will:
   - Start a PostgreSQL database with pgvector extension
   - Build and run the Python Flask app

3. **Access the APIs:**
   - Flask app runs on [http://localhost:5000](http://localhost:5000)
   - Example endpoints:
     - `GET /api/echo?prompt=Hello`
     - `GET /api/hello?name=YourName`
     - `GET /api/ask?question=What are popular hobbies?`

## Running the LLM Locally with Ollama

This project is designed to work with a local LLM server, such as Ollama. You can easily start the LLM using Ollama with the following command:

```
ollama run deepseek-r1:14b
```

This will start the deepseek-r1:14b model locally at `http://localhost:11434`, which is the default endpoint expected by the project. Make sure Ollama is installed and the model is available before starting the Python app or using Docker Compose.

For more information on Ollama, visit: [https://ollama.com/](https://ollama.com/)

## File Structure
- `app.py` - Main Flask app with REST APIs
- `ingest_students.py` - Ingests students.json into the vector DB with embeddings
- `students.json` - Sample student data (India-based)
- `requirements.txt` - Python dependencies
- `Dockerfile` - Containerizes the Python app
- `docker-compose.yml` - Orchestrates the app and database

## Notes
- The ingestion logic runs automatically when the Flask app starts.
- The project expects the LLM to provide an embedding endpoint (`/api/embeddings`) and a generate endpoint (`/api/generate`).
- You can modify the student data in `students.json` as needed.
- For production, secure your database credentials and API endpoints.

## Troubleshooting
- If you see errors related to vector types, ensure the pgvector extension is enabled (handled automatically by the app).
- If the LLM is not running or accessible, some endpoints may fail.
- Check logs for detailed error messages.

## License
MIT
