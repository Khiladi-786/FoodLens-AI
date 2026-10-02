from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_cors import CORS
import sqlite3
import os
import json
import bcrypt
import base64
import uuid
import re
import time
import logging
from io import BytesIO
from PIL import Image
from werkzeug.utils import secure_filename
from ocr import extract_text  # OCR Function
from ml_lookup import check_allergen_risk  # ML Model for Risk Assessment
from alternative import get_alternative  # Alternative Food Recommender

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)
logger = logging.getLogger("foodlens_ai")

# Initialize Flask App
app = Flask(__name__, 
            static_folder=os.path.join(BASE_DIR, 'static'), 
            template_folder=os.path.join(BASE_DIR, 'templates'))

# 1. Secret Key Security
secret_key = os.environ.get('FLASK_SECRET_KEY')
if not secret_key:
    logger.warning("⚠️ FLASK_SECRET_KEY not found in environment. Using development fallback secret.")
    secret_key = 'dev_fallback_secret_key_foodlens_ai_2026'
app.secret_key = secret_key

CORS(app)

# 2. Session Cookie Security
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1')

# 3. File Upload & Database Configuration
DATABASE = os.path.join(BASE_DIR, 'users.db')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max limit

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 4. Security Headers
@app.after_request
def apply_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# 5. Database Connection Helper
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Access rows by column name
    return conn

# Initialize Database
def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                allergies TEXT,
                health_conditions TEXT,
                diet TEXT
            )
        ''')
        conn.commit()
    logger.info("Database initialized successfully.")

# 6. Rate Limiting for Authentication
login_attempts = {}

def is_rate_limited(key, max_attempts=5, window_seconds=300):
    now = time.time()
    if key in login_attempts:
        count, timestamp = login_attempts[key]
        if now - timestamp < window_seconds:
            if count >= max_attempts:
                return True
        else:
            login_attempts[key] = [0, now]
    return False

def record_failed_attempt(key, window_seconds=300):
    now = time.time()
    if key in login_attempts:
        count, timestamp = login_attempts[key]
        if now - timestamp < window_seconds:
            login_attempts[key] = [count + 1, timestamp]
        else:
            login_attempts[key] = [1, now]
    else:
        login_attempts[key] = [1, now]

def reset_login_attempts(key):
    login_attempts.pop(key, None)

# 7. File Cleanup Helper
def cleanup_old_uploads(max_age_seconds=3600):
    """Clean up uploaded image files older than 1 hour to prevent disk bloat."""
    try:
        now = time.time()
        for filename in os.listdir(UPLOAD_FOLDER):
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                if now - os.path.getmtime(filepath) > max_age_seconds:
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass
    except Exception as e:
        logger.warning(f"Error during upload folder cleanup: {e}")

# Allowed extension helper
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Allowed diets list
VALID_DIETS = {
    "None", "Ketogenic", "Low-Carb", "Low-Fat", "Paleo", "Vegan", 
    "Vegetarian", "Pescetarian", "DASH", "Mayo Clinic", "Mediterranean", 
    "Nordic", "Atkins", "Carnivore", "Gluten-Free"
}

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        allergies = request.form.getlist("allergies")
        health_conditions = request.form.getlist("health_conditions")
        diet = request.form.get("diet", "None").strip()

        # Input Validation
        if not username or len(username) < 3 or len(username) > 30 or not re.match(r'^[a-zA-Z0-9_.-]+$', username):
            flash("⚠️ Username must be 3-30 characters long and contain only letters, numbers, underscores, or hyphens.", "error")
            return render_template("register.html")

        if not email or not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            flash("⚠️ Please enter a valid email address.", "error")
            return render_template("register.html")

        if not password or len(password) < 8:
            flash("⚠️ Password must be at least 8 characters long.", "error")
            return render_template("register.html")

        if diet not in VALID_DIETS:
            diet = "None"

        # Format lists
        allergies_str = ", ".join([a.strip() for a in allergies if a != "None" and a.strip()]) or "None"
        health_conditions_str = ", ".join([h.strip() for h in health_conditions if h != "None" and h.strip()]) or "None"

        # Hash password securely
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        try:
            with get_db_connection() as conn:
                conn.execute(
                    "INSERT INTO users (username, email, password, allergies, health_conditions, diet) VALUES (?, ?, ?, ?, ?, ?)",
                    (username, email, hashed_password, allergies_str, health_conditions_str, diet),
                )
                conn.commit()
                logger.info(f"New user registered: {username}")
                flash("✅ Registration successful! You can now log in.", "success")
                return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("⚠️ Username or email already exists. Try a different one.", "error")

    return render_template("register.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        remote_ip = request.remote_addr or 'unknown_ip'
        rate_key = f"{remote_ip}:{username}"

        if is_rate_limited(rate_key):
            logger.warning(f"Rate limit triggered for login: {remote_ip}")
            flash("⚠️ Too many failed login attempts. Please wait 5 minutes before trying again.", "danger")
            return render_template('login.html'), 429

        with get_db_connection() as conn:
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user['password']):
            reset_login_attempts(rate_key)
            session.clear()  # Clear previous session data safely
            session['user'] = user['username']
            logger.info(f"Successful login for user: {username}")
            flash(f"✅ Welcome back, {user['username']}!", "success")
            return redirect(url_for('upload'))
        else:
            record_failed_attempt(rate_key)
            logger.warning(f"Failed login attempt for user input: {username}")
            flash("❌ Invalid Username or Password!", "danger")

    return render_template('login.html')

@app.route("/upload", methods=["GET", "POST"])
def upload():
    # 8. Authorization Check
    if "user" not in session:
        flash("⚠️ Please log in first!", "danger")
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("image")
        captured_image = request.form.get("captured-image")

        filepath = None

        if file and file.filename:
            if not allowed_file(file.filename):
                flash("⚠️ Invalid file format. Only PNG, JPG, and JPEG images are allowed.", "danger")
                return redirect(request.url)
            
            # Validate MIME / content using PIL
            try:
                img = Image.open(file.stream)
                img.verify()
                file.stream.seek(0)
            except Exception as img_err:
                logger.warning(f"Uploaded file content verification failed: {img_err}")
                flash("⚠️ The uploaded file is corrupted or not a valid image.", "danger")
                return redirect(request.url)

            # Generate unique UUID filename to prevent collisions and path traversal
            ext = file.filename.rsplit('.', 1)[1].lower()
            unique_name = f"upload_{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
            file.save(filepath)

        elif captured_image:
            try:
                # Handle Base64 Data URL safely
                if "," in captured_image:
                    base64_data = captured_image.split(",", 1)[1]
                else:
                    base64_data = captured_image

                image_data = base64.b64decode(base64_data)

                # Validate image content
                img = Image.open(BytesIO(image_data))
                img.verify()

                # Generate unique UUID filename for camera capture
                unique_name = f"capture_{uuid.uuid4().hex}.png"
                filepath = os.path.join(app.config["UPLOAD_FOLDER"], unique_name)
                with open(filepath, "wb") as img_file:
                    img_file.write(image_data)

            except Exception as cap_err:
                logger.warning(f"Captured camera payload verification failed: {cap_err}")
                flash("⚠️ Corrupted camera capture image. Please capture again.", "danger")
                return redirect(request.url)
        else:
            flash("⚠️ No file selected or captured!", "danger")
            return redirect(request.url)

        # Process OCR & Risk Analysis
        try:
            extracted_text, processed_path = extract_text(filepath)
            
            # Check for unreadable / empty OCR text
            if not extracted_text or not extracted_text.strip():
                logger.info(f"Empty OCR text extracted from file: {filepath}")
                flash("⚠️ We couldn't read enough text from this image. Try uploading a clearer ingredient label.", "warning")
                return redirect(url_for("upload"))

            username = session.get("user", "Guest")
            ml_result = check_allergen_risk(username, extracted_text)

            if "error" in ml_result:
                flash(ml_result["error"], "danger")
                return redirect(url_for("upload"))

            # Store in session securely for the logged-in user
            session["ml_result"] = json.dumps(ml_result)
            session["extracted_text"] = extracted_text

            # Trigger non-blocking file cleanup
            cleanup_old_uploads()

            flash("✅ Analysis completed successfully!", "success")
            return redirect(url_for("results"))

        except Exception as e:
            logger.error(f"Error processing upload analysis: {e}", exc_info=True)
            flash("⚠️ An error occurred while analyzing the image. Please try again with a clearer photo.", "danger")
            return redirect(url_for("upload"))

    return render_template("upload.html")

@app.route('/results')
def results():
    # Authorization Check
    if "user" not in session:
        flash("⚠️ Please log in first!", "danger")
        return redirect(url_for("login"))

    username = session.get('user')
    extracted_text = session.get('extracted_text')
    ml_result_str = session.get('ml_result')

    if not ml_result_str:
        flash("⚠️ No analysis found. Please upload an image.", "warning")
        return redirect(url_for('upload'))

    try:
        ml_result = json.loads(ml_result_str)
    except json.JSONDecodeError:
        logger.error("JSON decode error reading ml_result from session.")
        flash("⚠️ Error loading analysis results. Please scan again.", "warning")
        return redirect(url_for('upload'))

    analysis_results = ml_result.get("analysis_results", [])
    unsafe_ingredients = ml_result.get("unsafe_ingredients", [])

    # Store unsafe ingredients for recommendation route
    session['unsafe_ingredients'] = json.dumps(unsafe_ingredients)

    return render_template('result.html', 
                            analysis_results=analysis_results, 
                            extracted_text=extracted_text, 
                            username=username, 
                            unsafe_ingredients=unsafe_ingredients)

@app.route("/recommendation")
def recommendation():
    # Authorization Check
    if "user" not in session:
        flash("⚠️ Please log in first!", "danger")
        return redirect(url_for("login"))

    username = session.get("user")

    unsafe_json = session.get("unsafe_ingredients", "[]")
    try:
        unsafe_ingredients = json.loads(unsafe_json)
        unsafe_ingredients = [ing.lower().strip() for ing in unsafe_ingredients if ing]
    except Exception:
        unsafe_ingredients = []

    # Get alternatives safely
    try:
        recommendations = get_alternative(unsafe_ingredients)
    except Exception as err:
        logger.error(f"Error computing recommendations: {err}")
        recommendations = {ing: "No suitable alternative found." for ing in unsafe_ingredients}

    return render_template("recommendation.html", 
                            username=username, 
                            unsafe_ingredients=unsafe_ingredients, 
                            recommendations=recommendations)

@app.route('/logout')
def logout():
    session.clear()
    flash("👋 You have been logged out.", "info")
    return redirect(url_for('login'))

# 9. Error Handlers
@app.errorhandler(400)
def bad_request_error(e):
    logger.warning(f"400 Bad Request: {e}")
    return render_template('error.html', code=400, title="Bad Request", message="The request was invalid or malformed."), 400

@app.errorhandler(401)
def unauthorized_error(e):
    logger.warning(f"401 Unauthorized: {e}")
    return render_template('error.html', code=401, title="Unauthorized Access", message="Please log in to access this page."), 401

@app.errorhandler(403)
def forbidden_error(e):
    logger.warning(f"403 Forbidden: {e}")
    return render_template('error.html', code=403, title="Forbidden", message="You do not have permission to access this resource."), 403

@app.errorhandler(404)
def page_not_found(e):
    logger.info(f"404 Not Found: {request.url}")
    return render_template('error.html', code=404, title="Page Not Found", message="The page you requested could not be found."), 404

@app.errorhandler(413)
def request_entity_too_large(e):
    logger.warning(f"413 Entity Too Large attempt: {request.content_length}")
    return render_template('error.html', code=413, title="File Size Exceeded", message="The uploaded image exceeds the 16 MB limit. Please select a smaller file."), 413

@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500 Internal Error on {request.url}", exc_info=e)
    return render_template('error.html', code=500, title="Server Error", message="An unexpected error occurred. Our team has been notified."), 500

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
