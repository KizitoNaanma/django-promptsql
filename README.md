# PromptSQL

PromptSQL is a lightweight service that lets you query a database using natural language prompts.  
It uses **LangChain** with an LLM to translate your prompt into SQL, run the query, and return the result.  
It supports **streaming responses**, so results can be consumed in real-time, and manages session state either in-memory or with Redis.

---

## Features

-  **Natural language → SQL** queries  
-  Supports **SQLite** (default, ephemeral DB inside the container)  
-  **Session memory management** (in-memory or Redis if configured)  
-  **Streaming responses** from the LLM  
-  Dockerized setup with `docker-compose`  

---

## Tech Stack

- **Django REST Framework** (API endpoints)  
- **LangChain** (LLM orchestration)  
- **SQLite** (default database)  
- **Redis** (optional session storage)  
- **Docker + docker-compose**  

---

## Environment Variables

Create a `.env` file in the project root with:

```env
  OPENAI_API_KEY=your-openai-key
  DATABASE_URL=sqlite:///db.sqlite3
  REDIS_URL=redis://redis:6379/0   # Optional; falls back to in-memory if not set 
```
---
## Running with Docker

Build and start the services:

```bash
docker-compose up --build
```
Access at 
```bash
http://localhost:8000/api/chat/
