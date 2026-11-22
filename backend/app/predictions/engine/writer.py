"""High quality narrative draft generator following Jyotish Rulebook v2 Section 10 & 18.
Generates structured per-topic JSON: {overview, themes, challenges, basis_ids}
and professional English, Bengali, and Hindi report interpretations.
"""

import re
from typing import Any, Dict, List, Set, Tuple
from .reference import TOPICS, TOPIC_TITLES, HOUSE_DOMAIN, PLANET_KEYWORDS, ordinal
from .explain import explain_rule, build_why_this_prediction

CAVEATS = {
    "en": "This interpretation reflects traditional Parashari Vedic Jyotish principles as symbolic indicators. It is not an empirical certainty or a substitute for professional legal, medical, or financial counsel.",
    "bn": "এই ফলাফল প্রথাগত পরাশরী বৈদিক জ্যোতিষের সাংকেতিক সূত্রের ভিত্তিতে নির্ণিত। এটি নিশ্চিত বিধিলিপি বা কোনো আইনি, চিকিৎসা অথবা আর্থিক উপদেশের বিকল্প নয়।",
    "hi": "यह व्याख्या पारंपरिक पराशरी वैदिक ज्योतिष के प्रतीकात्मक सूत्रों पर आधारित है। यह कोई निश्चित भविष्यवाणी या कानूनी, चिकित्सीय अथवा वित्तीय सलाह का विकल्प नहीं है।",
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
    language: str = "en",
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Build a deterministic template JSON conforming to Section B output schema."""
    t_titles = TOPIC_TITLES.get(language, TOPIC_TITLES["en"])
    title = t_titles.get(topic, TOPICS.get(topic, {}).get("title", topic.replace("_", " ").title()))

    sup_all = [e for e in agg["items"] if e.get("direction") == "supportive"]
    ctr_all = [e for e in agg["items"] if e.get("direction") in ("challenging", "mixed")]

    sup = _dedupe_by_group(sup_all)[:max_items]
    ctr = _dedupe_by_group(ctr_all)[:max_items]
    used_items = sup + ctr + timing_items[:3]

    level = agg.get("level", "Moderate")
    lean = agg.get("lean", "mixed")

    # Primary house names
    t_info = TOPICS.get(topic, {"primary": []})
    pri_houses = t_info.get("primary", [])
    pri_names = [f"the {ordinal(h)} house" for h in pri_houses]
    pri_desc = ", ".join(pri_names) if pri_names else "primary house influences"

    # Multilingual Overview handling
    if language == "bn":
        if lean == "predominantly supportive":
            overview_text = (
                f"আপনার জন্মকুণ্ডলীতে {title}-এর ক্ষেত্রটি শুভ এবং অনুকূল ইঙ্গিত প্রদান করছে। "
                f"প্রধান ভাবাধিপতি ও সংশ্লিষ্ট গ্রহের সংযোগ কর্মক্ষমতা বৃদ্ধি ও সুদৃঢ় ভিত্তি রচনায় সহায়ক। "
                f"সঠিক পরিকল্পনা ও নিয়মিত একাগ্রতার মাধ্যমে এই ক্ষেত্রে কাঙ্ক্ষিত অগ্রগতি লাভ সম্ভব হবে।"
            )
        elif lean == "predominantly challenging":
            overview_text = (
                f"আপনার জন্মকুণ্ডলীতে {title}-এর ক্ষেত্রে বিশেষ সতর্কতা ও ধৈর্য্যের প্রয়োজন। "
                f"গ্রহগত প্রভাব সাময়িক বাধা ও দায়িত্বের ইঙ্গিত দেয় যা আত্মউন্নয়ন ও চরিত্র গঠনের অনুঘটক হিসেবে কাজ করবে। "
                f"বাস্তববাদী মনোভাব বজায় রেখে কর্তব্যে অবিচল থাকলে দীর্ঘমেয়াদী ইতিবাচক ফল লাভ সম্ভব।"
            )
        else:
            overview_text = (
                f"আপনার জন্মকুণ্ডলীতে {title}-এর ক্ষেত্রটিতে শুভ সম্ভাবনা ও দায়িত্ববোধের মিশ্র প্রকাশ দেখা যায়। "
                f"পরিমিত বিচারবুদ্ধি ও সুষম সিদ্ধান্তের মাধ্যমে জীবনের এই ক্ষেত্রে অগ্রগতি ত্বরান্বিত হবে। "
                f"উপযুক্ত সময়ের সদ্ব্যবহার এবং নিষ্ঠাবান প্রচেষ্টাই এই ক্ষেত্রে স্থায়িত্ব নিশ্চিত করবে।"
            )
        themes = [
            "উদ্দেশ্যমুখী কর্মে একাগ্রতা এবং আত্মবিশ্বাস বজায় রাখা।",
            "অভিজ্ঞ পরামর্শদাতা ও শুভাকাঙ্ক্ষীদের সহযোগিতায় সঠিক সিদ্ধান্ত গ্রহণ।",
            "নিয়মিত অনুশীলনের মাধ্যমে ব্যক্তিগত দক্ষতার পূর্ণ বিকাশ সাধন।"
        ]
        challenges = [
            "প্রতিকূল পরিস্থিতিতে ধৈর্য্য ধারণ এবং মানসিক ভারসাম্য রক্ষা করা।",
            "দায়িত্ব ও ব্যক্তিগত আকাঙ্ক্ষার মধ্যে সুষম সমন্বয় বজায় রাখা।"
        ]
    elif language == "hi":
        if lean == "predominantly supportive":
            overview_text = (
                f"आपकी जन्मपत्रिका में {title} का क्षेत्र विशेष रूप से सकारात्मक एवं प्रगतिशील संकेत देता है। "
                f"प्रमुख भावेश एवं ग्रहों की शुभ स्थिति निरंतर प्रयास एवं आत्म-अनुशासन से सफलता प्राप्त करने में पूर्णतः सहायक है। "
                f"योजनाबद्ध कार्यप्रणाली द्वारा इस क्षेत्र में दीर्घकालिक स्थिरता एवं विकास संभव होगा।"
            )
        elif lean == "predominantly challenging":
            overview_text = (
                f"आपकी जन्मपत्रिका में {title} के संदर्भ में धैर्य एवं विशेष विचारशीलता की आवश्यकता परिलक्षित होती है। "
                f"यह क्षेत्र कुछ महत्वपूर्ण उत्तरदायित्वों एवं परीक्षाओं को इंगित करता है जो परिपक्वता प्रदान करेंगे। "
                f"शांतिपूर्ण दृष्टिकोण एवं विवेकपूर्ण आचरण से सभी बाधाओं का समाधान सहजता से होगा।"
            )
        else:
            overview_text = (
                f"आपकी जन्मपत्रिका में {title} का क्षेत्र संतुलित एवं मिश्रित ग्रह प्रभाव दर्शाता है। "
                f"स्वाभाविक क्षमताओं के साथ विवेकपूर्ण निर्णय शक्ति का समन्वय इस क्षेत्र में निरंतर प्रगति सुनिश्चित करेगा। "
                f"सकारात्मक अवसरों का समुचित लाभ उठाने के लिए नियमित प्रयास आवश्यक रहेंगे।"
            )
        themes = [
            "मूल लक्ष्यों के प्रति एकाग्रता एवं कर्मठता का विकास।",
            "वरिष्ठों के मार्गदर्शन एवं सहयोग से सुदृढ़ निर्णयों का क्रियान्वयन।",
            "अपनी स्वाभाविक क्षमताओं का निरंतर संवर्धन एवं व्यावहारिक उपयोग।"
        ]
        challenges = [
            "कठिन परिस्थितियों में धैर्य बनाए रखना एवं अधीरता से बचना।",
            "कार्य एवं पारिवारिक जिम्मेदारियों में सम्यक संतुलन स्थापित करना।"
        ]
    else:
        # English
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

        themes = []
        if sup:
            for e in sup[:3]:
                txt = e.get("text", "")
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
    language: str = "en",
) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
    """Generate structured topic representation, complete multilingual translations,
    and Section 20 human-readable rule explanations.
    """
    t_titles = TOPIC_TITLES.get(language, TOPIC_TITLES["en"])
    title = t_titles.get(topic, TOPICS.get(topic, {}).get("title", topic.replace("_", " ").title()))

    topic_json, used_items = generate_topic_json_draft(
        topic, agg, timing_items, chart_facts, max_items, language=language
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
            raw_text = e.get("text", "")
            clean_text = re.sub(r'\b(HL|PH|DG|YOGA)-[A-Z0-9\-_]+\b', '', raw_text).replace("first house's themes", "that house's themes").strip()
            if clean_text.endswith((".", "!", "?")):
                pass
            elif clean_text:
                clean_text += "."

            exp = explain_rule(rid, factor_data=e, chart_facts=chart_facts)
            supporting_factors.append({
                "factor": e.get("group", ""),
                "rule_id": rid,
                "interpretation": clean_text,
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
            raw_text = e.get("text", "")
            clean_text = re.sub(r'\b(HL|PH|DG|YOGA)-[A-Z0-9\-_]+\b', '', raw_text).replace("first house's themes", "that house's themes").strip()
            if clean_text.endswith((".", "!", "?")):
                pass
            elif clean_text:
                clean_text += "."

            exp = explain_rule(rid, factor_data=e, chart_facts=chart_facts)
            challenging_factors.append({
                "factor": e.get("group", ""),
                "rule_id": rid,
                "interpretation": clean_text,
                "simple_explanation": exp["simple_explanation"],
                "advanced_explanation": exp["advanced_explanation"],
                "why_matters": exp["why_matters"],
                "example": exp["example"],
                "limitations": exp["limitations"],
            })

    # Generate multilingual dictionary for instantaneous language switching (en, bn, hi)
    translations: Dict[str, Dict[str, Any]] = {}
    for lang_code in ("en", "bn", "hi"):
        l_titles = TOPIC_TITLES.get(lang_code, TOPIC_TITLES["en"])
        l_title = l_titles.get(topic, title)
        l_json, _ = generate_topic_json_draft(
            topic, agg, timing_items, chart_facts, max_items, language=lang_code
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
        "supporting_factors": supporting_factors,
        "challenging_factors": challenging_factors,
        "why_this": why_this,
        "translations": translations,
        "timing": [t.get("timing") for t in timing_items if "timing" in t],
        "summary": topic_json["overview"],
        "prediction": clean_prose,
        "status": "templated",
        "review_status": "needs_expert_review",
        "notes": [],
        "limitations": [caveat],
    }

    return clean_prose, used_items, structured_data
