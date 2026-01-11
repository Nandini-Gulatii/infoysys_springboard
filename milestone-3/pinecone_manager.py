import pinecone
import os
from dotenv import load_dotenv

load_dotenv()


class PineconeManager:
    def __init__(self):
        self.initialized = False
        self.api_key = os.getenv('PINECONE_API_KEY')

        if not self.api_key:
            print("❌ PINECONE_API_KEY not found")
            return

        # Try to detect environment
        self.environment = self.detect_environment()
        if not self.environment:
            return

        try:
            pinecone.init(api_key=self.api_key, environment=self.environment)
            self.initialized = True
            print(f"✅ Pinecone initialized in {self.environment}")

            # List indexes
            indexes = pinecone.list_indexes()
            print(f"   Available indexes: {indexes}")

        except Exception as e:
            print(f"❌ Failed to initialize Pinecone: {e}")

    def detect_environment(self):
        """Detect the correct Pinecone environment"""
        env_from_env = os.getenv('PINECONE_ENVIRONMENT')
        if env_from_env:
            return env_from_env

        # Common environments to try
        environments = [
            'us-east1-gcp',  # Most common for free tier
            'us-east-1-aws',  # AWS
            'us-west1-gcp',  # GCP West
            'us-west-2-aws',  # AWS West
        ]

        print("🔍 Detecting Pinecone environment...")
        for env in environments:
            try:
                pinecone.init(api_key=self.api_key, environment=env, pool_threads=1)
                pinecone.list_indexes()  # Test connection
                print(f"✅ Detected environment: {env}")
                pinecone.deinit()  # Clean up for proper init later
                return env
            except:
                continue

        print("❌ Could not detect Pinecone environment")
        print("Please set PINECONE_ENVIRONMENT in .env file")
        return None

    def create_user_index(self, index_name):
        """Create a new Pinecone index for a user"""
        if not self.initialized:
            return None, "Pinecone not initialized"

        try:
            # Clean index name
            index_name = index_name.lower().replace('_', '-')[:45]

            # Check if index exists
            if index_name in pinecone.list_indexes():
                print(f"✅ Index '{index_name}' already exists")
                return index_name, None

            print(f"Creating index '{index_name}'...")

            # For free tier, use serverless
            pinecone.create_index(
                name=index_name,
                dimension=384,
                metric='cosine',
                spec=pinecone.ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )

            print(f"✅ Index '{index_name}' created")
            return index_name, None

        except Exception as e:
            print(f"❌ Error creating index: {e}")
            return None, str(e)

    def index_exists(self, index_name):
        """Check if index exists"""
        if not self.initialized:
            return False

        try:
            index_name = index_name.lower().replace('_', '-')[:45]
            return index_name in pinecone.list_indexes()
        except:
            return False