import os
import openai
from dotenv import load_dotenv
import re
from typing import List, Dict
import json

load_dotenv()


class OpenAIProcessor:
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in .env file")

        self.client = openai.OpenAI(api_key=api_key)
        print("✅ OpenAI GPT processor initialized")

    def extract_relevant_context(self, documents: List[Dict], query: str, max_chars: int = 3000) -> str:
        """Extract most relevant context from documents for the query"""
        relevant_chunks = []
        total_chars = 0

        for doc in documents:
            content = doc['content']
            filename = doc['filename']

            # Find sentences containing query terms
            sentences = self._split_into_sentences(content)
            relevant_sentences = []

            query_words = set(query.lower().split())
            query_words = {w for w in query_words if len(w) > 3}  # Filter short words

            for sentence in sentences:
                sentence_lower = sentence.lower()

                # Check for exact phrase match
                if query.lower() in sentence_lower:
                    relevant_sentences.append(sentence)
                    continue

                # Check for word matches
                word_matches = sum(1 for word in query_words if word in sentence_lower)
                if word_matches >= max(1, len(query_words) * 0.3):  # At least 30% match
                    relevant_sentences.append(sentence)

            # If no matches found, take first few sentences
            if not relevant_sentences and sentences:
                relevant_sentences = sentences[:3]

            # Format context with filename
            if relevant_sentences:
                doc_context = f"\n[From: {filename}]\n" + " ".join(relevant_sentences[:10])  # Limit to 10 sentences

                if total_chars + len(doc_context) <= max_chars:
                    relevant_chunks.append(doc_context)
                    total_chars += len(doc_context)

        return "\n".join(relevant_chunks)

    def _split_into_sentences(self, text: str) -> List[str]:
        """Simple sentence splitting"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def generate_answer(self, query: str, context: str, documents: List[Dict]) -> Dict:
        """Generate answer using GPT with context"""
        try:
            # Prepare system message
            system_message = """You are an AI Document Assistant that helps users understand their uploaded documents. 
            Always answer based ONLY on the provided document context. 
            If the context doesn't contain relevant information, say so clearly.
            Be concise, accurate, and helpful.
            Format your answer with clear paragraphs and bullet points when appropriate."""

            # Prepare user message with context
            user_message = f"""Question: {query}

Document Context:
{context}

Instructions:
1. Answer based ONLY on the provided document context
2. If context doesn't contain the answer, say: "Based on the uploaded documents, I couldn't find specific information about this."
3. Be specific and cite which document information came from
4. Use bullet points for lists
5. Keep answer under 300 words

Answer:"""

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=500,
                top_p=0.9
            )

            answer = response.choices[0].message.content.strip()

            # Extract sources
            sources = self._extract_sources(answer, documents)

            return {
                "answer": answer,
                "sources": sources,
                "model": "gpt-3.5-turbo",
                "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
            }

        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return {
                "answer": f"I encountered an error processing your question. Please try again. Error: {str(e)[:100]}",
                "sources": [],
                "error": str(e)
            }

    def _extract_sources(self, answer: str, documents: List[Dict]) -> List[Dict]:
        """Extract sources mentioned in the answer"""
        sources = []
        seen_filenames = set()

        # Look for document references in answer
        for doc in documents:
            filename = doc['filename']

            # Check if filename is mentioned in answer
            if filename in answer:
                # Extract relevant sentences from the document
                sentences = self._split_into_sentences(doc['content'])
                relevant_sentences = sentences[:3]  # Take first 3 sentences

                for sentence in relevant_sentences:
                    if sentence and len(sentence) > 20:
                        sources.append({
                            "content": sentence[:200] + ("..." if len(sentence) > 200 else ""),
                            "source": filename,
                            "type": "Relevant content"
                        })
                        break  # Only add one source per document

                seen_filenames.add(filename)

        # If no sources found, add document summaries
        if not sources:
            for doc in documents[:2]:  # Limit to 2 documents
                preview = doc['content'][:150] + "..." if len(doc['content']) > 150 else doc['content']
                sources.append({
                    "content": preview,
                    "source": doc['filename'],
                    "type": "Document preview"
                })

        return sources[:5]  # Limit to 5 sources

    def summarize_documents(self, documents: List[Dict]) -> str:
        """Generate a summary of all documents"""
        if not documents:
            return "No documents uploaded yet."

        # Prepare context
        context_parts = []
        for doc in documents[:3]:  # Summarize first 3 documents
            content_preview = doc['content'][:1000]  # First 1000 chars
            context_parts.append(f"\n[Document: {doc['filename']}]\n{content_preview}")

        context = "\n".join(context_parts)

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful document summarizer."},
                    {"role": "user", "content": f"""Please provide a concise summary of these documents:

{context}

Summary should include:
1. Main topics covered
2. Document types and purposes
3. Key points from each document
4. Overall theme

Keep summary under 200 words."""}
                ],
                temperature=0.3,
                max_tokens=300
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"❌ OpenAI summarization error: {e}")
            return f"Summary unavailable. Error: {str(e)[:100]}"

    def analyze_specific_topic(self, topic: str, documents: List[Dict]) -> str:
        """Analyze a specific topic across documents"""
        if not documents:
            return f"No documents to analyze '{topic}'."

        # Extract relevant context for the topic
        context = self.extract_relevant_context(documents, topic, max_chars=2000)

        if not context:
            return f"Could not find information about '{topic}' in the uploaded documents."

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert document analyst."},
                    {"role": "user", "content": f"""Analyze this topic: {topic}

Based on this document context:
{context}

Provide a detailed analysis including:
1. What the documents say about {topic}
2. Key points and details
3. References to specific sections or laws (if applicable)
4. Overall understanding from the documents

Analysis:"""}
                ],
                temperature=0.3,
                max_tokens=400
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"❌ OpenAI analysis error: {e}")
            return f"Analysis unavailable. Error: {str(e)[:100]}"


# Global instance
openai_processor = None
try:
    openai_processor = OpenAIProcessor()
except Exception as e:
    print(f"⚠️ OpenAI processor not available: {e}")