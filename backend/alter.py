import os
import sys
import pandas as pd
from gensim.models import Word2Vec

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load trained Word2Vec model
model_path = os.path.join(BASE_DIR, "ingredient_alternatives.model")
try:
    model = Word2Vec.load(model_path)
except Exception as e:
    print(f"Error loading model: {e}")
    sys.exit()

# Load CSV dictionary
file_path = os.path.join(BASE_DIR, "ingredient_alternative.csv")
try:
    df = pd.read_csv(file_path)
    df = df.dropna(subset=["Ingredient", "Alternative"])  # Remove missing values
    df["Ingredient"] = df["Ingredient"].str.lower().str.strip()
    df["Alternative"] = df["Alternative"].str.lower().str.strip()
    alternative_dict = dict(zip(df["Ingredient"], df["Alternative"]))
except Exception as e:
    print(f"Warning: Failed to load CSV alternatives: {e}")
    alternative_dict = {}

# Function to get ingredient alternative
def get_alternative(ingredient):
    ingredient = ingredient.lower().strip()

    # Check CSV dictionary first
    if ingredient in alternative_dict:
        return alternative_dict[ingredient]
    
    # Check Word2Vec model
    if ingredient in model.wv:
        return model.wv.most_similar(ingredient, topn=1)[0][0]
    
    return "No suitable alternative found."

if __name__ == "__main__":
    while True:
        ingredient = input("\nEnter an ingredient (or type 'exit' to quit): ").strip()
        if ingredient.lower() == "exit":
            print("Goodbye!")
            break

        alternative = get_alternative(ingredient)
        print(f"🔄 Alternative for '{ingredient}': {alternative}")
