from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
import os
import re
import uuid
from werkzeug.utils import secure_filename
import datetime
from functools import wraps

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'ai-smart-file-assistant-internship'
app.config['UPLOAD_FOLDER'] = 'data/files'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# Create directories
os.makedirs('data/files', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)

print("\n" + "=" * 60)
print("🚀 AI SMART FILE ASSISTANT")
print("=" * 60)

# Initialize document analyzer
try:
    from document_analyzer import document_analyzer

    print("✅ Document analyzer initialized")
except Exception as e:
    print(f"⚠️ Document analyzer error: {e}")
    document_analyzer = None

# Initialize answer generator
try:
    from answer_generator import answer_generator

    print("✅ Answer generator initialized")
except Exception as e:
    print(f"⚠️ Answer generator error: {e}")
    answer_generator = None

print("=" * 60 + "\n")


# Login decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first', 'error')
            return redirect(url_for('signin'))
        return f(*args, **kwargs)

    return decorated_function


# Routes
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        errors = []

        if not all([first_name, last_name, email, password]):
            errors.append('All fields are required')

        if password != confirm_password:
            errors.append('Passwords do not match')

        # Simple password validation
        if len(password) < 8:
            errors.append('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', password):
            errors.append('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', password):
            errors.append('Password must contain at least one lowercase letter')
        if not re.search(r'\d', password):
            errors.append('Password must contain at least one digit')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('signup.html')

        # Create user session
        session['user_id'] = 1
        session['user_email'] = email
        session['user_name'] = f"{first_name} {last_name}"

        flash('Account created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('signup.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')

        if not email or not password:
            flash('Please enter both email and password', 'error')
            return render_template('signin.html')

        # Simple authentication (accept any in demo)
        session['user_id'] = 1
        session['user_email'] = email
        session['user_name'] = email.split('@')[0].title()

        flash('Welcome back!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('signin.html')


@app.route('/dashboard')
@login_required
def dashboard():
    # Create user object for template
    user_info = {
        'first_name': session.get('user_name', 'Demo').split()[0],
        'last_name': session.get('user_name', 'User').split()[-1] if ' ' in session.get('user_name', '') else 'User',
        'email': session.get('user_email', 'demo@example.com'),
        'pinecone_index': 'smart-analyzer',
        'get_full_name': lambda: session.get('user_name', 'Demo User')
    }

    return render_template('dashboard.html', user=user_info)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))


# API Endpoints
@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    print("\n" + "=" * 60)
    print("📤 FILE UPLOAD")
    print("=" * 60)

    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    user_id = session.get('user_id', 1)

    try:
        # Save file
        filename = secure_filename(file.filename)
        file_ext = filename.split('.')[-1].lower() if '.' in filename else 'txt'

        # Create user directory
        user_dir = f"data/files/{user_id}"
        os.makedirs(user_dir, exist_ok=True)

        # Save with unique name
        unique_name = f"{uuid.uuid4().hex}.{file_ext}"
        filepath = os.path.join(user_dir, unique_name)
        file.save(filepath)

        file_size = os.path.getsize(filepath)

        print(f"✅ File saved: {filename}")
        print(f"📁 Location: {filepath}")
        print(f"📊 Size: {file_size:,} bytes")

        return jsonify({
            'success': True,
            'file': {
                'name': filename,
                'type': file_ext.upper(),
                'size': f"{file_size / 1024:.1f} KB",
                'uploaded': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'processed': True,
                'message': f'✅ {filename} uploaded successfully! Ready for analysis.'
            }
        })

    except Exception as e:
        print(f"❌ Upload error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.json
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'error': 'Question is required'}), 400

    print("\n" + "=" * 60)
    print(f"💬 QUESTION: {question}")
    print("=" * 60)

    user_id = session.get('user_id', 1)

    try:
        # Get document analyzer
        from document_analyzer import document_analyzer

        # Get documents
        documents = document_analyzer.get_user_documents(user_id)

        if not documents:
            print("📭 No documents found")
            return jsonify({
                'success': True,
                'question': question,
                'answer': "📁 You haven't uploaded any documents yet. Please upload some documents first!",
                'sources': []
            })

        print(f"📚 Found {len(documents)} documents")

        # Initialize content extractor and explanation generator
        from content_extractor import content_extractor
        from explanation_generator import explanation_generator

        # Generate proper explanation
        result = explanation_generator.generate_explanation(question, documents, content_extractor)

        print(f"✅ Explanation generated: {len(result['answer']):,} characters")

        return jsonify({
            'success': True,
            'question': question,
            'answer': result['answer'],
            'sources': result['sources'],
            'ai_model': 'Content Analyzer'
        })

    except ImportError as e:
        print(f"❌ Import error: {e}")
        # Fallback to simple response
        return jsonify({
            'success': True,
            'question': question,
            'answer': f"I understand you're asking about '{question}'. Please ensure all required modules are installed.",
            'sources': []
        })
    except Exception as e:
        print(f"❌ Chat error: {e}")
        import traceback
        traceback.print_exc()

        return jsonify({
            'success': True,
            'question': question,
            'answer': f"I encountered an error while analyzing your documents. Please try asking a different question.",
            'sources': []
        })

@app.route('/api/files')
@login_required
def get_files():
    user_id = session.get('user_id', 1)
    user_dir = f"data/files/{user_id}"

    files = []
    if os.path.exists(user_dir):
        for filename in os.listdir(user_dir):
            filepath = os.path.join(user_dir, filename)
            if os.path.isfile(filepath):
                file_size = os.path.getsize(filepath)
                file_ext = filename.split('.')[-1].lower() if '.' in filename else 'txt'

                # Get modification time
                mtime = os.path.getmtime(filepath)
                upload_time = datetime.datetime.fromtimestamp(mtime)

                files.append({
                    'id': len(files) + 1,
                    'name': filename,
                    'type': file_ext.upper(),
                    'size': f"{file_size / 1024:.1f} KB",
                    'uploaded': upload_time.strftime('%Y-%m-%d %H:%M'),
                    'processed': True
                })

    print(f"📁 Serving {len(files)} files for user {user_id}")
    return jsonify({'files': files})


@app.route('/api/stats')
@login_required
def get_stats():
    user_id = session.get('user_id', 1)
    user_dir = f"data/files/{user_id}"

    file_count = 0
    total_size = 0

    if os.path.exists(user_dir):
        for filename in os.listdir(user_dir):
            filepath = os.path.join(user_dir, filename)
            if os.path.isfile(filepath):
                file_count += 1
                total_size += os.path.getsize(filepath)

    return jsonify({
        'user': {
            'name': session.get('user_name', 'Demo User'),
            'email': session.get('user_email', 'demo@example.com'),
            'index': 'file-analyzer'
        },
        'files': {
            'total': file_count,
            'total_size_mb': f"{total_size / (1024 * 1024):.2f}",
            'recent_uploads': file_count
        },
        'ai': {
            'status': '✅ Ready' if document_analyzer and answer_generator else '⚠️ Initializing',
            'documents_loaded': file_count
        }
    })


# Run the app
if __name__ == '__main__':
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"🌐 Running on: http://localhost:5000")
    print("👤 Demo login: Use any email/password")
    print("=" * 60 + "\n")

    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except:
        print("⚠️ Port 5000 busy, trying 5001...")
        app.run(debug=True, host='0.0.0.0', port=5001)