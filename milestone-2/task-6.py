import os
from dotenv import load_dotenv

# ---------------- LOAD ENV ----------------
load_dotenv()
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not PINECONE_API_KEY:
    raise Exception("PINECONE_API_KEY not found")

# ---------------- LANGCHAIN IMPORTS (NEW STYLE) ----------------
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredHTMLLoader,
    PyPDFLoader,
    Docx2txtLoader
)

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings

# ---------------- PINECONE ----------------
from pinecone import Pinecone, ServerlessSpec

# ---------------- CONFIG ----------------
DATA_DIR = "../data"
INDEX_NAME = "task6-index"
DIMENSION = 384

# ---------------- CONNECT PINECONE ----------------
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if not exists
existing_indexes = [idx["name"] for idx in pc.list_indexes()]
if INDEX_NAME not in existing_indexes:
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")
    )
    print("Index created")
else:
    print("Index already exists")

index = pc.Index(INDEX_NAME)

# ---------------- EMBEDDING MODEL ----------------
embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ---------------- TEXT SPLITTER ----------------
splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=200
)

# ---------------- LOAD FILES SAFELY ----------------
def load_file(path):
    try:
        if path.endswith(".txt"):
            return TextLoader(path).load()
        elif path.endswith(".pdf"):
            return PyPDFLoader(path).load()
        elif path.endswith(".docx"):
            return Docx2txtLoader(path).load()
        elif path.endswith(".html"):
            return UnstructuredHTMLLoader(path).load()
    except Exception as e:
        print(f" Failed loading {path}: {e}")
        return []

# ---------------- PROCESS FILES ----------------
vector_id = 0

for filename in os.listdir(DATA_DIR):
    file_path = os.path.join(DATA_DIR, filename)
    print(f"\nProcessing: {filename}")

    docs = load_file(file_path)
    if not docs:
        continue

    chunks = splitter.split_documents(docs)

    for chunk in chunks:
        try:
            embedding = embeddings.embed_query(chunk.page_content)

            index.upsert([
                {
                    "id": f"vec-{vector_id}",
                    "values": embedding,
                    "metadata": {
                        "text": chunk.page_content,
                        "source": filename
                    }
                }
            ])
            vector_id += 1

        except Exception as e:
            print(f" Failed embedding chunk from {filename}: {e}")

print("\n✅ Task 6 completed successfully!")









