@echo off
echo Installing Tesseract OCR for Vietnamese...
curl -L "https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.3.20231005.exe" --output tesseract-installer.exe
start /wait tesseract-installer.exe /S
del tesseract-installer.exe
echo Tesseract OCR installed successfully.
pause