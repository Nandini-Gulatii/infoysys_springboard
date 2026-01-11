# Test if imports work
print("Testing imports...")

try:
    from document_analyzer import document_analyzer

    print("✅ document_analyzer imported")

    # Test document reading
    user_id = 1
    docs = document_analyzer.get_user_documents(user_id)
    print(f"📚 Found {len(docs)} documents")

except Exception as e:
    print(f"❌ document_analyzer error: {e}")

try:
    from answer_generator import answer_generator

    print("✅ answer_generator imported")
except Exception as e:
    print(f"❌ answer_generator error: {e}")

print("\n✅ All imports tested!")