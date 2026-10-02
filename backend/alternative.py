import os
import sys
import pandas as pd
from gensim.models import Word2Vec

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Load trained Word2Vec model
model_path = os.path.join(BASE_DIR, "ingredient_alternatives.model")
try:
    model = Word2Vec.load(model_path)
except Exception as e:
    print(f"Error loading model: {e}")
    sys.exit()

# ✅ Load CSV dictionary for direct mapping
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

# ✅ Function to get ingredient alternative
def get_alternative(ingredients):
    if isinstance(ingredients, str):  
        ingredients = [ingredients]  # Convert single string to list

    alternatives = {}

    for ingredient in ingredients:
        ingredient = ingredient.lower().strip()

        # 🟢 Check CSV dictionary first
        if ingredient in alternative_dict:
            alternatives[ingredient] = alternative_dict[ingredient]
        else:
            # 🔵 Check Word2Vec model
            try:
                if ingredient in model.wv.key_to_index:
                    similar_ingredients = model.wv.most_similar(ingredient, topn=3)
                    alternatives[ingredient] = ", ".join([item[0] for item in similar_ingredients])
                else:
                    alternatives[ingredient] = "No suitable alternative found."
            except KeyError:
                alternatives[ingredient] = "No suitable alternative found."

    return alternatives

