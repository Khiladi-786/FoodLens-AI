import os
import pandas as pd
from gensim.models import Word2Vec
import random
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Load CSV file and preprocess
file_path = os.path.join(BASE_DIR, "ingredient_alternative.csv")
try:
    df = pd.read_csv(file_path)
    df = df.dropna(subset=["Ingredient", "Alternative"])  # Remove missing values
    df["Ingredient"] = df["Ingredient"].str.lower().str.strip()
    df["Alternative"] = df["Alternative"].str.lower().str.strip()
    alternative_dict = dict(zip(df["Ingredient"], df["Alternative"]))
    print("✅ CSV alternatives loaded successfully!")
except Exception as e:
    print(f"❌ Error loading CSV: {e}")
    exit()

# ✅ Expand training sentences
sentences = []
for _, row in df.iterrows():
    ingredient, alternative = row["Ingredient"], row["Alternative"]
    
    # Basic substitution sentences
    sentences.append([ingredient, alternative])  
    sentences.append(["use", alternative, "instead", "of", ingredient])  
    sentences.append([alternative, "is", "a", "substitute", "for", ingredient])  

    # 🔥 Context-based substitutions
    category_pairs = [
        ("dairy", "non-dairy"),
        ("meat", "plant-based"),
        ("sugar", "sugar-free"),
        ("gluten", "gluten-free"),
        ("oil", "healthy oil"),
    ]
    
    for cat1, cat2 in category_pairs:
        if cat1 in ingredient:
            sentences.append([ingredient, "is", cat1, "but", alternative, "is", cat2])
        if cat2 in alternative:
            sentences.append([alternative, "is", "a", cat2, "option", "for", ingredient])

    # 🔥 Randomized ingredient substitution (boosts variation)
    random_ingredient = random.choice(df["Ingredient"].tolist())
    if random_ingredient != ingredient:
        sentences.append([ingredient, "is similar to", random_ingredient])

# ✅ Train Word2Vec model (Improved parameters)
model = Word2Vec(
    sentences, 
    vector_size=50,  # 🔥 Reduced for better performance
    window=5,        # 🔥 Increased for better context learning
    min_count=1, 
    workers=4
)

# ✅ Save model
model.save(os.path.join(BASE_DIR, "ingredient_alternatives.model"))
print("✅ Model training complete! Saved as 'ingredient_alternatives.model'")

# ✅ Evaluate model accuracy using cosine similarity
def evaluate_model(model, alternative_dict):
    correct = 0
    total = 0
    similarities = []

    for ingredient, expected_alternative in alternative_dict.items():
        try:
            # Ensure both words exist in the vocabulary
            if ingredient in model.wv and expected_alternative in model.wv:
                total += 1
                
                # Compute cosine similarity
                similarity = cosine_similarity(
                    [model.wv[ingredient]], 
                    [model.wv[expected_alternative]]
                )[0][0]
                
                similarities.append(similarity)
                
                # Consider it correct if similarity is above 0.5 (adjust if needed)
                if similarity > 0.5:
                    correct += 1

        except KeyError:
            pass  # Ignore missing words in vocabulary

    if total == 0:
        return 0.0  # Avoid division by zero
    
    accuracy = (correct / total) * 100
    avg_similarity = np.mean(similarities) * 100 if similarities else 0.0
    return accuracy, avg_similarity

# ✅ Compute accuracy
accuracy, avg_similarity = evaluate_model(model, alternative_dict)

