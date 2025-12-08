from langchain_community.document_loaders import (
    TextLoader,
    BSHTMLLoader,
    UnstructuredWordDocumentLoader,
    PyPDFLoader
)

# ---------- Load All Files ----------

files = {
    "html": r"C:\\Users\\Akshat Gulati\\PycharmProjects\\infoysys_springboard\\data\\India Code_ Section Details.html",
    "txt": r"C:\\Users\\Akshat Gulati\\PycharmProjects\\infoysys_springboard\\data\\legal document (1).txt",
    "docx": r"C:\\Users\\Akshat Gulati\\PycharmProjects\\infoysys_springboard\\data\\THE INDIAN PENAL CODE.docx",
    "pdf": r"C:\\Users\\Akshat Gulati\\PycharmProjects\\infoysys_springboard\\data\\the_constitution_of_india.pdf",
}

loaders = [
    BSHTMLLoader(files["html"]),
    TextLoader(files["txt"], encoding="utf-8"),
    UnstructuredWordDocumentLoader(files["docx"]),
    PyPDFLoader(files["pdf"]),
]

all_text = ""

for loader in loaders:
    docs = loader.load()
    for doc in docs:
        all_text += doc.page_content + "\n\n"

# ---------- SAVE OUTPUT IN milestone-1 ----------
output_path = r"C:\Users\Akshat Gulati\PycharmProjects\infoysys_springboard\milestone-1\output-1.txt"

with open(output_path, "w", encoding="utf-8") as f:
    f.write(all_text)

print("\n\n  TASK COMPLETED — Extracted text saved to: \n", output_path)
