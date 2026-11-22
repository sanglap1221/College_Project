"""Deterministic grounding gate. Runs on ANY prose (templated or AI-written)."""
import re
from .reference import PLANETS
ORD=re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)\b")
CITE=re.compile(r"\[([A-Z0-9][A-Z0-9\-]*)\]")
def check(text, allowed_ids, allowed_houses, allowed_planets, allowed_dates, forbidden):
    problems=[]
    for pat in forbidden:
        m=re.search(pat,text,re.I)
        if m: problems.append(f"forbidden claim pattern: '{m.group(0)}'")
    cited=set(CITE.findall(text))
    for c in cited-set(allowed_ids): problems.append(f"unknown rule id cited: {c}")
    if not cited: problems.append("no rule IDs cited")
    for ln in text.splitlines():
        s=ln.strip()
        if len(s)>70 and not CITE.search(s) and "not a certainty" not in s and "not medical advice" not in s and not s.startswith("Evidence level"):
            problems.append(f"uncited statement: '{s[:60]}...'")
    for h in {int(x) for x in ORD.findall(text)}-set(allowed_houses):
        problems.append(f"house {h} mentioned but not in evidence")
    for p in set(re.findall(r"\b("+"|".join(PLANETS)+r")\b",text))-set(allowed_planets):
        problems.append(f"planet {p} mentioned but not in evidence")
    seen=set(re.findall(r"\b\d{4}-\d{2}-\d{2}\b",text))|set(re.findall(r"\b(?:19|20)\d{2}\b",text))
    ok={d for d in allowed_dates}|{d[:4] for d in allowed_dates}
    for d in seen-ok: problems.append(f"date/year {d} not in supplied timing")
    return problems
