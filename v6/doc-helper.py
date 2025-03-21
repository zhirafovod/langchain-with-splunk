import os
import requests
import random
from bs4 import BeautifulSoup
from flask import Flask, request, jsonify

# -----------------------------
# LangChain and Observability
# -----------------------------
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.chat_history import InMemoryChatMessageHistory, BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_chroma import Chroma
from langchain.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
# from langchain import hub, PromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
# from langchain.callbacks.stdout import StdOutCallbackHandler

# Optional: OpenTelemetry instrumentation for observability of your chain
from opentelemetry.instrumentation.langchain import LangchainInstrumentor

# -----------------------------
# Flask App
# -----------------------------
app = Flask(__name__)

# -----------------------------
# OpenTelemetry Setup
# -----------------------------
otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_HTTP_ENDPOINT", "http://127.0.0.1:4318")
LangchainInstrumentor().instrument()

# -----------------------------
# Model and Embeddings Setup
# -----------------------------
model = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    model="meta-llama-3.1-8b-instruct",
    temperature=0,
    api_key="not-needed",
    # callbacks=[StdOutCallbackHandler()],
)

# Embeddings model
embeddings_model = OpenAIEmbeddings(
    check_embedding_ctx_length=False,
    model="text-embedding-nomic-embed-text-v1.5",
    base_url="http://localhost:1234/v1",
    openai_api_key="not-needed"
)

# -----------------------------
# Documentation Embeddings
# -----------------------------
docs = [
    {"name": "Splunk Documentation Root", "desc": "Splunk Product Documentation Pages", "url": "https://docs.splunk.com/Documentation" },
]

documents = [
    Document(page_content=doc["desc"], metadata={"doc": doc["name"], "url": doc["url"]})
    for doc in docs
]

docs_db = Chroma.from_documents(
    documents=documents,
    embedding=embeddings_model,
    persist_directory="../splunk_embeddings"
)

# -----------------------------
# Constants and Tools
# -----------------------------
ROOT_URL = "https://docs.splunk.com/Documentation"

@tool
def fetch_page_content(url: str) -> str:
    """Fetch the content of a given URL from Splunk documentation."""
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        content = soup.get_text(strip=True)[:4000]  # Limit content size

        # Collect links pointing to docs.splunk.com
        all_links = {}
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            text = a.get_text(strip=True)
            if href.startswith('http') and 'docs.splunk.com' in href:
                all_links[href] = text

        top_links = list(all_links.items())[:10]
        link_options = "\n".join([f"{text}: {l}" for (l, text) in top_links])
        print(f"Content: {content}\nAvailable links:\n{link_options}")
        return f"Content: {content}\nAvailable links:\n{link_options}"

    except Exception as e:
        return f"Error fetching {url}: {str(e)}"

@tool
def search_doc_info(query: str) -> str:
    """Retrieve documentations from embeddings."""
    docs = docs_db.similarity_search(query, k=2)
    return "\n".join([f"{doc.metadata['product']}: {doc.page_content}" for doc in docs])

@tool
def provide_answer(answer: str) -> str:
    """Provide the final answer to the user's question."""
    return f"Final answer: {answer}"

# -----------------------------
# Agent Logic
# -----------------------------
agent_instructions = """
You are a Splunk documentation navigator. Your goal is to answer questions about Splunk by traversing its documentation. Use the following strategy:
1. Start by calling `search_doc_info` with the user's question to find relevant documentation.
2. Analyze the content and available links returned by `fetch_page_content`.
3. If the content answers the question, call `provide_answer` with the answer.
4. If not, choose the most relevant link from the list and call `fetch_page_content` with that URL.
5. Limit traversal to 5 steps; if no answer is found, provide the best available information with `provide_answer`.
"""

prompt_template = """
Answer the following questions as best you can. You have access to the following tools:
    
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}
"""
prompt = PromptTemplate.from_template(prompt_template)
print(f"Prompt: {prompt}")

prompt.template = agent_instructions  # Fix: Use `template` instead of `messages`

agent = create_react_agent(
    llm=model,
    tools=[fetch_page_content, search_doc_info, provide_answer],
    prompt=prompt
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=[fetch_page_content, search_doc_info, provide_answer],
    verbose=True,
    max_iterations=3,  # Limit traversal steps
    # handle_parsing_errors=True
)

# -----------------------------
# Managing Chat History
# -----------------------------
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

with_message_history = RunnableWithMessageHistory(
    agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)

# -----------------------------
# Flask Endpoints
# -----------------------------
@app.route("/askquestion", methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question')
    session_id = data.get('session_id', 'default')
    config = {"configurable": {"session_id": session_id}}

    response = with_message_history.invoke(
        {"input": f"Start at {ROOT_URL} and answer: {question}"},
        config=config
    )
    return jsonify({"answer": response["output"]})

@app.route("/random", methods=['GET'])
def random_product():
    all_metadatas = docs_db.get()['metadatas']
    product_names = [meta["product"] for meta in all_metadatas if "product" in meta]
    if not product_names:
        return "No products found", 404
    return random.choice(product_names)

if __name__ == '__main__':
    app.run(debug=True, port=8080)
