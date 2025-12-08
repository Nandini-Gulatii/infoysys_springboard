import json
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ---- READ INPUT (task-1 output) ----
input_path = r"C:\Users\Akshat Gulati\PycharmProjects\infoysys_springboard\milestone-1\output-1.txt"

with open(input_path, "r", encoding="utf-8") as f:
    full_text = f.read()

# ---- SPLIT INTO CHUNKS ----
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=100,
    length_function=len
)

chunks = text_splitter.split_text(full_text)

# ---- SAVE OUTPUT ----
output_path = r"C:\Users\Akshat Gulati\PycharmProjects\infoysys_springboard\milestone-1\output-2_chunks.json"

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(chunks, f, indent=4, ensure_ascii=False)

print(f"Task 2 Completed! {len(chunks)} chunks saved to {output_path}")
