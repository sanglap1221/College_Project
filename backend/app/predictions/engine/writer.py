"""High quality narrative draft generator following Jyotish Rulebook v2 Section 10 & 18.
Generates comprehensive, non-deterministic, professional English paragraphs for every topic
directly from the verified rulebook evidence package.
"""

from typing import Any, Dict, List, Tuple
from .reference import TOPICS, HOUSE_DOMAIN, PLANET_KEYWORDS, ordinal

CAVEAT = "This interpretation reflects traditional Parashari Vedic Jyotish principles as symbolic indicators. It is not an empirical certainty or a substitute for professional legal, medical, or financial counsel."

TECHNICAL_TERMS_EXPLAINED = {
    "Kendra": "pivotal angular houses (1st, 4th, 7th, 10th) representing foundational pillars of life",
    "Trikona": "auspicious trine houses (1st, 5th, 9th) signifying merit, knowledge, and fortune",
    "Dusthana": "houses of challenge, transformation, and service (6th, 8th, 12th)",
    "Upachaya": "houses of growth and development over time (3rd, 6th, 10th, 11th)",
    "Mahadasha": "major life cycle ruled by a specific planetary significator",
    "Antardasha": "sub-cycle modulating the thematic focus of the major period",
}


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


def generate_topic_narrative(
    topic: str,
    agg: Dict[str, Any],
    timing_items: List[Dict[str, Any]],
    chart_facts: Dict[str, Any],
    max_items: int = 6,
) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    """Build a natural, flowing narrative draft for a given topic following the Section 10 style."""
    t_info = TOPICS.get(topic, {"title": topic.replace("_", " ").title(), "primary": [], "supporting": [], "karakas": []})
    title = t_info["title"]

    sup_all = [e for e in agg["items"] if e.get("direction") == "supportive"]
    ctr_all = [e for e in agg["items"] if e.get("direction") in ("challenging", "mixed")]
    
    sup = _dedupe_by_group(sup_all)[:max_items]
    ctr = _dedupe_by_group(ctr_all)[:max_items]
    used_items = sup + ctr + timing_items[:3]

    level = agg.get("level", "Moderate")
    lean = agg.get("lean", "mixed")
    explanation = agg.get("explanation", "")

    # 1. Section Introduction
    primary_houses = t_info.get("primary", [])
    pri_str = ", ".join(f"the {ordinal(h)} house ({HOUSE_DOMAIN.get(h, '')})" for h in primary_houses)
    intro = (
        f"In traditional Vedic Jyotish, your {title.lower()} is analyzed through the lens of {pri_str}. "
        f"The convergence of planetary placements, dignity, and lordship patterns establishes the broad thematic tendencies "
        f"and opportunities available for conscious cultivation."
    )

    # 2. Supporting Themes
    if sup:
        sup_lines = []
        for e in sup:
            rule_id = e.get("rule_id", "")
            txt = e.get("text", "")
            sup_lines.append(f"• {txt} [{rule_id}]")
        sup_text = "\n".join(sup_lines)
    else:
        sup_text = "No strong classical supporting yogas or exalted dignity factors were isolated for this specific subject in the primary houses."

    # 3. Challenging or Modifying Factors
    if ctr:
        ctr_lines = []
        for e in ctr:
            rule_id = e.get("rule_id", "")
            txt = e.get("text", "")
            ctr_lines.append(f"• {txt} [{rule_id}]")
        ctr_text = "\n".join(ctr_lines)
    else:
        ctr_text = "No major conflicting planetary tensions or severe debilities were identified in this area."

    # 4. Balanced Synthesis & Development Outlook
    if lean == "predominantly supportive":
        outlook = (
            f"Overall, the chart indicators for {title.lower()} reflect a supportive and constructive foundation. "
            f"The primary house lords exhibit auspicious alignment, indicating favorable potential when paired with consistent effort and self-discipline."
        )
    elif lean == "predominantly challenging":
        outlook = (
            f"Overall, this life domain invites greater consciousness, patience, and deliberate effort. "
            f"The presence of modifying or challenging influences indicates areas where responsibilities and tests may arise, serving as catalysts for mature character development."
        )
    else:
        outlook = (
            f"The chart displays a nuanced combination of both constructive strengths and modifying responsibilities. "
            f"Success in this sphere depends on balancing natural inclinations with measured deliberation and practical discernment."
        )

    # 5. Timing & Periods
    timing_text = ""
    if timing_items:
        timing_lines = []
        for t in timing_items[:3]:
            rule_id = t.get("rule_id", "DASHA")
            timing_lines.append(f"• {t.get('text', '')} [{rule_id}]")
        timing_text = (
            f"### Active Astrological Timing\n"
            f"The timing of these themes is modulated by the current Vimshottari Dasha cycles:\n"
            + "\n".join(timing_lines)
        )

    # 6. Restricted topic handling (Health)
    caution_notice = ""
    if t_info.get("restricted"):
        caution_notice = (
            "> [!NOTE]\n"
            "> **Traditional Vedic Health Symbolism:** Astrological health interpretations reflect broad constitutional tendencies "
            "and elements (fire, earth, air, water) from classical texts. This is strictly non-diagnostic and must never replace medical evaluation."
        )

    # Combine into full markdown narrative
    parts = [
        f"## {title}",
        "",
        f"**Evidence Level:** `{level}` ({lean}) — *{explanation}*",
        "",
        intro,
        "",
        "### Key Symbolic Tendencies & Supporting Factors",
        sup_text,
        "",
        "### Modifying Influences & Growth Challenges",
        ctr_text,
        "",
        "### Development Outlook & Guidance",
        outlook,
    ]

    if timing_text:
        parts.extend(["", timing_text])

    if caution_notice:
        parts.extend(["", caution_notice])

    parts.extend(["", f"*{CAVEAT}*"])

    full_markdown = "\n".join(parts)

    structured_data = {
        "topic": topic,
        "title": title,
        "evidence_level": level,
        "lean": lean,
        "explanation": explanation,
        "counts": agg.get("counts", {}),
        "supporting_factors": [{"factor": e.get("group", ""), "interpretation": e.get("text", ""), "rule_id": e.get("rule_id", "")} for e in sup],
        "challenging_factors": [{"factor": e.get("group", ""), "interpretation": e.get("text", ""), "rule_id": e.get("rule_id", "")} for e in ctr],
        "timing": [t.get("timing") for t in timing_items if "timing" in t],
        "summary": outlook,
        "prediction": full_markdown,
        "status": "templated",
        "review_status": "needs_expert_review",
        "notes": [],
        "limitations": [CAVEAT],
    }

    return full_markdown, used_items, structured_data
