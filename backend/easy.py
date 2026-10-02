import os
from PIL import Image
import pytesseract 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Set the Tesseract path for Windows if running on Windows and executable exists
if os.name == 'nt' and os.path.exists(r'C:\Program Files\Tesseract-OCR\tesseract.exe'):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'   

# Load the image
image_path = os.path.join(BASE_DIR, '..', 'sample images', 'sample 15.jpg')
if os.path.exists(image_path):
    image = Image.open(image_path)
    # Perform OCR i.e. extract text from image
    extracted_text = pytesseract.image_to_string(image)
    print("Extracted Text:\n", extracted_text)
else:
    print(f"Sample image not found at: {image_path}")