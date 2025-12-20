import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Load API key
load_dotenv()   # loads .env or s.env
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise Exception("OPENAI_API_KEY not found")

# Initialize GPT-3.5 Turbo
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7
)

# Ask a random question
response = llm.invoke([
    HumanMessage(content="Explain semantic search in simple words")
])

print("GPT Response:\n")
print(response.content)
