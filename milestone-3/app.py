from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import re

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# ---- LangChain / AI imports (UPDATED & STABLE) ----
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Pinecone as PineconeVectorStore
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    Docx2txtLoader,
    BSHTMLLoader
)

import pinecone


# --------------------------------------------------

load_dotenv()

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            profile_picture TEXT,
            index_name TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect("users.db")

# ---------------- PASSWORD VALIDATION ----------------
def strong_password(p):
    return (
        len(p) >= 8 and
        re.search(r"[A-Z]", p) and
        re.search(r"[a-z]", p) and
        re.search(r"[0-9]", p) and
        re.search(r"[@$!%*?&]", p)
    )

# ---------------- PINECONE ----------------
pinecone.init(
    api_key=os.getenv("PINECONE_API_KEY"),
    environment="us-east-1"
)


embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

# ---------------- ROUTES ----------------
@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        f = request.form["first_name"]
        l = request.form["last_name"]
        e = request.form["email"]
        p = request.form["password"]

        if not strong_password(p):
            return "Password is weak"

        hashed = generate_password_hash(p)

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (first_name, last_name, email, password) VALUES (?, ?, ?, ?)",
            (f, l, e, hashed)
        )
        uid = cur.lastrowid

        index_name = f"{f.lower()}-{l.lower()}-{uid}"

        cur.execute(
            "UPDATE users SET index_name=? WHERE id=?",
            (index_name, uid)
        )

        conn.commit()
        conn.close()

        session["user_id"] = uid
        return redirect("/dashboard")

    return render_template("signup.html")

@app.route("/signin", methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        e = request.form["email"]
        p = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, password FROM users WHERE email=?", (e,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user[1], p):
            session["user_id"] = user[0]
            return redirect("/dashboard")

        return "Invalid credentials"

    return render_template("signin.html")

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT index_name FROM users WHERE id=?", (session["user_id"],))
    raw_index_name = cur.fetchone()[0]

    # sanitize index name for Pinecone
    index_name = raw_index_name.lower()
    index_name = index_name.replace("_", "-")
    index_name = "".join(c for c in index_name if c.isalnum() or c == "-")
    conn.close()

    if request.method == "POST":
        file = request.files["file"]
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # -------- FILE LOADING (FIXED) --------
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        elif filename.endswith(".txt"):
            loader = TextLoader(file_path, encoding="utf-8")
        elif filename.endswith(".docx"):
            loader = Docx2txtLoader(file_path)
        elif filename.endswith(".html"):
            loader = BSHTMLLoader(file_path)
        else:
            return "Unsupported file type"

        try:
            documents = loader.load()
        except Exception as e:
            return f"Error reading file. Please upload a UTF-8 encoded file.<br>{str(e)}"

        # -------- CHUNKING --------
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000,
            chunk_overlap=200
        )
        chunks = splitter.split_documents(documents)

        # -------- USER-SPECIFIC INDEX --------
        if index_name not in pinecone.list_indexes():
            pinecone.create_index(
                name=index_name,
                dimension=384,
                metric="cosine"
            )

        PineconeVectorStore.from_documents(
            chunks,
            embeddings,
            index_name=index_name
        )

        return "File uploaded and processed by AI successfully ✅"

    return render_template("dashboard.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
