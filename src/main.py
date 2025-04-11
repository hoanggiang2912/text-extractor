import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import pytesseract
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import numpy as np
import cv2
import os

class VietnameseOCRExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("Vietnamese OCR Extractor")
        self.root.geometry("1000x700")
        
        # Configure Tesseract
        pytesseract.pytesseract.tesseract_cmd = r'F:\Tesseract\tesseract.exe'
        
        self.create_widgets()
        self.style_widgets()
        self.setup_menu()
    
    def create_widgets(self):
        # Main frames
        self.left_frame = tk.Frame(self.root, width=450, height=650, bg='white')
        self.left_frame.pack_propagate(False)
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.right_frame = tk.Frame(self.root)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Image display
        self.img_label = tk.Label(self.left_frame, bg='white')
        self.img_label.pack(fill=tk.BOTH, expand=True)
        
        # Text box with line numbers
        self.text_frame = tk.Frame(self.right_frame)
        self.text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.text_box = scrolledtext.ScrolledText(
            self.text_frame, 
            wrap=tk.WORD, 
            font=('Consolas', 11),
            undo=True
        )
        self.text_box.pack(fill=tk.BOTH, expand=True)
        
        # Control panel
        self.control_frame = tk.Frame(self.right_frame)
        self.control_frame.pack(fill=tk.X, pady=5)
        
        self.open_btn = ttk.Button(
            self.control_frame, 
            text="📁 Open Image", 
            command=self.open_image
        )
        self.open_btn.pack(side=tk.LEFT, padx=5)
        
        self.copy_btn = ttk.Button(
            self.control_frame, 
            text="⎘ Copy Text", 
            command=self.copy_text
        )
        self.copy_btn.pack(side=tk.LEFT, padx=5)
        
        self.save_btn = ttk.Button(
            self.control_frame, 
            text="💾 Save Text", 
            command=self.save_text
        )
        self.save_btn.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        self.status_bar = tk.Label(
            self.right_frame, 
            textvariable=self.status_var,
            bd=1, 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.status_bar.pack(fill=tk.X)
    
    def style_widgets(self):
        style = ttk.Style()
        style.configure('TButton', 
        font=('Segoe UI', 10),  # Tuple format here
        padding=8)
        
        style.map('TButton',
                foreground=[('active', '#ffffff')],
                background=[('active', '#45a049')])
        
        self.root.option_add('*Font', ('Segoe UI', 10))  # Corrected line
    
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_image)
        file_menu.add_command(label="Save", command=self.save_text)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        self.root.config(menu=menubar)
    
    def preprocess_image(self, img):
        """Enhance image for better OCR results"""
        try:
            # Convert to grayscale
            img = img.convert('L')
            
            # Increase resolution (minimum 300 DPI effective)
            if img.size[0] < 1000 or img.size[1] < 1000:
                new_size = (int(img.size[0] * 1.5), int(img.size[1] * 1.5))
                img = img.resize(new_size, Image.LANCZOS)
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)
            
            # Denoise
            img_array = np.array(img)
            img_array = cv2.fastNlMeansDenoising(img_array, None, 10, 7, 21)
            img = Image.fromarray(img_array)
            
            return img
        except Exception as e:
            raise Exception(f"Image processing error: {str(e)}")
    
    def open_image(self):
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff"),
            ("All files", "*.*")
        ]
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        
        if not filepath:
            return
        
        try:
            self.status_var.set("Processing...")
            self.root.update()
            
            # Load original image
            original_img = Image.open(filepath)
            
            # Display thumbnail
            display_img = original_img.copy()
            display_img.thumbnail((600, 600))
            photo = ImageTk.PhotoImage(display_img)
            self.img_label.config(image=photo)
            self.img_label.image = photo
            
            # Preprocess and OCR
            processed_img = self.preprocess_image(original_img)
            text = pytesseract.image_to_string(
                processed_img, 
                lang='vie', 
                config='--oem 3 --psm 6'
            )
            
            self.text_box.delete(1.0, tk.END)
            self.text_box.insert(tk.END, text)
            self.status_var.set(f"Ready - {filepath}")
            
        except Exception as e:
            messagebox.showerror(
                "OCR Error",
                f"Failed to process image:\n{str(e)}"
            )
            self.status_var.set("Error processing image")
    
    def copy_text(self):
        text = self.text_box.get(1.0, tk.END).strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_var.set("Text copied to clipboard!")
        else:
            self.status_var.set("No text to copy")
    
    def save_text(self):
        text = self.text_box.get(1.0, tk.END).strip()
        if not text:
            messagebox.showwarning("Empty Text", "No text to save")
            return
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.status_var.set(f"Text saved to {filepath}")
            except Exception as e:
                messagebox.showerror(
                    "Save Error",
                    f"Failed to save file:\n{str(e)}"
                )

if __name__ == "__main__":
    root = tk.Tk()
    app = VietnameseOCRExtractor(root)
    root.mainloop()