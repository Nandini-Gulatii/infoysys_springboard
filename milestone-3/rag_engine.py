from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from config import Config


class RAGEngine:
    def __init__(self, vectorstore):
        if not Config.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")

        # Initialize OpenAI LLM
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            openai_api_key=Config.OPENAI_API_KEY,
            max_tokens=500
        )

        # Custom prompt
        self.prompt_template = """You are a helpful AI assistant that answers questions based ONLY on the provided context.

Context from user's uploaded documents:
{context}

User Question: {question}

Instructions:
1. Answer based ONLY on the context provided above
2. If the context doesn't contain relevant information, say: "I don't have enough information to answer this question based on the uploaded documents."
3. Be concise and accurate
4. Do not make up information
5. If the question is about the documents in general, provide a summary

Answer:"""

        self.prompt = PromptTemplate(
            template=self.prompt_template,
            input_variables=["context", "question"]
        )

        # Create retrieval chain
        self.qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(
                search_kwargs={"k": 3}
            ),
            chain_type_kwargs={"prompt": self.prompt},
            return_source_documents=True
        )

    def query(self, question):
        """Query the RAG system"""
        try:
            print(f"🔍 Processing question: {question}")
            result = self.qa_chain.invoke({"query": question})

            # Format response
            response = {
                "answer": result["result"],
                "sources": []
            }

            # Extract source information
            if "source_documents" in result:
                for doc in result["source_documents"]:
                    source_info = {
                        "content": doc.page_content[:200] + "...",
                        "source": doc.metadata.get("source", "Unknown"),
                        "type": doc.metadata.get("type", "Unknown")
                    }
                    response["sources"].append(source_info)

            print(f"✅ Generated answer with {len(response['sources'])} sources")
            return response

        except Exception as e:
            print(f"❌ RAG query error: {e}")
            return {
                "answer": "Sorry, I encountered an error processing your request. Please try again.",
                "sources": []
            }