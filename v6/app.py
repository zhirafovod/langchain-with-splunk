import os
import random
from flask import Flask, request
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.chat_history import InMemoryChatMessageHistory, BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_chroma import Chroma
from langchain.tools import tool
from langchain.agents import create_react_agent, AgentExecutor
from langchain import hub

from opentelemetry.instrumentation.langchain import LangchainInstrumentor

# Initialize Flask app and OpenTelemetry
app = Flask(__name__)

LangchainInstrumentor().instrument()

# Initialize the language model (local Llama 3.2)
model = ChatOpenAI(
    base_url="http://localhost:1234/v1",
    model="llama-3.2-3b-instruct",
    temperature=0,
    api_key="not-needed"
)

# Initialize embeddings model
embeddings_model = OpenAIEmbeddings(
    check_embedding_ctx_length=False,
    model="text-embedding-nomic-embed-text-v1.5",
    base_url="http://localhost:1234/v1",
    openai_api_key="not-needed"
)

# Set up multiple vector databases
company_db = Chroma(
    persist_directory="../company_embeddings",
    embedding_function=embeddings_model
)

general_db = Chroma(
    persist_directory="../general_knowledge_embeddings",
    embedding_function=embeddings_model
)

# Define tools
@tool
def company_info(query: str) -> str:
    """Retrieve information about companies from the company vector database."""
    docs = company_db.similarity_search(query)
    return "\n".join([doc.page_content for doc in docs])

@tool
def general_knowledge(query: str) -> str:
    """Retrieve general knowledge information from the general knowledge vector database."""
    docs = general_db.similarity_search(query)
    return "\n".join([doc.page_content for doc in docs])

@tool
def web_search_tool(query: str) -> str:
    """Perform a simulated web search (replace with real API in production)."""
    return f"Web search results for '{query}': [simulated results]"

# List of tools for the agent
tools = [company_info, general_knowledge, web_search_tool]

# Set up the agent with ReAct prompt
prompt = hub.pull("hwchase17/react")
# output the fetched prompt
print(prompt)
agent = create_react_agent(model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Chat history management
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

# Wrap agent with message history
with_message_history = RunnableWithMessageHistory(
    agent_executor,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)

# API endpoint to handle questions
@app.route("/askquestion", methods=['POST'])
def ask_question():
    data = request.json
    question = data.get('question')
    session_id = data.get('session_id', 'default')
    config = {"configurable": {"session_id": session_id}}
    response = with_message_history.invoke(
        {"input": question},
        config=config
    )
    return response['output']

# API endpoint to return a random company name
@app.route('/random', methods=['GET'])
def random_company():
    all_metadatas = company_db.get()['metadatas']
    company_names = list(set([meta.get("company_name") for meta in all_metadatas if meta.get("company_name")]))
    if company_names:
        return random.choice(company_names)
    else:
        return "No companies found", 404

if __name__ == '__main__':
    app.run(debug=True)