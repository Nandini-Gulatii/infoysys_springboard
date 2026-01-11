import os
import re
from collections import Counter


class ContentExtractor:
    """Extracts and analyzes content from documents"""

    def __init__(self):
        print("✅ Content Extractor initialized")

    def extract_meaningful_content(self, filepath, file_type):
        """Extract meaningful content from document"""
        try:
            if file_type == 'docx':
                return self._extract_from_docx(filepath)
            else:
                return self._extract_from_text(filepath)
        except Exception as e:
            print(f"❌ Error extracting content: {e}")
            return ""

    def _extract_from_docx(self, filepath):
        """Extract content from DOCX file"""
        try:
            import docx

            # Load document
            doc = docx.Document(filepath)
            all_text = []

            # Extract paragraphs with meaningful content
            for para in doc.paragraphs:
                text = para.text.strip()
                if text and len(text) > 10:  # Skip very short paragraphs
                    all_text.append(text)

            # Extract tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        cell_text = cell.text.strip()
                        if cell_text:
                            row_text.append(cell_text)
                    if row_text:
                        all_text.append(" | ".join(row_text))

            content = "\n".join(all_text)

            # Clean up the content
            content = self._clean_content(content)

            print(f"📖 Extracted {len(content):,} characters from DOCX")
            return content

        except Exception as e:
            print(f"❌ DOCX extraction error: {e}")
            return ""

    def _extract_from_text(self, filepath):
        """Extract content from text file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            content = self._clean_content(content)
            print(f"📖 Extracted {len(content):,} characters from text file")
            return content

        except Exception as e:
            print(f"❌ Text extraction error: {e}")
            return ""

    def _clean_content(self, content):
        """Clean and normalize content"""
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)

        # Remove page numbers and headers
        content = re.sub(r'\bPage \d+\b', '', content)
        content = re.sub(r'\b\d+\s+of\s+\d+\b', '', content)

        # Ensure proper sentence endings
        content = re.sub(r'\.(\s*[a-z])', lambda m: '. ' + m.group(1).upper(), content)

        return content.strip()

    def find_relevant_sections(self, content, query):
        """Find sections relevant to the query"""
        if not content:
            return []

        query_lower = query.lower()
        sentences = self._split_into_sentences(content)

        relevant_sentences = []

        for sentence in sentences:
            sentence_lower = sentence.lower()

            # Check for exact match
            if query_lower in sentence_lower:
                relevant_sentences.append(sentence)
                continue

            # Check for word matches
            query_words = [w for w in query_lower.split() if len(w) > 3]
            matches = sum(1 for word in query_words if word in sentence_lower)

            if matches >= max(1, len(query_words) * 0.5):  # At least 50% match
                relevant_sentences.append(sentence)

        # Limit to most relevant
        return relevant_sentences[:10]

    def extract_definitions(self, content):
        """Extract definition-like sentences"""
        if not content:
            return []

        sentences = self._split_into_sentences(content)
        definitions = []

        definition_patterns = [
            r'is defined as',
            r'means',
            r'refers to',
            r'is known as',
            r'is called',
            r'is termed',
            r'definition of',
            r'means and includes'
        ]

        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(pattern in sentence_lower for pattern in definition_patterns):
                definitions.append(sentence)

        return definitions[:5]

    def extract_key_points(self, content, max_points=5):
        """Extract key points from content"""
        if not content:
            return []

        sentences = self._split_into_sentences(content)

        # Score sentences based on importance
        scored_sentences = []
        for i, sentence in enumerate(sentences):
            score = 0

            # Sentences with definition patterns get higher score
            definition_patterns = ['is defined as', 'means', 'refers to']
            if any(pattern in sentence.lower() for pattern in definition_patterns):
                score += 10

            # Sentences with numbers/sections get higher score
            if re.search(r'[Ss]ection \d+', sentence):
                score += 5

            # Sentences with legal terms get higher score
            legal_terms = ['shall', 'punishable', 'offence', 'liable', 'imprisonment']
            if any(term in sentence.lower() for term in legal_terms):
                score += 3

            # Earlier sentences get higher score
            score += max(0, 10 - i)  # First 10 sentences get bonus

            # Longer sentences (but not too long) get higher score
            word_count = len(sentence.split())
            if 10 <= word_count <= 50:
                score += 2

            scored_sentences.append((score, sentence))

        # Sort by score and take top
        scored_sentences.sort(reverse=True, key=lambda x: x[0])

        return [sentence for _, sentence in scored_sentences[:max_points]]

    def _split_into_sentences(self, text):
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]

    def analyze_document_structure(self, content):
        """Analyze document structure and extract sections"""
        if not content:
            return {}

        # Look for sections (like Section 300, Chapter II, etc.)
        sections = {}

        # Find section patterns
        section_patterns = [
            r'[Ss]ection (\d+[A-Z]*)\.?\s+(.+?)(?=[Ss]ection|\n\n|$)',
            r'[Cc]hapter ([IVXLCDM]+)\.?\s+(.+?)(?=[Cc]hapter|\n\n|$)',
            r'[Aa]rticle (\d+)\.?\s+(.+?)(?=[Aa]rticle|\n\n|$)'
        ]

        for pattern in section_patterns:
            matches = re.findall(pattern, content, re.DOTALL)
            for match in matches:
                section_num = match[0]
                section_content = match[1].strip()
                if len(section_content) > 20:
                    sections[f"Section {section_num}"] = section_content[:500]

        return sections


# Create instance
content_extractor = ContentExtractor()