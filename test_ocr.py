import pytesseract
from PIL import Image

# Set Tesseract path (Windows only - adjust to your path)
pytesseract.pytesseract.tesseract_cmd = r'F:\Tesseract\tesseract.exe'

# Test with a Vietnamese image (you'll need to create one)
image_path = "vietnamese_test.png"

try:
    text = pytesseract.image_to_string(Image.open(image_path), lang='vie')
    print("Extracted Text:")
    print(text)
except Exception as e:
    print(f"Error: {e}")
    
    