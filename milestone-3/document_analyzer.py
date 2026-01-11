import os


class DocumentAnalyzer:
    def __init__(self):
        print("✅ Document Analyzer initialized")

    def get_user_documents(self, user_id):
        """Get documents for user"""
        user_dir = f"data/files/{user_id}"
        documents = []

        if os.path.exists(user_dir):
            print(f"📁 Scanning: {user_dir}")
            for filename in os.listdir(user_dir):
                filepath = os.path.join(user_dir, filename)
                if os.path.isfile(filepath):
                    file_ext = filename.split('.')[-1].lower() if '.' in filename else 'txt'

                    documents.append({
                        'filename': filename,
                        'filepath': filepath,
                        'type': file_ext,
                        'size': os.path.getsize(filepath)
                    })

                    print(f"  ✓ {filename} ({file_ext.upper()})")

        print(f"📚 Total: {len(documents)} documents")
        return documents


# Create instance
document_analyzer = DocumentAnalyzer()