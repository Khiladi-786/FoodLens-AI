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

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Python (Flask/FastAPI)
- **ML/NLP**: Scikit-learn, Pandas, OCR (Tesseract)
- **Database**: SQLite / Firebase (optional)
- **Deployment**: Localhost or Cloud (Heroku, Vercel)

---


## 📦 Installation

# Clone the repo
git clone https://github.com/akshayjith4/Revealio.git
cd Revealio

# (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set secret key environment variable
export FLASK_SECRET_KEY="your-production-secret-key"

# Run the app
python backend/app.py
