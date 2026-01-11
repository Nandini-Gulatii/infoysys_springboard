import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from werkzeug.utils import secure_filename
import uuid
import tempfile

# Test document loaders
print("=" * 60)
print("DEBUGGING FILE PROCESSING")
print("=" * 60)

# Test 1: Check imports
print("\n1. Testing imports...")
try:
    from langchain_community.document_loaders import PyPDFLoader, TextLoader, Docx2txtLoader
    print("✅ Document loaders imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Installing missing packages...")
    os.system("pip install pypdf python-docx beautifulsoup4")

# Test 2: Create a test file
print("\n2. Creating test file...")
test_content = """This is a test document for the AI Smart File Assistant.
The application can process multiple file formats including PDF, DOCX, HTML, and TXT.
Users can upload their documents and ask questions about them.
The AI uses RAG (Retrieval Augmented Generation) to provide answers.
Each user gets their own Pinecone vector database index."""

test_file_path = os.path.join(tempfile.gettempdir(), "test_document.txt")
with open(test_file_path, "w", encoding="utf-8") as f:
    f.write(test_content)
print(f"✅ Created test file: {test_file_path}")

# Test 3: Try to load the document
print("\n3. Testing document loader...")
try:
    from langchain_community.document_loaders import TextLoader
    loader = TextLoader(test_file_path, encoding='utf-8')
    documents = loader.load()
    print(f"✅ Successfully loaded {len(documents)} document(s)")
    for i, doc in enumerate(documents[:2]):  # Show first 2
        print(f"   Document {i+1}: {len(doc.page_content)} characters")
        print(f"   Preview: {doc.page_content[:100]}...")
except Exception as e:
    print(f"❌ Error loading document: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check Pinecone setup
print("\n4. Checking Pinecone configuration...")
try:
    from config import Config
    print(f"✅ Config loaded")
    print(f"   PINECONE_API_KEY: {'Set' if Config.PINECONE_API_KEY else 'Not set'}")
    print(f"   OPENAI_API_KEY: {'Set' if Config.OPENAI_API_KEY else 'Not set'}")
    print(f"   PINECONE_ENVIRONMENT: {Config.PINECONE_ENVIRONMENT}")
except Exception as e:
    print(f"❌ Config error: {e}")

# Test 5: Test Pinecone connection
print("\n5. Testing Pinecone connection...")
try:
    import pinecone
    pinecone.init(
        api_key=Config.PINECONE_API_KEY if 'Config' in locals() else '',
        environment=Config.PINECONE_ENVIRONMENT if 'Config' in locals() else 'us-east1-gcp'
    )
    indexes = pinecone.list_indexes()
    print(f"✅ Pinecone connected. Indexes: {indexes}")
except Exception as e:
    print(f"❌ Pinecone connection failed: {e}")

# Test 6: Test embeddings
print("\n6. Testing embeddings...")
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    test_text = "This is a test sentence."
    embedding = embeddings.embed_query(test_text)
    print(f"✅ Embeddings working. Vector dimension: {len(embedding)}")
except Exception as e:
    print(f"❌ Embeddings error: {e}")

print("\n" + "=" * 60)
print("DEBUG COMPLETE")
print("=" * 60)