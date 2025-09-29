'''
This module defines utilities for running Retrieval-Augmented Generation (RAG)
for the mental health chatbot.
'''

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import faiss
import litellm
from sentence_transformers import SentenceTransformer

from config import MODEL

# ---- Config ----
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_PATH = BASE_DIR / "data" / "text_chunk_index" / "chunks.index"
META_PATH = BASE_DIR / "data" / "text_chunk_index" / "metadata.json"
TOP_K = 5
SIM_THRESHOLD = 0.15


class RAG:
    ANALYZE_PROMPT = """
You are a bilingual (Thai/English) mental-health analyst. A Thai-speaking student just
shared their feelings. Infer their state and prepare search hints for a knowledge base
covering topics such as: depression screening (PHQ-9), anxiety screening (GAD-7),
mindfulness interventions, university mental-health policies, WHO suicide prevention
strategy, and digital self-help programmes.

Return ONLY JSON with these keys:
{
  "mental_state": "one of: suicidal ideation | depressive symptoms | anxiety or panic |
                   stress or burnout | emotionally neutral | positive state | unknown",
  "justification": "short English rationale referencing cues (quote or paraphrase)",
  "retrieval_keywords": ["english keyword", ... up to 8 items],
  "retrieval_query": "1 concise English query combining the most relevant resources"
}

Guidelines:
- Translate important Thai phrases to English when justifying.
- retrieval_keywords should favour clinical or topic terms that match the knowledge
  base, e.g. "PHQ-9", "GAD-7 scoring", "mindfulness program", "university policy".
- retrieval_query must be suitable for vector search; pick terms that point to the
  best-matching documents (e.g. "PHQ-9 depression severity guidance").
"""

    ADVICE_PROMPT = """
Context for your reply:
  User Input (Thai):
\"\"\"{user_input}\"\"\"
  Analysis Summary:
    mental_state: {mental_state}
    justification: {justification}
    knowledge_focus: {knowledge_focus}
    retrieval_keywords: {keywords}
  Retrieved Knowledge (English):
\"\"\"{retrieved_context}\"\"\"

Respond with JSON exactly in this form:
{{
  "mental_state": "{mental_state}",
  "justification": "{justification}",
  "context_keywords": {keywords},
  "thai_advice": "..."  // single-paragraph Thai following the system style
}}
"""

    def __init__(self) -> None:
        self.model = SentenceTransformer(EMBED_MODEL)
        self.index = faiss.read_index(str(INDEX_PATH))
        with open(META_PATH, "r", encoding="utf-8") as f:
            self.metadatas = json.load(f)

    @staticmethod
    def _parse_json(payload: str) -> Dict[str, Any]:
        try:
            return json.loads(payload)
        except json.JSONDecodeError:
            start = payload.find("{")
            end = payload.rfind("}")
            if start != -1 and end != -1 and end > start:
                snippet = payload[start : end + 1]
                return json.loads(snippet)
            raise

    @staticmethod
    def _normalise_keywords(data: Dict[str, Any]) -> List[str]:
        keywords = data.get("retrieval_keywords") or data.get("context_keywords") or []
        if isinstance(keywords, list):
            return [k.strip() for k in keywords if isinstance(k, str) and k.strip()]
        return []

    def _call_llm(self, messages: List[Dict[str, str]], *, max_tokens: int, temperature: float) -> str:
        response = litellm.completion(
            model=MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message["content"].strip()

    def analyze_user_input(self, user_input: str) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": "You extract mental health signals."},
            {"role": "user", "content": f"{self.ANALYZE_PROMPT}\n\nUser message:\n{user_input}"},
        ]
        payload = self._call_llm(messages, max_tokens=350, temperature=0.1)
        analysis = self._parse_json(payload)
        if "retrieval_query" not in analysis or not analysis["retrieval_query"].strip():
            keywords = self._normalise_keywords(analysis)
            analysis["retrieval_query"] = " ".join(keywords[:4]) or user_input
        return analysis

    def _build_search_query(self, analysis: Dict[str, Any], user_input: str) -> str:
        terms: List[str] = []
        terms.extend(self._normalise_keywords(analysis))
        if analysis.get("retrieval_query"):
            terms.append(analysis["retrieval_query"])
        terms.append(analysis.get("mental_state", ""))
        query = " ".join(t for t in terms if isinstance(t, str) and t.strip()).strip()
        return query or user_input

    def retrieve(self, query: str, k: int = TOP_K) -> List[Dict[str, Any]]:
        q_emb = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True)
        D, I = self.index.search(q_emb, k)
        results = []
        for score, idx in zip(D[0], I[0]):
            meta = self.metadatas[idx]
            results.append(
                {
                    "score": float(score),
                    "id": meta.get("chunk_id"),
                    "source": meta.get("source"),
                    "text": meta.get("text"),
                }
            )
        return results

    def test(self, query: str, k: int = TOP_K, threshold: float = SIM_THRESHOLD) -> Dict[str, Any]:
        user_input = query.split(":", 1)[-1].strip() if "USER_INPUT" in query else query
        analysis = self.analyze_user_input(user_input)
        search_query = self._build_search_query(analysis, user_input)

        hits = self.retrieve(search_query, k=k)
        filtered = [h for h in hits if h["score"] >= threshold]
        if not filtered:
            return {"analysis": analysis, "answer": "I couldn't find reliable context.", "hits": []}

        context = "\n\n".join(f"[{i+1}] {h['text']}" for i, h in enumerate(filtered))
        keywords_json = json.dumps(self._normalise_keywords(analysis), ensure_ascii=False)
        prompt = self.ADVICE_PROMPT.format(
            user_input=user_input,
            mental_state=analysis.get("mental_state", "unknown"),
            justification=analysis.get("justification", ""),
            knowledge_focus=analysis.get("knowledge_focus", "unknown"),
            keywords=keywords_json,
            retrieved_context=context,
        )
        system_style = (
            "You are “Potted Plant,” a deeply present, emotionally sensitive Thai-speaking "
            "mental health companion. Write in natural, fluent, modern Thai without English, "
            "jargon, or foreign loan words. Avoid overused phrases such as แงงง, โอ้ยใจบาง, "
            "สุดยอด!, เธอเก่งมากกก. Be thoughtful, original, and genuinely empathetic, like a "
            "long heartfelt note to a dear friend. Use imagery or poetic Thai only when it "
            "feels natural. The reply must be a single flowing paragraph—no lists or bullet "
            "points. Follow the JSON template provided in the user message and place the Thai "
            "paragraph under thai_advice."
        )
        messages = [
            {"role": "system", "content": system_style},
            {"role": "user", "content": prompt},
        ]
        advice_raw = self._call_llm(messages, max_tokens=400, temperature=0.6)
        try:
            advice = self._parse_json(advice_raw)
        except json.JSONDecodeError:
            advice = {"raw": advice_raw}
        return {"analysis": analysis, "answer": advice, "hits": filtered}


# ---- ตัวอย่างการใช้งาน ----
if __name__ == "__main__":
    rag = RAG()
    query = "USER_INPUT : " + "ค่าใช้จ่ายบาน ทำงานพาร์ทไทม์ชั่วโมงลด เงินไม่พอ ใช้ชีวิตไปวัน ๆ แบบไม่มีแรงใจ"
    response = rag.test(query)

    print("\n\nAnalysis:", response.get("analysis"))
    print("Answer:", response.get("answer"))
    print("\nHits:")
    for h in response.get("hits", []):
        print(f"[{h['source']} - chunk {h['id']}] (score={h['score']:.2f})")
