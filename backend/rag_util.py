'''
This module is create query and Class RAG for retrieval Doc.
'''

import faiss
import json
from sentence_transformers import SentenceTransformer
import litellm
from config import MODEL

# ---- Config ----
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
# INDEX_PATH = "/home/worawit/Documents/allProject/realProject/mental_health_chatbot/data/text_chunk_index/chunks.index"            ##text_old_chunk_origin
INDEX_PATH = "/home/worawit/Documents/allProject/realProject/mental_health_chatbot/data/text_chunk_example_index/chunks.index"      ##text_new_chunk
# META_PATH = "/home/worawit/Documents/allProject/realProject/mental_health_chatbot/data/text_chunk_index/metadata.json"            ##text_old_chunk_origin
META_PATH = "/home/worawit/Documents/allProject/realProject/mental_health_chatbot/data/text_chunk_example_index/metadata.json"      ##text_new_chunk
TOP_K = 5
SIM_THRESHOLD = 0.3


class RAG:
    def __init__(self):
        # load embedding model
        self.model = SentenceTransformer(EMBED_MODEL)
        # load FAISS index
        self.index = faiss.read_index(INDEX_PATH)
        # load metadata
        with open(META_PATH, "r", encoding="utf-8") as f:
            self.metadatas = json.load(f)

    def retrieve(self, query: str, k: int = TOP_K):
        # embed query
        q_emb = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        
        # search FAISS
        D, I = self.index.search(q_emb, k)
        
        results = []
        for score, idx in zip(D[0], I[0]):
            meta = self.metadatas[idx]
            results.append({
                "score": float(score),
                "id": meta.get("chunk_id"),
                "source": meta.get("source"),
                "text": meta.get("text")
            })
        return results

    def answer(self, query: str, k: int = TOP_K, threshold: float = SIM_THRESHOLD):
        hits = self.retrieve(query, k=k)
        filtered = [h for h in hits if h["score"] >= threshold]
        # print("DEBUGGING:",filtered[0]["text"])
        
        if not filtered:
            return {"answer": "I couldn't find reliable context."}

        context = "\n\n".join([f"[{i+1}] {h['text']}" for i, h in enumerate(filtered)])
        # print("DEBUG Context:",context)
        prompt = f"Use only the context to answer. If not found, say so.\n\nContext:\n{context}\n\nQuestion: {query}"
        message = [{
            "role":"system","content":"You are a helpful assistant or mental health consulting. Answer using only provided context and you have kepp it in mood and tone.",
            "role":"user","content":f"{prompt}"
        }]

        r = litellm.completion(
            model=MODEL,
            messages=message,
            max_tokens=400,
            temperature=0.7
        )
        # print("DEBUGGING:",r.choices[0].message["content"])
        return {"answer": r.choices[0].message["content"], "hits": filtered}


# ---- ตัวอย่างการใช้งาน ----
if __name__ == "__main__":
    rag = RAG()
    query = "sucide"
    
    response = rag.answer(query)
    print("\n\nAnswer:", response["answer"])
    print("\nHits:")
    for h in response["hits"]:
        print(f"[{h['source']} - chunk {h['id']}] (score={h['score']:.2f})")
        # print(h["text"][:200], "...\n")
