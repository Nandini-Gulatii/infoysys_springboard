import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("PINECONE DIAGNOSTIC TOOL")
print("=" * 70)

# Get API key
api_key = os.getenv('PINECONE_API_KEY')
if not api_key:
    print("❌ ERROR: PINECONE_API_KEY not found in .env file")
    print("Please add: PINECONE_API_KEY=your-key-here")
    sys.exit(1)

print(f"✅ API Key found: {api_key[:15]}...{api_key[-10:]}")

# Test if key is valid format
if not api_key.startswith('pcsk_') and not api_key.startswith('pc-'):
    print("⚠️ WARNING: API key format looks unusual")
    print("Pinecone keys usually start with 'pcsk_' or 'pc-'")

# Test internet connection
print("\n1. Testing internet connection...")
try:
    response = requests.get("https://www.google.com", timeout=5)
    print("✅ Internet connection: OK")
except:
    print("❌ Internet connection: FAILED")
    print("Check your network connection")
    sys.exit(1)

# Try to extract environment from API key
print("\n2. Analyzing API key...")
if 'pinecone.io' in api_key:
    # Sometimes keys include the URL
    print("Key appears to contain URL")
    if 'us-east1-gcp' in api_key:
        suggested_env = 'us-east1-gcp'
    elif 'us-east-1-aws' in api_key:
        suggested_env = 'us-east-1-aws'
    else:
        suggested_env = 'us-east1-gcp'  # Default
else:
    suggested_env = 'us-east1-gcp'

print(f"Suggested environment: {suggested_env}")

# Test Pinecone connection
print("\n3. Testing Pinecone connection...")

# Common environments to try (in order of likelihood)
environments = [
    'us-east1-gcp',  # Most common (GCP)
    'us-east-1-aws',  # AWS
    'gcp-starter',  # Old free tier
    'aws-starter',  # Old free tier
    'us-west1-gcp',  # GCP West
    'us-west-2-aws',  # AWS West
    'eu-west1-aws',  # AWS Europe
    'asia-southeast1-gcp',  # GCP Asia
]

success = False
working_env = None

for env in environments:
    try:
        print(f"\n   Trying {env}...")

        # Test with direct API call first
        test_url = f"https://controller.{env}.pinecone.io/databases"
        headers = {
            'Api-Key': api_key,
            'Content-Type': 'application/json'
        }

        # Try API call
        response = requests.get(test_url, headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"   ✅ {env}: Connection successful!")
            working_env = env
            success = True

            # Try to list indexes
            import pinecone

            pinecone.init(api_key=api_key, environment=env)
            indexes = pinecone.list_indexes()
            print(f"   📊 Indexes found: {indexes}")

            if indexes:
                # Test one index
                index = pinecone.Index(indexes[0])
                stats = index.describe_index_stats()
                print(f"   📈 Index stats: {stats}")

            break
        else:
            print(f"   ❌ {env}: Failed (HTTP {response.status_code})")

    except requests.exceptions.ConnectionError:
        print(f"   ❌ {env}: Connection refused")
    except Exception as e:
        error_msg = str(e)
        if "NameResolutionError" in error_msg or "getaddrinfo" in error_msg:
            print(f"   ❌ {env}: Invalid domain")
        else:
            print(f"   ❌ {env}: {error_msg[:50]}...")

if success:
    print("\n" + "=" * 70)
    print("✅ SUCCESS! Pinecone is working!")
    print(f"✅ Working environment: {working_env}")
    print("\nAdd this to your .env file:")
    print(f"PINECONE_ENVIRONMENT={working_env}")
    print("=" * 70)
else:
    print("\n" + "=" * 70)
    print("❌ FAILED to connect to Pinecone")
    print("\nPossible solutions:")
    print("1. Check if API key is valid at https://app.pinecone.io")
    print("2. Try a different API key")
    print("3. Use free tier: https://www.pinecone.io/start/")
    print("4. Use local alternative (ChromaDB) instead")
    print("=" * 70)

    # Offer to use local alternative
    use_local = input("\nUse local ChromaDB instead? (y/n): ")
    if use_local.lower() == 'y':
        print("\nSwitching to local ChromaDB...")
        # We'll set this up next