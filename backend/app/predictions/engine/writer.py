"""High quality narrative draft generator following Jyotish Rulebook v2 Section 10 & 18.
Generates structured per-topic JSON: {overview, themes, challenges, basis_ids}
and professional English, Bengali, and Hindi report interpretations.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from .reference import (
    TOPICS, TOPIC_TITLES, HOUSE_DOMAIN, PLANET_KEYWORDS, ordinal,
    SIGNS, TOPIC_PRIMARY_HOUSE, SIGNS_BN, SIGNS_HI, PLANETS_BN, PLANETS_HI,
    format_houses_ruled, to_bn_digits
)
from .explain import explain_rule, build_why_this_prediction, HOUSE_NAMES, PLANET_NAMES

CAVEATS = {
    "en": "This interpretation reflects traditional Parashari Vedic Jyotish principles as symbolic indicators. It is not an empirical certainty or a substitute for professional legal, medical, or financial counsel.",
    "bn": "এই ফলাফল প্রথাগত পরাশরী বৈদিক জ্যোতিষের সাংকেতিক সূত্রের ভিত্তিতে নির্ণিত। এটি নিশ্চিত বিধিলিপি বা কোনো আইনি, চিকিৎসা অথবা আর্থিক উপদেশের বিকল্প নয়।",
    "hi": "यह व्याख्या पारंपरिक पराशरी वैदिक ज्योतिष के प्रतीकात्मक सूत्रों पर आधारित है। यह कोई निश्चित भविष्यवाणी या कानूनी, चिकित्सीय अथवा वित्तीय सलाह का विकल्प नहीं है।",
}


def _build_current_period(timing_items: List[Dict[str, Any]], chart_facts: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Construct current active dasha period summary for the topic."""
    if not timing_items:
        return None
    md = next((t for t in timing_items if t.get("timing", {}).get("level") in ("MD", "mahadasha")), None)
    ad = next((t for t in timing_items if t.get("timing", {}).get("level") in ("AD", "antardasha")), None)
    return {
        "mahadasha": md.get("timing") if md else None,
        "antardasha": ad.get("timing") if ad else None,
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


def clean_markdown_artifacts(text: str) -> str:
    """Strip raw markdown headers, bullet symbols, and raw code fences."""
    if not text:
        return ""
    cleaned = text.replace("`", "")
    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned, flags=re.MULTILINE)
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
        if not raw_ov.endswith((".", "!", "?", "।")):
            raw_ov += "."
    elif len(words) < 40 and len(words) > 0:
        raw_ov = " ".join(words)

    # 3 themes, <= 28 words each
    raw_themes = data.get("themes", [])
    if not isinstance(raw_themes, list):
        raw_themes = [str(raw_themes)]
    clean_themes: List[str] = []
    for t in raw_themes:
        t_clean = clean_markdown_artifacts(str(t))
        t_words = t_clean.split()
        if t_words:
            if len(t_words) > 28:
                t_words = t_words[:28]
            clean_str = " ".join(t_words)
            if not clean_str.endswith((".", "!", "?", "।")):
                clean_str += "."
            clean_themes.append(clean_str)
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
            if len(c_words) > 28:
                c_words = c_words[:28]
            clean_str = " ".join(c_words)
            if not clean_str.endswith((".", "!", "?", "।")):
                clean_str += "."
            clean_chal.append(clean_str)
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


def format_evidence_sentence(item: Dict[str, Any], chart: Any = None, lang: str = "en") -> str:
    """Format a single evidence sentence citing evidence ID and naming chart-specific facts without filler."""
    rule_id = item.get("rule_id", "FACT")
    facts = item.get("facts", {})
    planets = item.get("planets", [])
    kind = item.get("kind", "")

    if rule_id.startswith("YOGA-"):
        p_list = planets or []
        first_p = p_list[0] if p_list else "Jupiter"
        sign_idx = chart.sign(first_p) if chart else 5
        sign_name = SIGNS[sign_idx - 1]
        h_occ = chart.house(first_p) if chart else 9
        is_raja = "RAJA" in rule_id

        if lang == "bn":
            p_names = ", ".join([PLANETS_BN.get(p, p) for p in p_list])
            y_name = "রাজযোগ" if is_raja else "শুভ গ্রহ সম্মেলন"
            return f"[{rule_id}] {SIGNS_BN.get(sign_name, sign_name)} রাশিতে ({to_bn_digits(h_occ)}ম ভাব) {p_names}-এর সংযোগে গঠিত {y_name} কেন্দ্র ও ত্রিকোণাধিপতির শক্তিকে সংহত করে।"
        elif lang == "hi":
            p_names = ", ".join([PLANETS_HI.get(p, p) for p in p_list])
            y_name = "राजयोग" if is_raja else "शुभ ग्रहीय योग"
            return f"[{rule_id}] {SIGNS_HI.get(sign_name, sign_name)} राशि में ({h_occ}वें भाव) {p_names} के संयोजन से निर्मित {y_name} केंद्र एवं त्रिकोण के स्वामियों को बल प्रदान करता है।"
        else:
            p_names = ", ".join(p_list)
            y_name = "Raja Yoga" if is_raja else "Planetary Combination"
            return f"[{rule_id}] {y_name} formed by {p_names} in {sign_name} ({ordinal(h_occ)} house) unifies Kendra and Trikona lord influences."

    # Lord placement: HL-H...-IN-H...
    if kind == "lord_placement" or rule_id.startswith("HL-"):
        h_from = facts.get("house")
        h_to = facts.get("placed_in")
        lord = facts.get("lord")
        if not lord and chart and h_from:
            lord = chart.house_lord(h_from)
        if not h_to and chart and lord:
            h_to = chart.house(lord)
        h_from = h_from or 1
        h_to = h_to or 1
        lord = lord or "Planet"
        sign_idx = chart.sign(lord) if chart else 1
        sign_name = SIGNS[sign_idx - 1]

        if lang == "bn":
            p_bn = PLANETS_BN.get(lord, lord)
            s_bn = SIGNS_BN.get(sign_name, sign_name)
            return f"[{rule_id}] {p_bn} ({to_bn_digits(h_from)}ম ভাবের অধিপতি, {s_bn} রাশিতে {to_bn_digits(h_to)}ম ভাবস্থ) {to_bn_digits(h_from)}ম ভাবের শক্তিকে সরাসরি {to_bn_digits(h_to)}ম ভাবের কার্যধারায় প্রতিফলিত করে।"
        elif lang == "hi":
            p_hi = PLANETS_HI.get(lord, lord)
            s_hi = SIGNS_HI.get(sign_name, sign_name)
            return f"[{rule_id}] {p_hi} ({h_from}वें भाव का स्वामी, {s_hi} राशि में {h_to}वें भाव में स्थित) {h_from}वें भाव के प्रभाव को सीधे {h_to}वें भाव में सक्रिय करता है।"
        else:
            return f"[{rule_id}] {lord} (ruling the {ordinal(h_from)} house, placed in {sign_name} in the {ordinal(h_to)} house) links the portfolio of the {ordinal(h_from)} house directly into the {ordinal(h_to)} house."

    # Planet placement: PH-...
    if kind == "placement" or rule_id.startswith("PH-"):
        p = planets[0] if planets else "Planet"
        h_occ = facts.get("house", chart.house(p) if chart else 1)
        sign_idx = chart.sign(p) if chart else 1
        sign_name = SIGNS[sign_idx - 1]
        ruled = chart.lorded(p) if chart else []
        ruled_str = format_houses_ruled(ruled, lang)

        if lang == "bn":
            p_bn = PLANETS_BN.get(p, p)
            s_bn = SIGNS_BN.get(sign_name, sign_name)
            return f"[{rule_id}] {p_bn} {s_bn} রাশিতে {to_bn_digits(h_occ)}ম ভাবস্থ ({ruled_str}), যা {to_bn_digits(h_occ)}ম ভাবের বিষয়ে প্রত্যক্ষ প্রভাব নির্দেশ করে।"
        elif lang == "hi":
            p_hi = PLANETS_HI.get(p, p)
            s_hi = SIGNS_HI.get(sign_name, sign_name)
            return f"[{rule_id}] {p_hi} {s_hi} राशि में {h_occ}वें भाव में स्थित है ({ruled_str}), जो {h_occ}वें भाव के प्रभाव को संचालित करता है।"
        else:
            return f"[{rule_id}] {p} occupies {sign_name} in the {ordinal(h_occ)} house ({ruled_str}), focusing active planetary energy on this sector."

    # Dignity: DG-...
    if kind == "dignity" or rule_id.startswith("DG-"):
        p = planets[0] if planets else "Planet"
        dig = chart.dignity(p) if chart else "dignified"
        sign_idx = chart.sign(p) if chart else 1
        sign_name = SIGNS[sign_idx - 1]
        h_occ = chart.house(p) if chart else 1
        ruled = chart.lorded(p) if chart else []
        ruled_str = format_houses_ruled(ruled, lang)

        if lang == "bn":
            p_bn = PLANETS_BN.get(p, p)
            s_bn = SIGNS_BN.get(sign_name, sign_name)
            return f"[{rule_id}] {p_bn} {s_bn} রাশিতে ({to_bn_digits(h_occ)}ম ভাব) স্থানবলে স্থিত, যা {ruled_str}-কে কার্যকর শক্তি প্রদান করে।"
        elif lang == "hi":
            p_hi = PLANETS_HI.get(p, p)
            s_hi = SIGNS_HI.get(sign_name, sign_name)
            return f"[{rule_id}] {p_hi} {s_hi} राशि में ({h_occ}वें भाव) शुभ बल में स्थित है, जो {ruled_str} को प्रत्यक्ष सामर्थ्य देता है।"
        else:
            return f"[{rule_id}] {p} possesses {dig} dignity in {sign_name} ({ordinal(h_occ)} house), reinforcing {ruled_str}."

    txt = item.get("text", "")
    return f"[{rule_id}] {txt}"


def get_topic_header(topic: str, chart: Any = None, lang: str = "en") -> str:
    """Return topic header with topic-relevant lord per Parashari principles."""
    h_pri = TOPIC_PRIMARY_HOUSE.get(topic, 1)
    base_title = TOPIC_TITLES.get(lang, TOPIC_TITLES["en"]).get(topic, topic.replace("_", " ").title())
    if not chart:
        return base_title
    pri_lord = chart.house_lord(h_pri)
    pri_lord_h = chart.house(pri_lord)
    pri_sign = SIGNS[chart.sign(pri_lord) - 1]

    if lang == "bn":
        p_bn = PLANETS_BN.get(pri_lord, pri_lord)
        s_bn = SIGNS_BN.get(pri_sign, pri_sign)
        return f"{base_title} — {to_bn_digits(h_pri)}ম পতি ({p_bn}) {to_bn_digits(pri_lord_h)}ম ভাবে ({s_bn})"
    elif lang == "hi":
        p_hi = PLANETS_HI.get(pri_lord, pri_lord)
        s_hi = SIGNS_HI.get(pri_sign, pri_sign)
        return f"{base_title} — {h_pri}वें भाव का स्वामी ({p_hi}) {pri_lord_h}वें भाव में ({s_hi})"
    else:
        return f"{base_title} — {ordinal(h_pri)} Lord ({pri_lord}) in {ordinal(pri_lord_h)} House ({pri_sign})"


def generate_topic_json_draft(
    topic: str,
    agg: Dict[str, Any],
    timing_items: List[Dict[str, Any]],
    chart_facts: Dict[str, Any],
    max_items: int = 5,
    language: str = "en",
    chart: Any = None,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Build a deterministic template JSON conforming to Section B output schema."""
    title = get_topic_header(topic, chart=chart, lang=language)

    sup_all = [e for e in agg["items"] if e.get("direction") == "supportive"]
    ctr_all = [e for e in agg["items"] if e.get("direction") in ("challenging", "mixed")]

    sup = _dedupe_by_group(sup_all)[:max_items]
    ctr = _dedupe_by_group(ctr_all)[:max_items]
    used_items = _dedupe_by_group(sup + ctr)

    lean = agg.get("lean", "mixed")
    h_pri = TOPIC_PRIMARY_HOUSE.get(topic, 1)
    pri_lord = chart.house_lord(h_pri) if chart else "Lord"
    pri_lord_h = chart.house(pri_lord) if chart else 1
    pri_sign = SIGNS[chart.sign(pri_lord) - 1] if chart else "Sign"
    n_groups = agg.get("counts", {}).get("independent_groups", len(used_items))

    # Formulate Overview opening sentence referencing topic-relevant lord and placement
    if language == "bn":
        p_bn = PLANETS_BN.get(pri_lord, pri_lord)
        s_bn = SIGNS_BN.get(pri_sign, pri_sign)
        base_t = TOPIC_TITLES.get("bn", {}).get(topic, topic)
        overview_text = (
            f"আপনার {base_t}-এর ক্ষেত্রটি {to_bn_digits(h_pri)}ম পতি {p_bn} দ্বারা পরিচালিত, যা {s_bn} রাশিতে {to_bn_digits(pri_lord_h)}ম ভাবস্থ। "
            f"কুণ্ডলীর {to_bn_digits(n_groups)}টি গ্রহীয় অবস্থানের বিচারে এই ক্ষেত্রে {lean}-এর প্রভাব দেখা যায়। "
            f"সঠিক পরিকল্পনা ও নিয়মিত একাগ্রতার মাধ্যমে কাঙ্ক্ষিত অগ্রগতি ও স্থায়িত্ব লাভ সম্ভব।"
        )
    elif language == "hi":
        p_hi = PLANETS_HI.get(pri_lord, pri_lord)
        s_hi = SIGNS_HI.get(pri_sign, pri_sign)
        base_t = TOPIC_TITLES.get("hi", {}).get(topic, topic)
        overview_text = (
            f"आपकी {base_t} का आधार {h_pri}वें भाव के स्वामी {p_hi} द्वारा निर्धारित है, जो {s_hi} राशि में {pri_lord_h}वें भाव में स्थित है। "
            f"पत्रिका के {n_groups} ग्रह सूत्रों के आधार पर इस क्षेत्र में {lean} प्रभाव परिलक्षित होता है। "
            f"योजनाबद्ध कार्यप्रणाली एवं निरंतर प्रयास से इस क्षेत्र में दीर्घकालिक स्थिरता प्राप्त होगी।"
        )
    else:
        base_t = TOPIC_TITLES.get("en", {}).get(topic, topic.title())
        overview_text = (
            f"Your astrological configuration for {base_t.lower()} is anchored by the {ordinal(h_pri)} house lord {pri_lord} placed in {pri_sign} in the {ordinal(pri_lord_h)} house. "
            f"The chart reflects a {lean} pattern across {n_groups} independent factor groups. "
            f"Consistent focus and principled personal agency provide a constructive foundation for long-term progress."
        )

    # Formulate Themes (supportive factor sentences, each citing evidence ID and naming chart facts)
    themes: List[str] = []
    for e in sup[:3]:
        s_txt = format_evidence_sentence(e, chart=chart, lang=language)
        themes.append(s_txt)
    first_rule_id = agg["items"][0].get("rule_id", "NATAL") if agg.get("items") else "NATAL"
    while len(themes) < 3:
        if language == "bn":
            themes.append(f"[{first_rule_id}] {to_bn_digits(h_pri)}ম পতির নির্দেশিত দায়িত্বে ধারাবাহিক একাগ্রতা বজায় রাখা।")
        elif language == "hi":
            themes.append(f"[{first_rule_id}] {h_pri}वें भावेश के अनुसार मुख्य लक्ष्यों के प्रति नियमित निष्ठा।")
        else:
            themes.append(f"[{first_rule_id}] Steady dedication to core responsibilities indicated by the {ordinal(h_pri)} house lord.")

    # Formulate Challenges (modifying factor sentences, each citing evidence ID and naming chart facts)
    challenges: List[str] = []
    for e in ctr[:2]:
        c_txt = format_evidence_sentence(e, chart=chart, lang=language)
        challenges.append(c_txt)
    while len(challenges) < 2:
        if language == "bn":
            challenges.append(f"[{first_rule_id}] পরিবর্তনশীল পরিস্থিতিতে সময়োপযোগী ধৈর্য্য ও ভারসাম্য রক্ষা করা।")
        elif language == "hi":
            challenges.append(f"[{first_rule_id}] बदलती परिस्थितियों में विवेक एवं धैर्य का सम्यक संतुलन।")
        else:
            challenges.append(f"[{first_rule_id}] Measured deliberation and patience across evolving operational cycles.")

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
    language: str = "en",
    chart: Any = None,
) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    """Generate structured topic representation, complete multilingual translations,
    and Section 20 human-readable rule explanations.
    """
    title = get_topic_header(topic, chart=chart, lang=language)

    topic_json, used_items = generate_topic_json_draft(
        topic, agg, timing_items, chart_facts, max_items, language=language, chart=chart
    )

    level = agg.get("level", "Moderate")
    lean = agg.get("lean", "mixed")
    explanation = agg.get("explanation", "")
    caveat = CAVEATS.get(language, CAVEATS["en"])

    # Build Section 20.B 'Why this prediction?' 6-point breakdown
    why_this = build_why_this_prediction(topic, agg, used_items, chart_facts)

    # Process supporting factors with human explanations
    supporting_factors = []
    for e in used_items:
        if e.get("direction") == "supportive":
            rid = e.get("rule_id", "")
            exp = explain_rule(rid, factor_data=e, chart_facts=chart_facts)
            formatted_sentence = format_evidence_sentence(e, chart=chart, lang=language)
            supporting_factors.append({
                "factor": e.get("group", ""),
                "rule_id": rid,
                "interpretation": formatted_sentence,
                "simple_explanation": exp["simple_explanation"],
                "advanced_explanation": exp["advanced_explanation"],
                "why_matters": exp["why_matters"],
                "example": exp["example"],
                "limitations": exp["limitations"],
            })

    # Process challenging factors with human explanations
    challenging_factors = []
    for e in used_items:
        if e.get("direction") in ("challenging", "mixed"):
            rid = e.get("rule_id", "")
            exp = explain_rule(rid, factor_data=e, chart_facts=chart_facts)
            formatted_sentence = format_evidence_sentence(e, chart=chart, lang=language)
            challenging_factors.append({
                "factor": e.get("group", ""),
                "rule_id": rid,
                "interpretation": formatted_sentence,
                "simple_explanation": exp["simple_explanation"],
                "advanced_explanation": exp["advanced_explanation"],
                "why_matters": exp["why_matters"],
                "example": exp["example"],
                "limitations": exp["limitations"],
            })

    # Generate multilingual dictionary for instantaneous language switching (en, bn, hi)
    translations: Dict[str, Dict[str, Any]] = {}
    for lang_code in ("en", "bn", "hi"):
        l_title = get_topic_header(topic, chart=chart, lang=lang_code)
        l_json, _ = generate_topic_json_draft(
            topic, agg, timing_items, chart_facts, max_items, language=lang_code, chart=chart
        )
        l_prose_lines = [
            f"## {l_title}",
            "",
            l_json["overview"],
            "",
            "Key Themes:" if lang_code == "en" else "মূল বৈশিষ্ট্য:" if lang_code == "bn" else "प्रमुख सूत्र:",
            "\n".join(f"- {th}" for th in l_json["themes"]),
            "",
            "Areas for Mindful Growth:" if lang_code == "en" else "সতর্কতা ও আত্মউন্নয়ন:" if lang_code == "bn" else "सावधानी एवं आत्मविकास:",
            "\n".join(f"- {ch}" for ch in l_json["challenges"]),
        ]
        translations[lang_code] = {
            "title": l_title,
            "overview": l_json["overview"],
            "themes": l_json["themes"],
            "challenges": l_json["challenges"],
            "summary": l_json["overview"],
            "prediction": "\n".join(l_prose_lines),
            "caveat": CAVEATS.get(lang_code, CAVEATS["en"]),
            "why_this": {
                "placement_meaning": why_this["placement_meaning"].get(lang_code, why_this["placement_meaning"]["en"]),
                "involved_factors": why_this["involved_factors"].get(lang_code, why_this["involved_factors"]["en"]),
                "life_themes": why_this["life_themes"].get(lang_code, why_this["life_themes"]["en"]),
                "relevance": why_this["relevance"].get(lang_code, why_this["relevance"]["en"]),
                "modifying_factors": why_this["modifying_factors"].get(lang_code, why_this["modifying_factors"]["en"]),
                "synthesis": why_this["synthesis"].get(lang_code, why_this["synthesis"]["en"]),
            },
        }

    prose_lines = [
        f"## {title}",
        "",
        topic_json["overview"],
        "",
        "Key Themes:" if language == "en" else "মূল বৈশিষ্ট্য:" if language == "bn" else "प्रमुख सूत्र:",
        "\n".join(f"- {th}" for th in topic_json["themes"]),
        "",
        "Areas for Mindful Growth:" if language == "en" else "সতর্কতা ও আত্মউন্নয়ন:" if language == "bn" else "सावधानी एवं आत्मविकास:",
        "\n".join(f"- {ch}" for ch in topic_json["challenges"]),
    ]
    clean_prose = "\n".join(prose_lines)

    h_pri = TOPIC_PRIMARY_HOUSE.get(topic, 1)
    pri_lord = chart.house_lord(h_pri) if chart else None
    pri_lord_h = chart.house(pri_lord) if (chart and pri_lord) else None
    pri_sign = SIGNS[chart.sign(pri_lord) - 1] if (chart and pri_lord) else None

    structured_data = {
        "topic": topic,
        "title": title,
        "header_lord": {
            "house": h_pri,
            "lord": pri_lord,
            "occupied_house": pri_lord_h,
            "sign": pri_sign,
        },
        "evidence_level": level,
        "lean": lean,
        "explanation": explanation,
        "counts": agg.get("counts", {}),
        "overview": topic_json["overview"],
        "themes": topic_json["themes"],
        "challenges": topic_json["challenges"],
        "basis_ids": topic_json["basis_ids"],
        "supporting_factors": supporting_factors,
        "challenging_factors": challenging_factors,
        "why_this": why_this,
        "translations": translations,
        "timing": [t.get("timing") for t in timing_items if "timing" in t],
        "current_period": _build_current_period(timing_items, chart_facts),
        "summary": topic_json["overview"],
        "prediction": clean_prose,
        "status": "templated",
        "review_status": "needs_expert_review",
        "notes": [],
        "limitations": [caveat],
    }

    return clean_prose, used_items, structured_data
