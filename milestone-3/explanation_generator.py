import re


class ExplanationGenerator:
    """Generates proper explanations from extracted content"""

    def __init__(self):
        print("✅ Explanation Generator initialized")

    def generate_explanation(self, question, documents, content_extractor):
        """Generate proper explanation for a question"""
        if not documents:
            return {
                "answer": "📭 I don't see any uploaded documents yet. Please upload documents first!",
                "sources": []
            }

        question_lower = question.lower().strip()

        # Extract and analyze all documents
        all_content = ""
        document_contents = []

        for doc in documents:
            content = content_extractor.extract_meaningful_content(doc['filepath'], doc['type'])
            if content:
                all_content += content + "\n\n"
                document_contents.append({
                    'filename': doc['filename'],
                    'content': content
                })

        if not all_content:
            return {
                "answer": "❌ Could not extract content from documents. Please ensure documents contain readable text.",
                "sources": []
            }

        print(f"📊 Total content extracted: {len(all_content):,} characters")

        # Generate answer based on question type
        if 'what is' in question_lower or 'define' in question_lower or 'explain' in question_lower:
            return self._explain_term(question, all_content, document_contents, content_extractor)
        elif 'summary' in question_lower or 'summarize' in question_lower:
            return self._generate_summary(all_content, document_contents, content_extractor)
        elif 'what document' in question_lower or 'list' in question_lower:
            return self._list_documents(document_contents)
        else:
            return self._answer_general_question(question, all_content, document_contents, content_extractor)

    def _explain_term(self, question, all_content, document_contents, content_extractor):
        """Explain a specific term"""
        # Extract the term from question
        term = self._extract_term(question)

        if not term:
            term = question.replace('what is', '').replace('define', '').replace('explain', '').strip(' ?')

        print(f"🔍 Looking for information about: {term}")

        # Find relevant content
        relevant_sentences = []
        sources_info = []

        for doc_info in document_contents:
            content = doc_info['content']
            filename = doc_info['filename']

            # Find sentences about the term
            sentences = content_extractor.find_relevant_sections(content, term)

            if sentences:
                relevant_sentences.extend(sentences[:3])  # Top 3 from each doc
                sources_info.append({
                    'filename': filename,
                    'sentences': sentences[:2]
                })

        if not relevant_sentences:
            # Try to find definitions
            for doc_info in document_contents:
                definitions = content_extractor.extract_definitions(doc_info['content'])
                if definitions:
                    relevant_sentences.extend(definitions[:2])
                    sources_info.append({
                        'filename': doc_info['filename'],
                        'sentences': definitions[:2]
                    })

            if not relevant_sentences:
                # Still nothing, use key points
                for doc_info in document_contents:
                    key_points = content_extractor.extract_key_points(doc_info['content'], 2)
                    if key_points:
                        relevant_sentences.extend(key_points)
                        sources_info.append({
                            'filename': doc_info['filename'],
                            'sentences': key_points[:2]
                        })

        # Generate explanation
        if not relevant_sentences:
            return {
                "answer": f"❌ I couldn't find information about '{term}' in your documents. Try asking about a different topic.",
                "sources": []
            }

        # Build explanation
        explanation = [f"**Explanation of {term.title()}**\n"]
        explanation.append(f"Based on your documents, here's what I found:\n")

        # Add the most relevant sentences
        seen_sentences = set()
        for i, sentence in enumerate(relevant_sentences[:5], 1):
            # Clean and format sentence
            clean_sentence = re.sub(r'\s+', ' ', sentence).strip()

            # Avoid duplicates
            if clean_sentence.lower() not in seen_sentences:
                seen_sentences.add(clean_sentence.lower())
                explanation.append(f"{i}. {clean_sentence}")

        # Add source information
        if sources_info:
            explanation.append(f"\n📚 Sources: {len(sources_info)} document(s)")

        # Create sources
        sources = []
        for info in sources_info[:3]:
            if info['sentences']:
                sources.append({
                    "content": info['sentences'][0][:200] + ("..." if len(info['sentences'][0]) > 200 else ""),
                    "source": info['filename'],
                    "type": "relevant content"
                })

        return {
            "answer": "\n".join(explanation),
            "sources": sources
        }

    def _generate_summary(self, all_content, document_contents, content_extractor):
        """Generate document summary"""
        summary = ["📚 **Document Summary**\n"]

        for doc_info in document_contents[:3]:  # Summarize first 3
            filename = doc_info['filename']
            content = doc_info['content']

            # Extract key points
            key_points = content_extractor.extract_key_points(content, 3)

            summary.append(f"\n📄 **{filename}**")

            if key_points:
                for i, point in enumerate(key_points, 1):
                    clean_point = re.sub(r'\s+', ' ', point).strip()[:150]
                    summary.append(f"{i}. {clean_point}")
            else:
                # Fallback: first few sentences
                sentences = content_extractor._split_into_sentences(content)
                if sentences:
                    for i, sentence in enumerate(sentences[:2], 1):
                        clean_sentence = re.sub(r'\s+', ' ', sentence).strip()[:150]
                        summary.append(f"{i}. {clean_sentence}")

            # Word count
            word_count = len(content.split())
            summary.append(f"   📊 {word_count:,} words")

        if len(document_contents) > 3:
            summary.append(f"\n... and {len(document_contents) - 3} more documents.")

        summary.append("\n💡 Ask me specific questions about any section!")

        # Create sources
        sources = []
        for doc_info in document_contents[:2]:
            if doc_info['content']:
                preview = doc_info['content'][:150].replace('\n', ' ') + "..."
                sources.append({
                    "content": preview,
                    "source": doc_info['filename'],
                    "type": "document preview"
                })

        return {
            "answer": "\n".join(summary),
            "sources": sources
        }

    def _list_documents(self, document_contents):
        """List documents with meaningful previews"""
        answer = ["📁 **Uploaded Documents**\n"]

        for i, doc_info in enumerate(document_contents[:5], 1):
            filename = doc_info['filename']
            content = doc_info['content']

            # Extract first meaningful sentence
            sentences = content_extractor._split_into_sentences(content)
            preview = sentences[0][:100] + "..." if sentences else "Content extracted"

            word_count = len(content.split())

            answer.append(f"{i}. **{filename}**")
            answer.append(f"   Preview: {preview}")
            answer.append(f"   Size: {word_count:,} words")
            answer.append("")

        if len(document_contents) > 5:
            answer.append(f"... and {len(document_contents) - 5} more files.")

        return {
            "answer": "\n".join(answer),
            "sources": []
        }

    def _answer_general_question(self, question, all_content, document_contents, content_extractor):
        """Answer general questions"""
        # Find relevant content
        relevant_sentences = []
        sources_info = []

        for doc_info in document_contents:
            content = doc_info['content']
            sentences = content_extractor.find_relevant_sections(content, question)

            if sentences:
                relevant_sentences.extend(sentences[:3])
                sources_info.append({
                    'filename': doc_info['filename'],
                    'sentences': sentences[:2]
                })

        if not relevant_sentences:
            # Try broader search with individual words
            question_words = [w for w in question.lower().split() if len(w) > 3]

            for doc_info in document_contents:
                content = doc_info['content']
                all_sentences = content_extractor._split_into_sentences(content)

                matching_sentences = []
                for sentence in all_sentences[:20]:  # Check first 20 sentences
                    sentence_lower = sentence.lower()
                    matches = sum(1 for word in question_words if word in sentence_lower)

                    if matches >= max(1, len(question_words) * 0.3):
                        matching_sentences.append(sentence)

                if matching_sentences:
                    relevant_sentences.extend(matching_sentences[:2])
                    sources_info.append({
                        'filename': doc_info['filename'],
                        'sentences': matching_sentences[:2]
                    })

        # Generate answer
        if not relevant_sentences:
            # Give general document information
            doc_names = ", ".join([doc['filename'] for doc in document_contents[:3]])
            return {
                "answer": f"📝 I have analyzed {len(document_contents)} documents including {doc_names}. Please ask specific questions about the content, such as definitions or explanations of terms.",
                "sources": []
            }

        # Build answer
        answer = [f"**Answer to your question:**\n"]
        answer.append(f"Based on your documents:\n")

        seen_sentences = set()
        count = 1

        for info in sources_info[:3]:
            if info['sentences']:
                answer.append(f"\n📄 From **{info['filename']}**:")

                for sentence in info['sentences'][:2]:
                    clean_sentence = re.sub(r'\s+', ' ', sentence).strip()
                    if clean_sentence.lower() not in seen_sentences:
                        seen_sentences.add(clean_sentence.lower())
                        answer.append(f"{count}. {clean_sentence}")
                        count += 1

        # Create sources
        sources = []
        for info in sources_info[:2]:
            if info['sentences']:
                sources.append({
                    "content": info['sentences'][0][:200] + ("..." if len(info['sentences'][0]) > 200 else ""),
                    "source": info['filename'],
                    "type": "relevant content"
                })

        return {
            "answer": "\n".join(answer),
            "sources": sources
        }

    def _extract_term(self, question):
        """Extract term from question"""
        patterns = [
            (r'what is (.+?)\??', 1),
            (r'define (.+?)$', 1),
            (r'explain (.+?)$', 1),
            (r'meaning of (.+?)$', 1),
            (r'tell me about (.+?)$', 1)
        ]

        for pattern, group in patterns:
            match = re.search(pattern, question.lower())
            if match:
                term = match.group(group).strip()
                # Clean up the term
                term = re.sub(r'\s+(?:in|according to|based on|from|under).*$', '', term)
                return term

        return ""


# Create instance
explanation_generator = ExplanationGenerator()