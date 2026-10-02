import pandas as pd
import chardet

file_path = "ingredient_alternative.csv"  # Change this to your actual CSV file name

# ✅ Detect encoding before reading
with open(file_path, "rb") as f:
    result = chardet.detect(f.read())
    detected_encoding = result["encoding"]

print(f"✅ Detected Encoding: {detected_encoding}")

try:
    # ✅ Read CSV with detected encoding
    df = pd.read_csv(file_path, encoding=detected_encoding, low_memory=False)

    # ✅ Remove only empty cells (not entire rows or columns)
    df = df.applymap(lambda x: x if pd.notna(x) else "")  # Replace NaN with an empty string

    # ✅ Save cleaned dataset
    cleaned_file_path = "cleaned_dataset.csv"
    df.to_csv(cleaned_file_path, index=False, encoding=detected_encoding)

    print(f"✅ Cleaning complete! Saved as '{cleaned_file_path}'")
except Exception as e:
    print(f"❌ Error: {e}")
