import os
from dotenv import load_dotenv

load_dotenv()

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone

# ---------- ENV ----------
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
if not PINECONE_API_KEY:
    raise Exception("PINECONE_API_KEY not found in .env")

# ---------- EMBEDDING ----------
embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ---------- VECTOR STORE ----------
index_name = "task6-index"

vector_store = PineconeVectorStore.from_existing_index(
    index_name=index_name,
    embedding=embedding
)

# ---------- QUERY ----------
query = input("Enter your query: ")

results = vector_store.similarity_search(query, k=4)

print("\nTop Matching Results:\n")
for i, doc in enumerate(results, 1):
    print(f"{i}. {doc.page_content[:300]}...\n")
