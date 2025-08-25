import os
import json
import redis
from langchain_openai import ChatOpenAI
from langchain_experimental.sql import SQLDatabaseSequentialChain
from langchain_community.utilities import SQLDatabase
from langchain.memory import ConversationBufferMemory
from langchain.callbacks.base import BaseCallbackHandler

# Env vars
openai_api_key = os.getenv("OPENAI_API_KEY")
database_url = os.getenv("DATABASE_URL")
redis_url = os.getenv("REDIS_URL")

# DB connection
db = SQLDatabase.from_uri(database_url)

# Session store: Redis if available, else in-memory
if redis_url:
    redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
else:
    redis_client = None
sessions = {}

# More general-purpose schema context
schema_context = """
You are a helpful assistant that can generate and execute SQL queries on the connected database.
Always return clear, accurate, and safe results based only on the schema.
Use joins only if necessary, otherwise keep queries simple.
"""

# Callback for streaming tokens
class StreamingHandler(BaseCallbackHandler):
    def __init__(self):
        self.tokens = []

    def on_llm_new_token(self, token: str, **kwargs):
        self.tokens.append(token)

    def get_stream(self):
        for token in self.tokens:
            yield token

# Truncate memory
def truncate_memory(memory, max_tokens=4000):
    messages = memory.chat_memory.messages
    total_tokens = sum(len(str(msg).split()) for msg in messages)
    while total_tokens > max_tokens and messages:
        messages.pop(0)
        total_tokens = sum(len(str(msg).split()) for msg in messages)
    memory.chat_memory.messages = messages

def _store_session(session_id, data: dict):
    if redis_client:
        redis_client.set(session_id, json.dumps(data))
    else:
        sessions[session_id] = data

def _load_session(session_id):
    if redis_client:
        raw = redis_client.get(session_id)
        return json.loads(raw) if raw else None
    return sessions.get(session_id)

def get_or_create_session(session_id: str, stream: bool, handler: StreamingHandler = None):
    session = _load_session(session_id)
    if not session:
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            input_key="query",
            return_messages=True
        )
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            api_key=openai_api_key,
            temperature=0,
            streaming=stream,
            callbacks=[handler] if handler else []
        )
        chain = SQLDatabaseSequentialChain.from_llm(
            db=db,
            llm=llm,
            memory=memory,
            verbose=True,
            return_intermediate_steps=False,
            input_key="query"
        )
        session = {"chain": chain, "memory": memory, "chat_history": []}
        _store_session(session_id, session)
    return session

def reset_memory(session_id: str):
    session = _load_session(session_id)
    if session:
        session["memory"].clear()
        session["chat_history"] = []
        _store_session(session_id, session)

def process_query(query: str, session_id: str, stream: bool = False):
    try:
        formatted_query = f"{schema_context}\n{query}"
        if stream:
            handler = StreamingHandler()
            session = get_or_create_session(session_id, stream, handler)
            truncate_memory(session["memory"])
            session["chain"].invoke({"query": formatted_query})
            return handler.get_stream()
        else:
            session = get_or_create_session(session_id, stream, None)
            truncate_memory(session["memory"])
            response = session["chain"].invoke({"query": formatted_query})
            result = response.get("result") if isinstance(response, dict) else response

            session["chat_history"].append({"user": query, "bot": result})
            _store_session(session_id, session)

            return {"result": result, "chat_history": session["chat_history"]}
    except Exception as e:
        return [f"[Error]: {str(e)}"] if stream else f"[Error]: {str(e)}"
