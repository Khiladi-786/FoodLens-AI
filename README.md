# 🧠 FoodLens AI – Smart Ingredient Scanner & Health Risk Detection System

FoodLens AI ("See What's Inside. Eat Smarter.") is an intelligent food label scanner powered by machine learning that helps users make healthier choices by identifying potentially harmful ingredients and personalizing alerts based on individual health conditions or preferences.

---

## 🚀 Features

- 📷 **Scan Ingredients**: Use your device camera or upload images of food labels.
- 🧪 **Smart Ingredient Parsing**: Extract and analyze ingredients using OCR and NLP.
- 💡 **ML-Powered Risk Detection**: Classify ingredients based on predefined risk levels (e.g., high sugar, allergens).
- ⚙️ **Personalization**: Customize alerts based on user health profiles (e.g., diabetic, allergic).
- 📊 **Health Impact Summary**: Instantly view a visual summary of food safety and nutritional flags.

---

## 🛠️ Tech Stack

- **Frontend**: HTML5, CSS3 (Custom Design System with Dark/Light Mode), JavaScript
- **Backend**: Python 3.11+, Flask 3, Gunicorn
- **ML/NLP**: Gensim Word2Vec, VADER Sentiment Analysis, RapidFuzz, Pandas
- **OCR Engine**: Tesseract OCR (via PyTesseract)
- **Database**: SQLite3 (Persistent Disk mountable)
- **Deployment**: Render Web Service (Docker containerized)

---

## 📦 Local Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Khiladi-786/FoodLens-AI.git
   cd FoodLens-AI
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Tesseract OCR:**
   - **macOS:** `brew install tesseract`
   - **Ubuntu/Debian:** `sudo apt-get install tesseract-ocr tesseract-ocr-eng`
   - **Windows:** Download and install the Tesseract binary installer.

5. **Set environment variable & run locally:**
   ```bash
   export FLASK_SECRET_KEY="local-dev-secret-key"
   python3 wsgi.py
   ```
   Open `http://localhost:5000` in your web browser.

---

## 🚀 Render Deployment (Docker Web Service)

FoodLens AI is pre-configured for containerized deployment on Render using Docker:

1. Connect your GitHub repository (`Khiladi-786/FoodLens-AI`) to Render.
2. Create a **New Web Service** and select **Docker** runtime.
3. Configure Environment Variables in the Render Dashboard:
   - `FLASK_SECRET_KEY`: Generate a random secret (Render can auto-generate this).
   - `SESSION_COOKIE_SECURE`: `true` (enforces HTTPS cookies).
   - *(Optional)* `FOODLENS_DB_PATH`: `/var/data/users.db` (if attaching a Render Persistent Disk).
4. Click **Deploy Web Service**. Render will automatically build the `Dockerfile` with Tesseract OCR and launch Gunicorn.
