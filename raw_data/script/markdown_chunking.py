import os
import glob
import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json

# Config
RAW_MD_DIR = os.path.expanduser("~/Documents/allProject/realProject/mental_health_chatbot/raw_data/markdown_data")
CHUNK_DIR = os.path.expanduser("~/Documents/allProject/realProject/mental_health_chatbot/data")
CHUNK_SIZE = 800      # จำนวนตัวอักษรต่อ chunk
CHUNK_OVERLAP = 200   # ตัวอักษรทับซ้อนระหว่าง chunks

os.makedirs(CHUNK_DIR, exist_ok=True)

def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_text(text)

# อ่านไฟล์ Markdown ทั้งหมด
for md_file in glob.glob(os.path.join(RAW_MD_DIR, "*.md")):
    filename = os.path.splitext(os.path.basename(md_file))[0]

    # ป้องกันไฟล์ชื่อซ้ำ
    filehash = hashlib.md5(md_file.encode()).hexdigest()[:6]
    filename = f"{filename}_{filehash}"

    with open(md_file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    # แบ่งเป็น chunks
    chunks = chunk_text(text)

    # เก็บ chunks เป็น JSON แทน (อ่านง่ายกว่า, ไม่เปลืองไฟล์)
    chunk_data = [{"id": i+1, "text": chunk} for i, chunk in enumerate(chunks)]
    out_path = os.path.join(CHUNK_DIR, f"{filename}.json")
    with open(out_path, "w", encoding="utf-8") as cf:
        json.dump(chunk_data, cf, ensure_ascii=False, indent=2)

    print(f"{md_file} -> {len(chunks)} chunks saved to {out_path}")
