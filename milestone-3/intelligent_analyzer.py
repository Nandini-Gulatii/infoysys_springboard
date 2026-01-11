import re
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter
import heapq


class IntelligentAnalyzer:
    def __init__(self):
        # Download NLTK data if needed
        try:
            nltk.data.find('tokenizers/punkt')
        except:
            print("📥 Downloading NLTK data...")
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)

        try:
            from nltk.corpus import stopwords
            self.stop_words = set(stopwords.words('english'))
        except:
            self.stop_words = set()

        print("✅ Intelligent Analyzer initialized")

    def generate_intelligent_response(self, query, documents):
        """Generate an intelligent response based on document content"""

        if not documents:
            return "You haven't uploaded any documents yet. Please upload documents first."

        # Check for summary request
        query_lower = query.lower()
        if any(word in query_lower for word in ['summary', 'summarize', 'overview']):
            return self._generate_summary_response(documents)

        # Check for document list request
        if any(phrase in query_lower for phrase in ['what documents', 'list documents', 'show files']):
            return self._list_documents(documents)

        # General query - search in documents
        return self._search_and_respond(query, documents)

    def _generate_summary_response(self, documents):
        """Generate summary of documents"""
        response = [f"📚 **Document Summary** ({len(documents)} documents):\n"]

        for i, doc in enumerate(documents[:3], 1):  # Summarize first 3
            filename = doc['filename']
            content = doc['content']
            file_type = doc['type']

            # Simple summary: first few sentences
            sentences = sent_tokenize(content)
            if len(sentences) > 3:
                summary = " ".join(sentences[:3]) + "..."
            else:
                summary = content[:300] + "..." if len(content) > 300 else content

            response.append(f"\n{i}. **{filename}** ({file_type.upper()}):")
            response.append(f"   {summary}")

            # Word count
            words = len(content.split())
            response.append(f"   📊 {words:,} words")

        if len(documents) > 3:
            response.append(f"\n... and {len(documents) - 3} more documents.")

        return "\n".join(response)

    def _list_documents(self, documents):
        """List uploaded documents"""
        if not documents:
            return "No documents uploaded yet."

        response = [f"📁 **Uploaded Documents** ({len(documents)} files):\n"]

        for i, doc in enumerate(documents[:5], 1):
            filename = doc['filename']
            file_type = doc['type'].upper()
            size = len(doc['content'])

            # Format size
            if size > 1000:
                size_str = f"{size / 1000:.1f}K chars"
            else:
                size_str = f"{size} chars"

            response.append(f"{i}. {filename} ({file_type}, {size_str})")

        if len(documents) > 5:
            response.append(f"\n... and {len(documents) - 5} more files.")

        response.append("\nAsk me questions about any of these documents!")

        return "\n".join(response)

    def _search_and_respond(self, query, documents):
        """Search for query in documents and generate response"""
        query_lower = query.lower()
        query_words = [w for w in query_lower.split() if len(w) > 3]

        results = []

        for doc in documents:
            content_lower = doc['content'].lower()
            filename = doc['filename']

            # Check for exact phrase
            if query_lower in content_lower:
                positions = []
                start = 0
                while True:
                    pos = content_lower.find(query_lower, start)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start = pos + 1

                if positions:
                    # Get context around matches
                    contexts = []
                    for pos in positions[:2]:  # First 2 matches
                        start_pos = max(0, pos - 150)
                        end_pos = min(len(doc['content']), pos + len(query_lower) + 150)
                        context = doc['content'][start_pos:end_pos]
                        context = re.sub(r'\s+', ' ', context).strip()
                        contexts.append(context)

                    results.append({
                        'filename': filename,
                        'matches': len(positions),
                        'contexts': contexts,
                        'score': len(positions) * 100
                    })

            # Check for individual word matches
            elif query_words:
                word_matches = []
                for word in query_words:
                    if word in content_lower:
                        count = content_lower.count(word)
                        word_matches.append((word, count))

                if word_matches:
                    total_matches = sum(count for _, count in word_matches)
                    matching_words = ", ".join([word for word, _ in word_matches[:3]])

                    # Find sentences containing these words
                    sentences = sent_tokenize(doc['content'])
                    relevant_sentences = []

                    for sentence in sentences:
                        sentence_lower = sentence.lower()
                        if any(word in sentence_lower for word, _ in word_matches):
                            relevant_sentences.append(sentence[:200])

                    if relevant_sentences:
                        results.append({
                            'filename': filename,
                            'matches': total_matches,
                            'contexts': relevant_sentences[:3],
                            'score': total_matches * 10,
                            'matching_words': matching_words
                        })

        # Sort by score
        results.sort(key=lambda x: x['score'], reverse=True)

        # Generate response
        if not results:
            return self._generate_fallback_response(query, documents)

        return self._format_search_results(query, results, documents)

    def _format_search_results(self, query, results, documents):
        """Format search results into a response"""
        response = [f"🔍 **Search Results for '{query}'**\n"]

        for i, result in enumerate(results[:3], 1):  # Top 3 results
            response.append(f"\n{i}. **{result['filename']}**")

            if 'matching_words' in result:
                response.append(f"   Matching words: {result['matching_words']}")

            response.append(f"   Found {result['matches']} match{'es' if result['matches'] > 1 else ''}")

            # Add first context
            if result['contexts']:
                context = result['contexts'][0]
                response.append(f"   📄 {context}...")

        if len(results) > 3:
            response.append(f"\n... found in {len(results) - 3} more documents.")

        response.append(f"\n📚 Searched through {len(documents)} document(s).")

        return "\n".join(response)

    def _generate_fallback_response(self, query, documents):
        """Generate response when no matches found"""
        # Count words in query
        query_words = query.lower().split()

        # Find documents with most content
        doc_previews = []
        for doc in documents[:2]:  # First 2 documents
            content = doc['content']
            filename = doc['filename']

            # Get first few sentences
            sentences = sent_tokenize(content)
            preview = " ".join(sentences[:2])[:200] + "..." if len(sentences) > 2 else content[:200] + "..."

            doc_previews.append(f"• **{filename}**: {preview}")

        response = [
            f"I searched through your {len(documents)} document(s) but couldn't find exact matches for '{query}'.",
            "\n**Suggestions:**",
            "1. Try different keywords from your documents",
            "2. Ask about general topics in your documents",
            "3. Upload more relevant documents",
            "\n**Document Previews:**"
        ]

        response.extend(doc_previews)

        if len(documents) > 2:
            response.append(f"\n... and {len(documents) - 2} more documents.")

        return "\n".join(response)


# Global instance
intelligent_analyzer = IntelligentAnalyzer()