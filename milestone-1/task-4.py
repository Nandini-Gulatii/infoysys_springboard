import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec

# ---------------- LOAD ENV ----------------
load_dotenv(".env")   # or full path if needed

api_key = os.getenv("PINECONE_API_KEY")

if not api_key:
    raise Exception("API Key not found! Add PINECONE_API_KEY to .env")

# ---------------- CONNECT ----------------
pc = Pinecone(api_key=api_key)
print("Connected to Pinecone!")

# ---------------- CREATE INDEX ----------------
index_name = "demo-index"

pc.create_index(
    name=index_name,
    dimension=384,
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",
        region="us-east-1"
    )
)

print("Index created!")

# ---------------- INSERT VECTORS ----------------
index = pc.Index(index_name)

vectors = [
    ("id1", [0.1]*384, {"text": "example vector 1"}),
    ("id2", [0.2]*384, {"text": "example vector 2"}),
]

index.upsert(vectors=vectors)
print("Vectors inserted!")

# ---------------- QUERY ----------------
result = index.query(vector=[0.1]*384, top_k=2, include_metadata=True)
print(result)

# ---------------- DELETE A VECTOR ----------------
index.delete(ids=["id2"])
print("Deleted id2")

# ---------------- DELETE INDEX (AFTER TESTING) ----------------
# pc.delete_index(index_name)
# print("Index deleted!")
