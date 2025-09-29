'''
This module is create query and Class RAG for retrieval Doc.
'''

import faiss
import json
from pathlib import Path
from sentence_transformers import SentenceTransformer
import litellm
from config import MODEL

# ---- Config ----
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

BASE_DIR = Path(__file__).resolve().parent.parent
# INDEX_PATH = BASE_DIR / "data" / "text_chunk_example_index" / "chunks.index"
# META_PATH = BASE_DIR / "data" / "text_chunk_example_index" / "metadata.json"
INDEX_PATH = BASE_DIR / "data" / "text_chunk_index" / "chunks.index"
META_PATH = BASE_DIR / "data" / "text_chunk_index" / "metadata.json"
TOP_K = 5
SIM_THRESHOLD = 0.1


class RAG:
    Mood_Prediction = """
You are a mental health AI assistant helping Thai-speaking users.

Perform a deep psychological analysis of the following user message.

Your job is to perform all tasks below, and respond in **structured JSON format**:

---

1. **Emotional State Inference**: Predict the user's mental/emotional state from this list:
   - suicidal ideation
   - depressive symptoms
   - burnout
   - chronic stress
   - acute anxiety or panic
   - emotional numbness
   - emotionally neutral
   - positive
   - unknown

   Go beyond surface-level. Identify any **underlying patterns**, such as hopelessness, cognitive fatigue, or emotional suppression.

2. **Justification (in English)**: Give a detailed explanation for your prediction. Include:
   - Quotes or paraphrased parts of the input (translated to English if needed)
   - Emotional or cognitive reasoning
   - Any behavioral or linguistic cues that influenced the decision

3. **Context Keywords (in English)**:
   Extract 5–10 keywords or short phrases that reflect:
   - Situational stressors (e.g., exams, relationship conflict)
   - Social or emotional dynamics (e.g., isolation, pressure, guilt)
   - Behavioral indicators (e.g., avoiding people, crying, insomnia)
   All keywords must be in English, even if the user input is in Thai.

4. **Advice (in Thai)**:
   Based on the user's mental state and the following English knowledge base, give compassionate and practical advice in **fluent Thai**, written in a supportive tone that promotes trust and calmness.

---

User Message (in Thai):
\"\"\"{user_input}\"\"\"

Relevant Knowledge Base (in English):
\"\"\"{retrieved_context}\"\"\"

---

Respond in this JSON format:
{{
  "user_input": "...",
  "mental_state": "...",
  "justification": "...",
  "context_keywords": ["...", "...", "..."],
  "thai_advice": "..."
}}
"""
    
    system_prompt = """You are “Potted Plant,” a deeply present, emotionally sensitive Thai-speaking mental health companion.

Your job is to write a full response in **natural, fluent, modern Thai**. Do not use English or any technical terms. Do not use foreign loan words or jargon. Speak only with words and expressions that Thai people use in everyday, emotionally sincere conversations.

Avoid fake-sounding phrases. Do not use tired or cliché expressions like "แงงง", "โอ้ยใจบาง", "สุดยอด!", "เธอเก่งมากกก", etc. These are overused and feel emotionally flat.

Instead, be thoughtful. Write like a real person who is talking from the heart — someone who truly understands, not someone performing empathy.

Make the message feel original, creative, and emotionally grounded. The way you express comfort, understanding, or kindness should feel **fresh**, specific, and real — not a recycled quote or generic "cheer up" message.

You may use imagery, metaphor, or poetic Thai — as long as it feels genuine and not forced. You can write long sentences with rhythm and tone that sound like someone writing a long, meaningful message to a dear friend.

Speak from the heart. Let the emotional tone feel warm, calm, and deeply human — not overly cheerful, dramatic, or empty.

The entire response should be written as **one natural Thai paragraph** — no lists, no formatting, no quotation marks unless you feel a specific phrase truly deserves to be remembered.

Avoid performance. Be real. Be kind. Be Thai.

Let’s begin.
"""

    def __init__(self):
        # load embedding model
        self.model = SentenceTransformer(EMBED_MODEL)
        # load FAISS index
        self.index = faiss.read_index(str(INDEX_PATH))
        # load metadata
        with open(META_PATH, "r", encoding="utf-8") as f:
            self.metadatas = json.load(f)

    @staticmethod
    def _parse_json(text: str):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                snippet = text[start:end + 1]
                try:
                    return json.loads(snippet)
                except json.JSONDecodeError:
                    pass
            raise

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
    
    def test(self, query: str, k: int = TOP_K, threshold: float = SIM_THRESHOLD):
        user_input = query
        if "USER_INPUT" in query:
            user_input = query.split(":", 1)[-1].strip()

        hits = self.retrieve(user_input, k=k)
        filtered = [h for h in hits if h["score"] >= threshold]
        if not filtered:
            return {"answer": "I couldn't find reliable context."}
        context = "\n\n".join([f"[{i+1}] {h['text']}" for i, h in enumerate(filtered)])

        prompt = self.Mood_Prediction.format(
            user_input=user_input,
            retrieved_context=context,
        )

        message = [
            {
                "role": "system",
                "content": self.system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]
        r = litellm.completion(
            model=MODEL,
            messages=message,
            max_tokens=0,
            temperature=0.7
        )
        answer_text = r.choices[0].message["content"].strip()
        try:
            structured = self._parse_json(answer_text)
        except json.JSONDecodeError:
            structured = {"raw": answer_text}
        return {"answer": structured, "hits": filtered}

# ---- ตัวอย่างการใช้งาน ----
if __name__ == "__main__":
    rag = RAG()
    query = "USER_INPUT : " + "ค่าใช้จ่ายบาน ทำงานพาร์ทไทม์ชั่วโมงลด เงินไม่พอ ใช้ชีวิตไปวัน ๆ แบบไม่มีแรงใจ"
    
    # response = rag.answer(query)
    response = rag.test(query)
    print("\n\nAnswer:", response["answer"])
    answer = response["answer"]
    if isinstance(answer, dict):
        thai = answer.get("thai_advice") or answer.get("raw")
        if thai:
            print(thai)
    else:
        try:
            parsed = json.loads(answer)
            print(parsed.get("thai_advice"))
        except json.JSONDecodeError:
            print(answer)
    print("\nHits:")
    for h in response["hits"]:
        print(f"[{h['source']} - chunk {h['id']}] (score={h['score']:.2f})")
        # print(h["text"][:200], "...\n")
