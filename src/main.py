import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import pytesseract
from PIL import Image, ImageTk, ImageEnhance, ImageFilter
import numpy as np
import cv2
import os
import io
import win32clipboard
from pdf2image import convert_from_path
import sys


class VietnameseOCRExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("Vietnamese OCR Extractor")
        self.root.geometry("1000x700")
        
        # Configure Tesseract (dynamic path handling)
        self.setup_tesseract()
        
        self.create_widgets()
        self.setup_menu()
        self.setup_drag_drop()
        self.setup_keybindings()
                
    def setup_tesseract(self):
        """Handle Tesseract path for both .exe and script modes"""
        try:
            if getattr(sys, 'frozen', False):
                # For packaged app
                tessdir = os.path.join(os.path.dirname(sys.executable), "Tesseract-OCR")
                if not os.path.exists(tessdir):
                    tessdir = 'F:\\Tesseract\\'
                os.environ["PATH"] += os.pathsep + tessdir
                pytesseract.pytesseract.tesseract_cmd = os.path.join(tessdir, "tesseract.exe")
            else:
                # For development
                pytesseract.pytesseract.tesseract_cmd = r'F:\Tesseract\tesseract.exe'
            
            # Verify Tesseract and Vietnamese language
            if 'vie' not in pytesseract.get_languages(config=''):
                messagebox.showwarning("Language Warning", 
                                     "Vietnamese language pack not installed for Tesseract")
        except Exception as e:
            messagebox.showerror("Tesseract Error", f"Failed to setup Tesseract:\n{str(e)}")
            self.root.quit()
    
    def setup_keybindings(self):
        self.root.bind('<Control-v>', self.paste_image)
        self.root.bind('<Control-V>', self.paste_image)
    
    def create_widgets(self):
        # Main frames
        self.left_frame = tk.Frame(self.root, width=450, height=650, bg='white')
        self.left_frame.pack_propagate(False)
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        self.right_frame = tk.Frame(self.root)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Image display panel
        self.img_label = tk.Label(
            self.left_frame, 
            bg='white', 
            text="Drag & Drop Image/PDF Here\nor\nCtrl+V to Paste Image",
            font=('Segoe UI', 12),
            compound='center'
        )
        self.img_label.pack(fill=tk.BOTH, expand=True)
        
        # Text box
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
            text="📁 Open Image/PDF",
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
            
            # Increase resolution if needed
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
        
    def process_file(self, filepath):
        """Process image or PDF file"""
        try:
            self.status_var.set("Processing...")
            self.root.update()
            
            if filepath.lower().endswith('.pdf'):
                self.process_pdf(filepath)
            else:
                self.process_image(Image.open(filepath))
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to process file:\n{str(e)}")
            self.status_var.set("Error processing file")
    
    def process_pdf(self, pdf_path):
        """Process all pages of PDF"""
        try:
            images = convert_from_path(pdf_path)
            if not images:
                messagebox.showwarning("Warning", "No pages found in PDF")
                return
            
            all_text = ""
            for i, img in enumerate(images):
                self.status_var.set(f"Processing page {i+1}/{len(images)}...")
                self.root.update()
                
                # Display first page thumbnail
                if i == 0:
                    self.display_image_thumbnail(img)
                
                # Process page
                processed_img = self.preprocess_image(img)
                text = pytesseract.image_to_string(processed_img, lang='vie', config='--oem 3 --psm 6')
                all_text += f"\n=== Page {i+1} ===\n{text}\n"
            
            self.text_box.delete(1.0, tk.END)
            self.text_box.insert(tk.END, all_text.strip())
            self.status_var.set(f"Processed {len(images)} pages")
            
        except Exception as e:
            raise Exception(f"PDF processing error: {str(e)}")
    
    def display_image_thumbnail(self, img):
        """Display thumbnail of image"""
        display_img = img.copy()
        display_img.thumbnail((600, 600))
        photo = ImageTk.PhotoImage(display_img)
        self.img_label.config(image=photo, text="")
        self.img_label.image = photo
    
    def process_image(self, img):
        """Process single image"""
        self.display_image_thumbnail(img)
        processed_img = self.preprocess_image(img)
        text = pytesseract.image_to_string(processed_img, lang='vie', config='--oem 3 --psm 6')
        self.text_box.delete(1.0, tk.END)
        self.text_box.insert(tk.END, text)
        self.status_var.set("OCR Complete")

    def open_image(self):
        """Handle file dialog opening"""
        filetypes = [
            ("Image/PDF files", "*.png *.jpg *.jpeg *.bmp *.tiff *.pdf"),
            ("All files", "*.*")
        ]
        filepath = filedialog.askopenfilename(filetypes=filetypes)
        if filepath:
            self.process_file(filepath)

    def paste_image(self, event=None):
        """Handle Ctrl+V pasting from clipboard"""
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                image_data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                image = Image.open(io.BytesIO(image_data))
                self.process_image(image)
            else:
                self.status_var.set("Clipboard has no image!")
        except Exception as e:
            messagebox.showerror("Paste Error", str(e))
        finally:
            win32clipboard.CloseClipboard()
        
    def setup_drag_drop(self):
        """Enable drag and drop functionality"""
        # For Windows
        if sys.platform == 'win32':
            try:
                self.root.drop_target_register(tk.DND_FILES)
                self.root.dnd_bind('<<Drop>>', self.handle_drop)
            except:
                # self.setup_crossplatform_dnd()
                return
        else:
            self.setup_crossplatform_dnd()

    def handle_drop(self, event):
        """Process dropped files (Windows native DND)"""
        filepath = event.data.strip('{}')
        self.process_dropped_file(filepath)

    def process_dropped_file(self, filepath):
        """Process files dropped on window"""
        if os.path.exists(filepath):
            self.process_file(filepath)
        else:
            messagebox.showerror("Error", "File not found!")

    def copy_text(self):
        """Copy text to clipboard"""
        text = self.text_box.get(1.0, tk.END).strip()
        if text:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.status_var.set("Text copied to clipboard!")
        else:
            self.status_var.set("No text to copy")
    
    def save_text(self):
        """Save text to file"""
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
                self.status_var.set(f"Text saved to {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Failed to save file:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = VietnameseOCRExtractor(root)
    root.mainloop()