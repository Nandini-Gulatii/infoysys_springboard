import os
from dotenv import load_dotenv

# ---- Load env ----
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

if not OPENAI_API_KEY:
    raise Exception("OPENAI_API_KEY not found in .env")

if not PINECONE_API_KEY:
    raise Exception("PINECONE_API_KEY not found in .env")

# ---- LangChain imports (UPDATED) ----
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_pinecone import PineconeVectorStore
from langchain_huggingface import HuggingFaceEmbeddings
from pinecone import Pinecone

# ---- Pinecone connection ----
pc = Pinecone(api_key=PINECONE_API_KEY)

INDEX_NAME = "task6-index"   # same index used in task 6/7

# ---- Embedding model ----
embedding = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ---- Vector store ----
vector_store = PineconeVectorStore.from_existing_index(
    index_name=INDEX_NAME,
    embedding=embedding
)

# ---- SYSTEM TEMPLATE (MENTOR PROVIDED) ----
SYSTEM_TEMPLATE = """
You are LegaBot, a precise legal research assistant designed to help users find authoritative legal provisions, rules, and relevant case law.

Use the following retrieved context to answer the user's question:

{context}

Follow all legal disclaimer rules strictly.
"""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_TEMPLATE),
    ("human", "{question}")
])

# ---- LLM ----
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0
)

# ---- RAG CHAIN ----
chain = prompt | llm | StrOutputParser()

# ---- USER QUERY ----
query = "What is Section 420 of IPC?"

# ---- Retrieve relevant docs ----
docs = vector_store.similarity_search(query, k=4)

context_text = "\n\n".join([
    f"[Chunk {i}] {doc.page_content}"
    for i, doc in enumerate(docs)
])

# ---- Run chain ----
response = chain.invoke({
    "context": context_text,
    "question": query
})

# ---- Output ----
print("\n===== LEGALBOT RESPONSE =====\n")
print(response)

print("\n===== SOURCES USED =====\n")
for i, doc in enumerate(docs):
    print(f"Source {i+1}:")
    print(doc.metadata)

