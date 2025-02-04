import logging

from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores.chroma import Chroma

logging.basicConfig(level=logging.DEBUG)

file_path = (
   "./customers-1000.csv"
)

loader = CSVLoader(file_path=file_path)
customer_data = loader.load()

# embeddings_model = OpenAIEmbeddings()
embeddings_model = OpenAIEmbeddings(
    check_embedding_ctx_length=False,
    model="text-embedding-nomic-embed-text-v1.5",
    base_url="http://localhost:1234/v1",
    openai_api_key="not-needed"
)

db = Chroma.from_documents(
   customer_data,
   embedding=embeddings_model,
   persist_directory="../my_embeddings"
)

results = db.similarity_search(
   "Which customers are associated with the company Cherry and Sons?"
)

for result in results:
   print("\n")
   print(result.page_content)