'''
This module is chunking markdoen file to Json directed by Wit
'''
import os
import glob
import hashlib
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json
import re

# Config
# TXT_DIR = os.path.expanduser("~/Documents/allProject/realProject/mental_health_chatbot/raw_data/text_data")
TXT_DIR = os.path.expanduser("/home/worawit/Documents/allProject/realProject/mental_health_chatbot/raw_data/text_example")
# CHUNK_DIR = os.path.expanduser("/home/worawit/Documents/allProject/realProject/mental_health_chatbot/data/text_chunk")
CHUNK_DIR = os.path.expanduser("/home/worawit/Documents/allProject/realProject/mental_health_chatbot/data/text_chunk_example")
CHUNK_SIZE = 800      # จำนวนตัวอักษรต่อ chunk
CHUNK_OVERLAP = 200   # ตัวอักษรทับซ้อนระหว่าง chunks

os.makedirs(CHUNK_DIR, exist_ok=True)

def clean_text(text):
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    
    # ลบ URL
    text = re.sub(r"http[s]?://\S+", "", text)
    
    # ลบตัวอักษรแปลก ๆ (ถ้ามี)
    text = re.sub(r"[^A-Za-z0-9ก-๙\s.,;:!?\-()\[\]\"']", " ", text)
    
    # normalize newlines
    # text = re.sub(r"\n+", "\n", text)
    
    return text

def chunk_text(text):
    text = clean_text(text)
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    return splitter.split_text(text)

# อ่านไฟล์ text ทั้งหมด
for txt_file in glob.glob(os.path.join(TXT_DIR, "*.txt")):
    filename = os.path.splitext(os.path.basename(txt_file))[0]

    # ป้องกันไฟล์ชื่อซ้ำ
    filehash = hashlib.md5(txt_file.encode()).hexdigest()[:6]
    filename = f"{filename}_{filehash}"

    with open(txt_file, "r", encoding="utf-8") as f:
        text = f.read().strip()

    # แบ่งเป็น chunks
    chunks = chunk_text(text)
    # print(chunks)

    # เก็บ chunks เป็น JSON แทน (อ่านง่ายกว่า, ไม่เปลืองไฟล์)
    chunk_data = [{"id": i+1,"source":filename ,"text": chunk} for i, chunk in enumerate(chunks)]
    out_path = os.path.join(CHUNK_DIR, f"{filename}.json")
    with open(out_path, "w", encoding="utf-8") as cf:
        json.dump(chunk_data, cf, ensure_ascii=False, indent=2)

    print(f"{txt_file} -> {len(chunks)} chunks saved to {out_path}")




# def chunk_text(text,size = CHUNK_SIZE,overlap=CHUNK_OVERLAP):
#     sents = re.split(r"(?<=[.!?])\s+", text.strip())
#     chunks, buf = [], ""
#     for s in sents:
#         if len(buf) + len(s) + 1 <= size:
#             buf = (buf + " " + s).strip()
#         else:
#             if buf:
#                 chunks.append(buf)
#             start = max(0, len(buf) - overlap)
#             carry = buf[start:]
#             buf = (carry + " " + s).strip()
#     if buf:
#         chunks.append(buf)
#     return chunks