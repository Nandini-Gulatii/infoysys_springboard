import json
from langchain_huggingface import HuggingFaceEmbeddings

# ---------- READ CHUNKS ----------
input_path = r"C:\Users\Akshat Gulati\PycharmProjects\infoysys_springboard\milestone-1\output-2_chunks.json"

with open(input_path, "r", encoding="utf-8") as f:
    chunks = json.load(f)

# ---------- LOAD EMBEDDING MODEL ----------
model_name = "sentence-transformers/all-MiniLM-L6-v2"
embeddings_model = HuggingFaceEmbeddings(model_name=model_name)

# ---------- CONVERT CHUNKS TO EMBEDDING ----------
output_data = []

for i, text in enumerate(chunks):
    embedding = embeddings_model.embed_query(text)
    output_data.append({
        "id": i,
        "text": text,
        "embedding": embedding
    })

# ---------- SAVE OUTPUT ----------
output_path = r"C:\Users\Akshat Gulati\PycharmProjects\infoysys_springboard\milestone-1\output-3_embeddings.json"

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, indent=4)

print("Task 3 Completed! Saved:", output_path)
