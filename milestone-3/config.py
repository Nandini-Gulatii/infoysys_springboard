import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-for-internship')

    # Database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload
    UPLOAD_FOLDER = 'data/files'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'html'}

    # API Keys
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')

    # Try to detect correct environment
    env_from_file = os.getenv('PINECONE_ENVIRONMENT')
    if env_from_file:
        PINECONE_ENVIRONMENT = env_from_file
    else:
        # Default to most common
        PINECONE_ENVIRONMENT = 'us-east1-gcp'

    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Models
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 100

    @classmethod
    def test_pinecone(cls):
        """Test Pinecone connection"""
        if not cls.PINECONE_API_KEY:
            return False, "No PINECONE_API_KEY"

        try:
            import pinecone
            pinecone.init(api_key=cls.PINECONE_API_KEY, environment=cls.PINECONE_ENVIRONMENT)
            indexes = pinecone.list_indexes()
            return True, f"Connected to {cls.PINECONE_ENVIRONMENT}. Indexes: {indexes}"
        except Exception as e:
            return False, str(e)