import re


class AnswerGenerator:
    def __init__(self):
        print("✅ Answer Generator initialized")

    def generate_proper_answer(self, question, documents):
        """Generate proper answers from documents"""

        if not documents:
            return {
                "answer": "📭 I don't see any uploaded documents yet. Please upload some documents first!",
                "sources": []
            }

        question_lower = question.lower().strip()

        # Handle different question types
        if 'summary' in question_lower or 'summarize' in question_lower:
            return self._generate_summary(documents)
        elif 'what document' in question_lower or 'list document' in question_lower:
            return self._list_documents(documents)
        elif 'what is' in question_lower or 'define' in question_lower or 'explain' in question_lower:
            return self._define_term(question, documents)
        else:
            return self._answer_question(question, documents)

    def _generate_summary(self, documents):
        """Generate summary of documents"""
        answer = ["📚 **Document Summary**\n"]

        for i, doc in enumerate(documents[:3], 1):
            filename = doc['filename']
            content = doc['content']
            words = doc['word_count']

            # Get first few meaningful sentences
            sentences = self._get_first_sentences(content, 2)
            summary = " ".join(sentences)

            answer.append(f"\n{i}. **{filename}**")
            answer.append(f"   {summary}")
            answer.append(f"   📊 {words:,} words")

            # Extract a few key terms
            key_terms = self._extract_key_terms(content, 3)
            if key_terms:
                answer.append(f"   🔑 Key topics: {', '.join(key_terms)}")

        if len(documents) > 3:
            answer.append(f"\n... and {len(documents) - 3} more documents.")

        answer.append("\n💡 Ask me specific questions about any document!")

        return {
            "answer": "\n".join(answer),
            "sources": self._create_sources(documents[:2])
        }

    def _list_documents(self, documents):
        """List uploaded documents"""
        answer = ["📁 **Uploaded Documents**\n"]

        for i, doc in enumerate(documents[:5], 1):
            filename = doc['filename']
            file_type = doc['type'].upper()
            size = len(doc['content'])

            # Format size
            if size > 1000:
                size_str = f"{size / 1000:.1f}K chars"
            else:
                size_str = f"{size} chars"

            # Get preview
            preview = doc['content'][:100].replace('\n', ' ')
            if len(preview) >= 100:
                preview = preview + "..."

            answer.append(f"{i}. **{filename}** ({file_type})")
            answer.append(f"   Size: {size_str}")
            answer.append(f"   Preview: {preview}")
            answer.append("")

        if len(documents) > 5:
            answer.append(f"... and {len(documents) - 5} more files.")

        return {
            "answer": "\n".join(answer),
            "sources": []
        }

    def _define_term(self, question, documents):
        """Define a term from documents"""
        # Extract term from question
        term = self._extract_term(question)

        if not term:
            return self._answer_question(question, documents)

        # Search for term in documents
        relevant_sentences = []
        source_files = []

        for doc in documents:
            content = doc['content']
            sentences = self._split_sentences(content)

            for sentence in sentences:
                if term.lower() in sentence.lower():
                    relevant_sentences.append(sentence)
                    if doc['filename'] not in source_files:
                        source_files.append(doc['filename'])
                    break  # Only take first match per document

        if not relevant_sentences:
            return {
                "answer": f"❌ I couldn't find information about '{term}' in your documents.",
                "sources": []
            }

        # Build answer
        answer = [f"📖 **Information about {term.title()}**\n"]
        answer.append(f"Based on your documents:\n")

        for i, (sentence, filename) in enumerate(zip(relevant_sentences[:3], source_files[:3]), 1):
            clean_sentence = re.sub(r'\s+', ' ', sentence).strip()
            answer.append(f"\n{i}. **From {filename}:**")
            answer.append(f"   {clean_sentence}")

        return {
            "answer": "\n".join(answer),
            "sources": self._create_sources_from_sentences(relevant_sentences[:2], source_files[:2])
        }

    def _answer_question(self, question, documents):
        """Answer general questions"""
        question_lower = question.lower()
        relevant_content = []

        for doc in documents:
            content_lower = doc['content'].lower()

            # Check if question words are in document
            question_words = [w for w in question_lower.split() if len(w) > 3]
            matches = sum(1 for word in question_words if word in content_lower)

            if matches > 0 or question_lower in content_lower:
                # Find relevant sentences
                sentences = self._split_sentences(doc['content'])
                relevant = []

                for sentence in sentences[:10]:  # Check first 10 sentences
                    sentence_lower = sentence.lower()
                    if any(word in sentence_lower for word in question_words) or question_lower in sentence_lower:
                        relevant.append(sentence)

                if relevant:
                    relevant_content.append({
                        'filename': doc['filename'],
                        'sentences': relevant[:3]  # Top 3 sentences
                    })

        if not relevant_content:
            # No direct matches, give general response
            doc_names = ", ".join([doc['filename'] for doc in documents[:3]])
            return {
                "answer": f"📝 I have analyzed your documents ({doc_names}) but couldn't find specific information about '{question}'. Try asking about topics that might be in your documents.",
                "sources": self._create_sources(documents[:2])
            }

        # Build answer from relevant content
        answer = [f"🔍 **Information from your documents**\n"]

        for item in relevant_content[:2]:  # Limit to 2 documents
            answer.append(f"\n📄 **{item['filename']}:**")
            for i, sentence in enumerate(item['sentences'], 1):
                clean_sentence = re.sub(r'\s+', ' ', sentence).strip()[:200]
                answer.append(f"{i}. {clean_sentence}")

        return {
            "answer": "\n".join(answer),
            "sources": self._create_sources_from_relevant(relevant_content)
        }

    # Helper methods
    def _extract_term(self, question):
        """Extract term from definition question"""
        patterns = [
            (r'what is (.+?)\??', 1),
            (r'define (.+?)$', 1),
            (r'explain (.+?)$', 1),
            (r'meaning of (.+?)$', 1)
        ]

        for pattern, group in patterns:
            match = re.search(pattern, question.lower())
            if match:
                term = match.group(group).strip()
                # Remove trailing question words
                term = re.sub(r'\s+(?:in|according to|based on|from).*$', '', term)
                return term

        return ""

    def _split_sentences(self, text):
        """Split text into sentences"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _get_first_sentences(self, text, num=2):
        """Get first N meaningful sentences"""
        sentences = self._split_sentences(text)
        meaningful = []

        for sentence in sentences:
            if len(sentence.split()) > 5:  # Skip very short sentences
                meaningful.append(sentence)
                if len(meaningful) >= num:
                    break

        return meaningful

    def _extract_key_terms(self, text, num=3):
        """Extract key terms from text"""
        words = text.lower().split()

        # Remove common words
        common = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are',
                  'was', 'were'}
        content_words = [w for w in words if w not in common and len(w) > 3]

        # Simple frequency count
        from collections import Counter
        freq = Counter(content_words)

        return [word for word, _ in freq.most_common(num)]

    def _create_sources(self, documents):
        """Create sources from documents"""
        sources = []
        for doc in documents:
            preview = doc['content'][:150].replace('\n', ' ')
            if len(preview) >= 150:
                preview = preview + "..."
            sources.append({
                "content": preview,
                "source": doc['filename'],
                "type": "document"
            })
        return sources

    def _create_sources_from_sentences(self, sentences, filenames):
        """Create sources from sentences"""
        sources = []
        for sentence, filename in zip(sentences, filenames):
            preview = sentence[:150].replace('\n', ' ')
            if len(preview) >= 150:
                preview = preview + "..."
            sources.append({
                "content": preview,
                "source": filename,
                "type": "relevant content"
            })
        return sources

    def _create_sources_from_relevant(self, relevant_content):
        """Create sources from relevant content"""
        sources = []
        for item in relevant_content[:2]:
            if item['sentences']:
                preview = item['sentences'][0][:150].replace('\n', ' ')
                if len(preview) >= 150:
                    preview = preview + "..."
                sources.append({
                    "content": preview,
                    "source": item['filename'],
                    "type": "relevant content"
                })
        return sources


# Create instance
answer_generator = AnswerGenerator()