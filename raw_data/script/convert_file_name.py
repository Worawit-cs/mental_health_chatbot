'''
This module is use for trans pdf to txt file directed by Wit
'''
import os
import pdfplumber
from ...path import get_path

BASE_DIR,PATH = get_path()
RAW_DATA_PATH = os.path.join(BASE_DIR, PATH["RAW_DATA_PATH"])



# Define directories
raw_data_dir = os.path.expanduser(f"{RAW_DATA_PATH}/pdf_data")
data_dir = os.path.expanduser(f"{RAW_DATA_PATH}/text_data")

# Ensure the output directory exists
os.makedirs(data_dir, exist_ok=True)

# Iterate through all PDF files in the raw_data directory
for filename in os.listdir(raw_data_dir):
    if filename.endswith(".pdf"):
        pdf_path = os.path.join(raw_data_dir, filename)
        txt_file = os.path.splitext(filename)[0] + ".txt"  # เปลี่ยนเป็น .txt
        txt_path = os.path.join(data_dir, txt_file)

        # Extract text from the PDF
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:  # ตรวจสอบว่า page_text ไม่ใช่ None
                    text += page_text + "\n\n"  # เพิ่มบรรทัดว่างระหว่างหน้า

        # Save the extracted text to a .md file
        with open(txt_path, "w", encoding="utf-8") as txt_file:
            txt_file.write(text)

        print(f"Converted {filename} to {txt_file}")
