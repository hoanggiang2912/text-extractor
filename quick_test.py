import tkinter as tk
from tkinter import filedialog, messagebox
import pytesseract
from PIL import Image

# Minimal setup
root = tk.Tk()
root.withdraw()  # Hide the main window

# Configure Tesseract (update path if needed)
pytesseract.pytesseract.tesseract_cmd = r'F:\Tesseract\tesseract.exe'

# Quick test function
def test_ocr():
    filepath = filedialog.askopenfilename(title="Select a Vietnamese image", filetypes=[("Image files", "*.png *.jpg *.jpeg")])
    if not filepath:
        return
    
    try:
        # Extract text (no GUI display)
        text = pytesseract.image_to_string(Image.open(filepath), lang='vie')
        
        # Show results in a popup
        messagebox.showinfo(
            "OCR Test Result",
            f"Extracted Text:\n\n{text if text else 'No text detected!'}"
        )
    except Exception as e:
        messagebox.showerror("Error", f"OCR failed:\n{str(e)}")

# Run the test
test_ocr()
root.destroy()