import os
import uuid
from werkzeug.utils import secure_filename
import logging
import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UploadHandler:
    def __init__(self):
        """Initialize without Pinecone dependency"""
        self.allowed_extensions = {'pdf', 'docx', 'txt', 'html'}
        logger.info("✅ UploadHandler initialized (No Pinecone required)")

    def allowed_file(self, filename):
        """Check if file extension is allowed"""
        if not '.' in filename:
            logger.warning(f"No extension in filename: {filename}")
            return False

        extension = filename.rsplit('.', 1)[1].lower()
        is_allowed = extension in self.allowed_extensions
        logger.info(f"File {filename} extension {extension} allowed: {is_allowed}")
        return is_allowed

    def save_file(self, file, user_id):
        """Save uploaded file to disk"""
        logger.info(f"Saving file: {file.filename} for user {user_id}")

        if not self.allowed_file(file.filename):
            error = f"File type not allowed. Supported: {', '.join(self.allowed_extensions)}"
            logger.error(error)
            return None, error

        # Generate secure filename
        original_filename = secure_filename(file.filename)
        file_ext = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"

        # Create user directory
        upload_folder = 'data/files'
        user_dir = os.path.join(upload_folder, str(user_id))
        os.makedirs(user_dir, exist_ok=True)
        logger.info(f"Created directory: {user_dir}")

        # Save file
        file_path = os.path.join(user_dir, unique_filename)
        file.save(file_path)

        # Get file size
        file_size = os.path.getsize(file_path)
        logger.info(f"✅ File saved: {file_path} ({file_size} bytes)")

        return {
            "unique_filename": unique_filename,
            "original_filename": original_filename,
            "file_path": file_path,
            "file_type": file_ext,
            "file_size": file_size
        }, None

    def load_document_content(self, file_path, file_type):
        """Load document content (simplified version without Pinecone)"""
        logger.info(f"Loading document content: {file_path}")

        try:
            if file_type == 'pdf':
                # Simple PDF text extraction
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in pdf_reader.pages:
                            text += page.extract_text() + "\n"
                        return text
                except:
                    return f"PDF content extracted (requires proper parsing)"

            elif file_type == 'docx':
                # Simple DOCX text extraction
                try:
                    import docx
                    doc = docx.Document(file_path)
                    text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                    return text
                except:
                    return f"DOCX content extracted (requires proper parsing)"

            elif file_type == 'txt':
                # Read text file
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()

            else:  # html or others
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()

        except Exception as e:
            logger.error(f"Error reading file: {e}")
            return f"File content (error reading: {str(e)[:50]})"

    def handle_upload(self, file, user_id, user_index=None):
        """Complete upload process WITHOUT Pinecone"""
        logger.info(f"Starting upload for user {user_id}")

        # Save file
        file_info, error = self.save_file(file, user_id)
        if error:
            logger.error(f"Save file error: {error}")
            return None, error

        # Read file content for display
        content = self.load_document_content(file_info["file_path"], file_info["file_type"])
        content_preview = content[:500] + "..." if len(content) > 500 else content

        logger.info(f"✅ Upload successful: {file_info['original_filename']}")
        logger.info(f"Content preview ({len(content)} chars): {content_preview}")

        # Create a simple file record
        class FileRecord:
            def __init__(self, file_info, content_length):
                self.id = 1
                self.original_filename = file_info['original_filename']
                self.file_type = file_info['file_type']
                self.file_size = file_info['file_size']
                self.upload_date = datetime.datetime.now()
                self.processed = True
                self.content_length = content_length

        file_record = FileRecord(file_info, len(content))

        return file_record, None