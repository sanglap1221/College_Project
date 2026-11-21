import re
from pathlib import Path
from typing import List, Dict

class DocumentRAG:
    def __init__(self):
        self.chunks: List[Dict[str, str]] = []
        self._load_and_chunk()

    def _load_and_chunk(self):
        # Locate new.txt relative to backend or root
        possible_paths = [
            Path(__file__).resolve().parents[3] / "new.txt",
            Path(__file__).resolve().parents[2] / "new.txt",
            Path("new.txt"),
        ]

        doc_path = None
        for p in possible_paths:
            if p.is_file():
                doc_path = p
                break

        if not doc_path:
            # Fallback default chunks if new.txt not found directly
            self.chunks = [
                {"title": "6 Core Modules", "content": "1. Birth Chart Data 2. Astrology Knowledge Base 3. Rule & Analysis Engine 4. Timing Engine 5. Prediction Engine 6. AI Interpretation"},
                {"title": "Planets", "content": "Sun: Authority, leadership, vitality. Moon: Mind, emotions. Mars: Action, courage. Mercury: Communication. Jupiter: Knowledge. Venus: Relationships. Saturn: Discipline. Rahu: Ambition. Ketu: Detachment."},
                {"title": "Houses", "content": "1st: Self, body. 2nd: Wealth, family. 3rd: Effort, courage. 4th: Home, mother. 5th: Education, children. 6th: Debts, service. 7th: Marriage, partnership. 8th: Transformation. 9th: Dharma, fortune. 10th: Career, status. 11th: Gains, income. 12th: Expenses, foreign."}
            ]
            return

        try:
            text = doc_path.read_text(encoding="utf-8")
            # Split by double newlines or numbered sections
            raw_sections = re.split(r'\n(?=[0-9]+\.\s+[A-Z]|[A-Z][a-zA-Z\s]{3,}\n)', text)
            for i, section in enumerate(raw_sections):
                sec_clean = section.strip()
                if len(sec_clean) > 20:
                    lines = sec_clean.split("\n")
                    title = lines[0] if len(lines) > 0 else f"Section {i+1}"
                    self.chunks.append({
                        "title": title[:60],
                        "content": sec_clean
                    })
            if not self.chunks:
                self.chunks.append({"title": "Full Document", "content": text[:4000]})
        except Exception as e:
            print(f"Error loading new.txt for RAG: {e}")

    def retrieve(self, query: str, top_k: int = 2) -> List[str]:
        if not self.chunks:
            return []

        query_words = set(re.findall(r'\w+', query.lower()))
        scored_chunks = []

        for chunk in self.chunks:
            text_lower = (chunk["title"] + " " + chunk["content"]).lower()
            score = sum(1 for word in query_words if word in text_lower)
            if score > 0:
                scored_chunks.append((score, chunk["content"]))

        # Sort by match score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        if not scored_chunks:
            # Fallback to first few chunks if no keyword overlap
            return [c["content"] for c in self.chunks[:top_k]]

        return [content for score, content in scored_chunks[:top_k]]

# Singleton instance
rag_store = DocumentRAG()
