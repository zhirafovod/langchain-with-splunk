import os

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import OpenAIEmbeddings
from langchain.vectorstores.chroma import Chroma
from flask import Flask, request
from opentelemetry.instrumentation.langchain import LangchainInstrumentor

from langchain_redis import RedisCache, RedisSemanticCache
from langchain.globals import set_llm_cache

import openlit

otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_HTTP_ENDPOINT", "http://127.0.0.1:4318")
openlit.init(otlp_endpoint=otel_endpoint, application_name="my-llm-app", environment="test")

# Use the environment variable if set, otherwise default to localhost
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379")
print(f"Connecting to Redis at: {REDIS_URL}")

redis_cache = RedisCache(redis_url=REDIS_URL)
set_llm_cache(redis_cache)


app = Flask(__name__)
LangchainInstrumentor().instrument()
model = ChatOpenAI(model="gpt-3.5-turbo")

embeddings_model = OpenAIEmbeddings()

db = Chroma(
    persist_directory="../my_embeddings",
    embedding_function=embeddings_model
)

store = {}
config = {"configurable": {"session_id": "test"}}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

with_message_history = RunnableWithMessageHistory(model, get_session_history)

@app.route("/askquestion", methods=['POST'])
def ask_question():

    data = request.json
    question = data.get('question')

    # find the documents most similar to the question that we can pass as context
    context = db.similarity_search(question)

    response = with_message_history.invoke(
        [
            SystemMessage(
                content=f'Use the following pieces of context to answer the question: {context}'
            ),
            HumanMessage(
                content=question
            )
        ],
        config=config
    )

    return response.content

