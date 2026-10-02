import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from gensim.models import Word2Vec

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ✅ Load trained Word2Vec model
model_path = os.path.join(BASE_DIR, "ingredient_alternatives.model")
try:
    model = Word2Vec.load(model_path)
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    sys.exit()

# ✅ Display basic model details
print("\n📊 **Model Summary**")
print(f"🔹 Vocabulary size: {len(model.wv.index_to_key)}")
print(f"🔹 Vector dimensions: {model.vector_size}")

# ✅ Function to get similar ingredients
def get_similar_ingredients(ingredient, topn=5):
    try:
        similar_words = model.wv.most_similar(ingredient, topn=topn)
        return [(word, round(score, 4)) for word, score in similar_words]
    except KeyError:
        return f"⚠️ '{ingredient}' not found in model vocabulary."

# ✅ Function to visualize word embeddings using PCA
def plot_embeddings(words):
    word_vectors = [model.wv[word] for word in words if word in model.wv]
    word_labels = [word for word in words if word in model.wv]

    if len(word_vectors) < 2:
        print("⚠️ Not enough valid words for visualization.")
        return

    # Reduce dimensions using PCA
    pca = PCA(n_components=2)
    reduced_vectors = pca.fit_transform(word_vectors)

    # Plot embeddings
    plt.figure(figsize=(8, 6))
    plt.scatter(reduced_vectors[:, 0], reduced_vectors[:, 1], color="blue")

    for word, coord in zip(word_labels, reduced_vectors):
        plt.annotate(word, (coord[0], coord[1]), fontsize=12)

    plt.title("Word2Vec Ingredient Embeddings (PCA)")
    plt.xlabel("PCA Component 1")
    plt.ylabel("PCA Component 2")
    plt.grid(True)
    plt.show()

# ✅ Interactive Analysis
while True:
    print("\n🔍 Enter an ingredient to analyze (or type 'exit' to quit):")
    ingredient = input("Ingredient: ").strip().lower()

    if ingredient == "exit":
        print("👋 Exiting analysis.")
        break

    similar_ingredients = get_similar_ingredients(ingredient)
    print(f"\n🥗 **Similar Ingredients for '{ingredient}':**")
    print(similar_ingredients)

    # ✅ Optional visualization (uncomment to use)
    words_to_plot = [ingredient] + [w[0] for w in similar_ingredients if isinstance(similar_ingredients, list)]
    plot_embeddings(words_to_plot)
