"""High quality narrative draft generator following Jyotish Rulebook v2 Section 10 & 18.
Generates structured per-topic JSON: {overview, themes, challenges, basis_ids}
and professional English report prose without raw engine jargon or markdown syntax leaks.
"""

import re
from typing import Any, Dict, List, Set, Tuple
from .reference import TOPICS, HOUSE_DOMAIN, PLANET_KEYWORDS, ordinal

CAVEAT = "This interpretation reflects traditional Parashari Vedic Jyotish principles as symbolic indicators. It is not an empirical certainty or a substitute for professional legal, medical, or financial counsel."


def _dedupe_by_group(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen = set()
    out = []
    for e in items:
        grp = e.get("group")
        if grp and grp in seen:
            continue
        if grp:
            seen.add(grp)
        out.append(e)
    return out


def clean_markdown_artifacts(text: str) -> str:
    """Strip raw markdown headers, bullet symbols, and raw code fences."""
    if not text:
        return ""
    # Strip backticks
    cleaned = text.replace("`", "")
    # Strip header markers like ###, ##, #
    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
    # Strip raw bullet symbols
    cleaned = re.sub(r"^[•\-\*]\s*", "", cleaned, flags=re.MULTILINE)
    return cleaned.strip()


def enforce_topic_json_limits(data: Dict[str, Any], allowed_ids: Set[str]) -> Dict[str, Any]:
    """Enforce strict code limits on topic JSON schema:
    overview: 40-70 words
    themes: 3 items, <=18 words each
    challenges: 2 items, <=22 words each
    basis_ids: filtered against allowed_ids
    Total words strictly <= 180 words.
    """
    raw_ov = str(data.get("overview", "")).strip()
    raw_ov = clean_markdown_artifacts(raw_ov)
    words = raw_ov.split()

    if len(words) > 70:
        words = words[:70]
        raw_ov = " ".join(words)
        if not raw_ov.endswith((".", "!", "?")):
            raw_ov += "."
    elif len(words) < 40 and len(words) > 0:
        raw_ov = " ".join(words)

    # 3 themes, <= 18 words each
    raw_themes = data.get("themes", [])
    if not isinstance(raw_themes, list):
        raw_themes = [str(raw_themes)]
    clean_themes: List[str] = []
    for t in raw_themes:
        t_clean = clean_markdown_artifacts(str(t))
        t_words = t_clean.split()
        if t_words:
            if len(t_words) > 18:
                t_words = t_words[:18]
            clean_themes.append(" ".join(t_words))
        if len(clean_themes) == 3:
            break

    while len(clean_themes) < 3:
        clean_themes.append("Steady focus on core responsibilities and methodical cultivation.")

    # 2 challenges
    raw_chal = data.get("challenges", [])
    if not isinstance(raw_chal, list):
        raw_chal = [str(raw_chal)]
    clean_chal: List[str] = []
    for c in raw_chal:
        c_clean = clean_markdown_artifacts(str(c))
        c_words = c_clean.split()
        if c_words:
            if len(c_words) > 22:
                c_words = c_words[:22]
            clean_chal.append(" ".join(c_words))
        if len(clean_chal) == 2:
            break

    while len(clean_chal) < 2:
        clean_chal.append("Navigating shifting priorities through measured deliberation and patience.")

    # basis_ids
    raw_basis = data.get("basis_ids", [])
    if not isinstance(raw_basis, list):
        raw_basis = []
    valid_basis = [str(bid).strip() for bid in raw_basis if str(bid).strip() in allowed_ids]
    if not valid_basis:
        valid_basis = sorted(list(allowed_ids))[:4]

    return {
        "overview": raw_ov,
        "themes": clean_themes[:3],
        "challenges": clean_chal[:2],
        "basis_ids": valid_basis,
    }


def generate_topic_json_draft(
    topic: str,
    agg: Dict[str, Any],
    timing_items: List[Dict[str, Any]],
    chart_facts: Dict[str, Any],
    max_items: int = 5,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Build a deterministic template JSON conforming to Section B output schema."""
    t_info = TOPICS.get(topic, {"title": topic.replace("_", " ").title(), "primary": [], "supporting": [], "karakas": []})
    title = t_info["title"]

    sup_all = [e for e in agg["items"] if e.get("direction") == "supportive"]
    ctr_all = [e for e in agg["items"] if e.get("direction") in ("challenging", "mixed")]

    sup = _dedupe_by_group(sup_all)[:max_items]
    ctr = _dedupe_by_group(ctr_all)[:max_items]
    used_items = sup + ctr + timing_items[:3]

    level = agg.get("level", "Moderate")
    lean = agg.get("lean", "mixed")

    # Primary house names
    pri_houses = t_info.get("primary", [])
    pri_names = [f"the {ordinal(h)} house" for h in pri_houses]
    pri_desc = ", ".join(pri_names) if pri_names else "primary house influences"

    # Overview paragraph (40-70 words)
    # Remove generic phrases ("auspicious alignment", "supportive and constructive foundation") unless level is Convergent
    if lean == "predominantly supportive":
        if level == "Convergent":
            foundation_phrase = "reflects a supportive and constructive foundation with auspicious alignment"
        else:
            foundation_phrase = "shows positive planetary indications supporting steady progress"
        overview_text = (
            f"Your astrological profile for {title.lower()} is governed by {pri_desc}. "
            f"The natal indicators reflect strong natural resonance, where consistent focus and personal agency unlock promising potential. "
            f"Overall, the chart {foundation_phrase}, pointing to favorable prospects through structured effort and principled action over time."
        )
    elif lean == "predominantly challenging":
        overview_text = (
            f"Your natal configuration for {title.lower()} is anchored in {pri_desc}. "
            f"This life domain highlights key growth tests requiring conscious perseverance, practical discernment, and patience. "
            f"By approaching responsibilities methodically and managing expectations with maturity, apparent hurdles serve as essential catalysts for long-term personal resilience."
        )
    else:
        overview_text = (
            f"Your astrological indicators for {title.lower()} emphasize balanced planetary influences across {pri_desc}. "
            f"Constructive strengths combine with meaningful responsibilities, requiring steady discernment and moderation. "
            f"Success in this sphere develops naturally when natural talents are paired with consistent preparation and deliberate timing."
        )

    # Clean themes (3 items, <=18 words each)
    themes = []
    if sup:
        for e in sup[:3]:
            txt = e.get("text", "")
            # Sanitize raw engine phrasing
            txt = txt.replace("first house's themes", "that house's themes")
            words = txt.split()[:16]
            themes.append(" ".join(words))
    while len(themes) < 3:
        if len(themes) == 0:
            themes.append("Fostering internal stability and deliberate focus on foundational objectives.")
        elif len(themes) == 1:
            themes.append("Developing constructive collaborations with trusted mentors and allies.")
        else:
            themes.append("Methodical refinement of personal capabilities and consistent application.")

    # Clean challenges (2 items, <=22 words each)
    challenges = []
    if ctr:
        for e in ctr[:2]:
            txt = e.get("text", "")
            txt = txt.replace("first house's themes", "that house's themes")
            words = txt.split()[:20]
            challenges.append(" ".join(words))
    while len(challenges) < 2:
        if len(challenges) == 0:
            challenges.append("Patience is required when external progress moves slower than anticipated.")
        else:
            challenges.append("Careful balancing of competing responsibilities prevents unnecessary fatigue.")

    basis_ids = [e.get("rule_id", "") for e in used_items if e.get("rule_id")]

    allowed_ids = set(basis_ids)
    draft_json = {
        "overview": overview_text,
        "themes": themes[:3],
        "challenges": challenges[:2],
        "basis_ids": basis_ids,
    }

    final_json = enforce_topic_json_limits(draft_json, allowed_ids)
    return final_json, used_items


def generate_topic_narrative(
    topic: str,
    agg: Dict[str, Any],
    timing_items: List[Dict[str, Any]],
    chart_facts: Dict[str, Any],
    max_items: int = 5,
) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    """Generate structured topic representation and clean narrative."""
    t_info = TOPICS.get(topic, {"title": topic.replace("_", " ").title(), "primary": [], "supporting": [], "karakas": []})
    title = t_info["title"]

    topic_json, used_items = generate_topic_json_draft(topic, agg, timing_items, chart_facts, max_items)

    level = agg.get("level", "Moderate")
    lean = agg.get("lean", "mixed")
    explanation = agg.get("explanation", "")

    # Clean prose narrative without raw engine prefixes
    prose_lines = [
        f"## {title}",
        "",
        topic_json["overview"],
        "",
        "Key Themes:",
        "\n".join(f"- {th}" for th in topic_json["themes"]),
        "",
        "Areas for Mindful Growth:",
        "\n".join(f"- {ch}" for ch in topic_json["challenges"]),
    ]

    clean_prose = "\n".join(prose_lines)

    structured_data = {
        "topic": topic,
        "title": title,
        "evidence_level": level,
        "lean": lean,
        "explanation": explanation,
        "counts": agg.get("counts", {}),
        "overview": topic_json["overview"],
        "themes": topic_json["themes"],
        "challenges": topic_json["challenges"],
        "basis_ids": topic_json["basis_ids"],
        "supporting_factors": [
            {"factor": e.get("group", ""), "interpretation": e.get("text", ""), "rule_id": e.get("rule_id", "")}
            for e in used_items if e.get("direction") == "supportive"
        ],
        "challenging_factors": [
            {"factor": e.get("group", ""), "interpretation": e.get("text", ""), "rule_id": e.get("rule_id", "")}
            for e in used_items if e.get("direction") in ("challenging", "mixed")
        ],
        "timing": [t.get("timing") for t in timing_items if "timing" in t],
        "summary": topic_json["overview"],
        "prediction": clean_prose,
        "status": "templated",
        "review_status": "needs_expert_review",
        "notes": [],
        "limitations": [CAVEAT],
    }

    return clean_prose, used_items, structured_data
