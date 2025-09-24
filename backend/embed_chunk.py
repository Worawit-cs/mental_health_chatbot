'''
this module is use for embed doc and store in data/chunk_index for using vector embedding
'''
import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

# Paths
CHUNK_JSON_DIR = "/home/worawit/Documents/allProject/realProject/mental_health_chatbot/data/chunk_json"
CHUNK_INDEX_DIR = "/home/worawit/Documents/allProject/realProject/mental_health_chatbot/data/chunk_index"
os.makedirs(CHUNK_INDEX_DIR, exist_ok=True)

# โหลดโมเดล Sentence-Transformers
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# รวบรวมทุก chunk
all_texts = []
all_metadatas = []

for file in os.listdir(CHUNK_JSON_DIR):
    if file.endswith(".json"):
        path = os.path.join(CHUNK_JSON_DIR, file)
        with open(path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
        for chunk in chunks:
            all_texts.append(chunk["text"])
            all_metadatas.append({"source": file, "chunk_id": chunk["id"]})

print(f"Total chunks: {len(all_texts)}")

# 1. สร้าง embeddings
embeddings = model.encode(all_texts, convert_to_numpy=True)

# 2. ทำ L2 Normalization
faiss.normalize_L2(embeddings)

# 3. สร้าง FAISS index ด้วย IndexFlatIP (Inner Product)
dim = embeddings.shape[1]
index = faiss.IndexFlatIP(dim) # เปลี่ยนจาก IndexFlatL2 เป็น IndexFlatIP

# เพิ่มเวกเตอร์ทั้งหมดเข้าสู่ดัชนี
index.add(embeddings)

# save FAISS index ลง chunk_index
index_path = os.path.join(CHUNK_INDEX_DIR, "chunks.index")
faiss.write_index(index, index_path)

# save metadata (optional)
metadata_path = os.path.join(CHUNK_INDEX_DIR, "metadata.json")
with open(metadata_path, "w", encoding="utf-8") as f:
    json.dump(all_metadatas, f, ensure_ascii=False, indent=2)

print(f"✅ Saved FAISS index to {index_path}")
print(f"✅ Saved metadata to {metadata_path}")