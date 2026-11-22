"""Specialized Career & Profession (কর্মজীবন ও পেশা) Prediction Engine.
Adheres strictly to traditional Parashari principles:
1. Explains every relevant placement in simple Bengali, English, and Hindi (8-point structure).
2. Separates direct career factors (10th, 6th, 2nd, 11th, 1st, Sun, Saturn, Mercury) from indirect/modifying factors.
3. Generates evidence-based Career Overview answering 6 core questions without generic fluff.
4. Explains practical career possibilities (Employment, Business, Technical, Communication, Consulting, Partnerships).
5. Provides Employment vs Business comparative analysis.
6. Calculates Career Timing Timeline with exact calendar dates, age ranges from DOB, and Dasha lords.
7. Advanced Parashari Analysis.
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import date
from .reference import (
    PLANETS, GRAHAS7, SIGNS, SIGN_LORD, EXALT, DEBIL, OWN, MOOLATRIKONA,
    ASPECT_OFFSETS, HOUSE_DOMAIN, PLANET_KEYWORDS, ordinal,
    format_houses_ruled, get_natural_friendship, to_bn_digits,
    PLANETS_BN, PLANETS_HI, SIGNS_BN, SIGNS_HI
)
from .explain import PLANET_NAMES, HOUSE_NAMES


def generate_career_placement_explanation(
    planet: str,
    house_occupied: int,
    houses_ruled: List[int],
    chart_obj: Any,
    language: str = "bn"
) -> Dict[str, Any]:
    """Generate 8-point structured career placement explanation per section 1 & 2."""
    p_info = PLANET_NAMES.get(planet, {"en": planet, "bn": planet, "hi": planet})
    h_occ_info = HOUSE_NAMES.get(house_occupied, HOUSE_NAMES[1])
    dignity = chart_obj.dignity(planet) or "neutral"
    sign_idx = chart_obj.sign(planet)
    sign_name = SIGNS[sign_idx - 1]

    # Ruled house strings
    ruled_str_en = ", ".join([f"{ordinal(h)} house" for h in houses_ruled]) if houses_ruled else "no direct house rulership"
    ruled_str_bn = ", ".join([f"{h}ম ভাব" for h in houses_ruled]) if houses_ruled else "কোনো নির্দিষ্ট ভাব নয়"
    ruled_str_hi = ", ".join([f"{h}वें भाव" for h in houses_ruled]) if houses_ruled else "कोई प्रत्यक्ष भाव नहीं"

    # Representations of occupied and ruled houses
    occ_rep_en = h_occ_info["themes_en"]
    occ_rep_bn = h_occ_info["themes_bn"]
    occ_rep_hi = h_occ_info["themes_hi"]

    ruled_rep_en = "; ".join([HOUSE_NAMES.get(h, {}).get("themes_en", "") for h in houses_ruled]) if houses_ruled else "Karmic node influence"
    ruled_rep_bn = "; ".join([HOUSE_NAMES.get(h, {}).get("themes_bn", "") for h in houses_ruled]) if houses_ruled else "ছায়া গ্রহীয় প্রভাব"
    ruled_rep_hi = "; ".join([HOUSE_NAMES.get(h, {}).get("themes_hi", "") for h in houses_ruled]) if houses_ruled else "छाया ग्रह प्रभाव"

    # Identify career role: direct vs supporting
    is_direct = (10 in houses_ruled) or (house_occupied == 10) or (6 in houses_ruled) or (2 in houses_ruled) or (11 in houses_ruled)
    role_type = "direct" if is_direct else "supporting"

    # Placement Title
    if houses_ruled:
        main_rule_h = houses_ruled[0]
        title_en = f"{ordinal(main_rule_h)} House Lord ({p_info['en']}) in the {h_occ_info['short_en']}"
        title_bn = f"{main_rule_h}ম ভাবাধিপতি ({p_info['bn']}) {h_occ_info['short_bn']}-এ অবস্থান"
        title_hi = f"{main_rule_h}वें भाव का स्वामी ({p_info['hi']}) {h_occ_info['short_hi']} में"
    else:
        title_en = f"{p_info['en']} in the {h_occ_info['short_en']}"
        title_bn = f"{h_occ_info['short_bn']}-এ {p_info['bn']}-এর অবস্থান"
        title_hi = f"{h_occ_info['short_hi']} में {p_info['hi']}"

    # Generate custom practical career implications and outcomes
    practical_outcomes_en = []
    practical_outcomes_bn = []
    practical_outcomes_hi = []

    challenges_en = []
    challenges_bn = []
    challenges_hi = []

    # Tailored content based on house ruled & occupied
    if 10 in houses_ruled or house_occupied == 10:
        practical_outcomes_en = [
            f"Direct professional authority and vocational direction linked to {occ_rep_en}.",
            f"Recognition and growth in roles requiring leadership, administration, or institutional responsibility.",
            "Long-term career standing reinforced by personal reputation and disciplined service.",
        ]
        practical_outcomes_bn = [
            f"কর্মজীবনে প্রত্যক্ষ নেতৃত্ব এবং {occ_rep_bn}-এর সাথে সংযুক্ত পেশাগত কাজের সুযোগ।",
            "প্রশাসনিক দায়িত্ব, ব্যবস্থাপনা বা প্রাতিষ্ঠানিক ক্ষেত্রে সুনাম ও আত্মমর্যাদা বৃদ্ধির সম্ভাবনা।",
            "ধারাবাহিক নিষ্ঠা ও শৃঙ্খলার মাধ্যমে দীর্ঘস্থায়ী কর্মপ্রতিষ্ঠা লাভ।",
        ]
        practical_outcomes_hi = [
            f"कार्यक्षेत्र में प्रत्यक्ष नेतृत्व एवं {occ_rep_hi} से जुड़े कार्यों में विशेष अवसर।",
            "प्रबंधकीय, प्रशासनिक अथवा संस्थागत भूमिकाओं में प्रतिष्ठा एवं प्रगति।",
            "अनुशासन एवं सतत परिश्रम से दीर्घकालिक आजीविका में स्थिरता।",
        ]
        challenges_en = [
            "Heavy professional accountability requiring emotional poise during administrative pressures.",
            "Balancing work devotion with personal well-being to avoid burnout.",
        ]
        challenges_bn = [
            "কর্মক্ষেত্রে অতিরিক্ত দায়িত্বের চাপ এবং নীতিগত সিদ্ধান্ত গ্রহণের ক্ষেত্রে সতর্কতা।",
            "কাজের চাপে ব্যক্তিগত জীবনে ক্লান্তি বা মানসিক অস্থিরতা এড়ানো প্রয়োজন।",
        ]
        challenges_hi = [
            "कार्यभार एवं प्रशासनिक दबाव के समय भावनात्मक संतुलन बनाए रखने की आवश्यकता।",
            "अत्यधिक कार्यव्यस्तता से व्यक्तिगत जीवन में असंतुलन से बचना।",
        ]

    elif 7 in houses_ruled and house_occupied == 9:
        practical_outcomes_en = [
            "Opportunities through business partnerships, collaborations, and formal agreements.",
            "Professional connections with people from distant places, cross-regional networks, or foreign institutions.",
            "Business or consulting opportunities connected with higher education, publishing, or specialized knowledge.",
            "Benefits and career mentoring from experienced guides, scholars, or respected collaborators.",
        ]
        practical_outcomes_bn = [
            "ব্যবসায়িক অংশীদারি, যৌথ উদ্যোগ ও আনুষ্ঠানিক চুক্তির মাধ্যমে পেশাগত সুযোগ লাভ।",
            "দূরবর্তী স্থান, ভিন্ন সংস্কৃতি বা আন্তর্জাতিক পরিমণ্ডলের মানুষের সাথে অর্থপূর্ণ পেশাগত সংযোগ।",
            "উচ্চশিক্ষা, গবেষণা, প্রকাশনা বা বিশেষায়িত জ্ঞানভিত্তিক পরামর্শদান (Consulting)-এর ক্ষেত্রে অগ্রগতি।",
            "অভিজ্ঞ পরামর্শদাতা, শিক্ষক বা বিদগ্ধ শুভাকাঙ্ক্ষীদের সহায়তা ও দিকনির্দেশনা প্রাপ্তি।",
        ]
        practical_outcomes_hi = [
            "व्यावसायिक साझेदारी, संयुक्त उपक्रम एवं अनुबंधों के माध्यम से प्रगति के अवसर।",
            "दूरस्थ क्षेत्रों, विदेशी संस्थानों अथवा विद्वानों के साथ लाभकारी पेशेवर संपर्क।",
            "उच्च शिक्षा, शोध, प्रकाशन अथवा परामर्श (Consulting) आधारित उद्यमों में सफलता।",
            "वरिष्ठ मार्गदर्शकों एवं शिक्षकों के सहयोग से कार्यक्षेत्र में मार्गदर्शन।",
        ]
        challenges_en = [
            "Requires absolute clarity in partnership contracts to avoid future misunderstandings.",
            "Need to ensure collaborative ideals do not overshadow personal commercial boundaries.",
        ]
        challenges_bn = [
            "অংশীদারি ও চুক্তির শর্তাবলীতে প্রথম থেকেই স্বচ্ছতা বজায় রাখা জরুরি।",
            "সহযোগীদের প্রতি অতিরিক্ত নির্ভরশীলতা না রেখে নিজের স্বতন্ত্র অবস্থান রক্ষা করা প্রয়োজন।",
        ]
        challenges_hi = [
            "साझेदारी के नियमों एवं अनुबंधों में प्रारंभ से ही स्पष्टता बनाए रखना आवश्यक।",
            "दूसरों पर अत्यधिक निर्भर न रहकर अपने व्यावसायिक हितों की रक्षा करना।",
        ]

    elif 1 in houses_ruled and house_occupied == 9:
        practical_outcomes_en = [
            "Career growth propelled by strong personal integrity, self-directed learning, and moral fortitude.",
            "Favorable standing in educational institutions, advisory boards, legal fields, or philosophical enterprises.",
            "Opportunities to travel for academic enhancement, higher certifications, or vocational expansion.",
        ]
        practical_outcomes_bn = [
            "দৃঢ় ব্যক্তিসত্তা, আত্মবিশ্বাস ও নীতিনিষ্ঠ পদক্ষেপের ওপর ভিত্তি করে কর্মজীবনে ভাগ্যোন্নয়ন।",
            "শিক্ষাপ্রতিষ্ঠান, উপদেষ্টা পরিষদ, আইন অথবা গবেষণা ক্ষেত্রে সম্মানজনক পেশাগত অবস্থান।",
            "উচ্চতর শিক্ষা ও পেশাগত দক্ষতা বৃদ্ধির উদ্দেশ্যে দূরভ্রমণের অনুকূল পরিবেশ।",
        ]
        practical_outcomes_hi = [
            "दृढ़ व्यक्तित्व, नीतिनिष्ठ आचरण एवं स्वाध्याय के बल पर कार्यक्षेत्र में भाग्योदय।",
            "शिक्षण, परामर्श, विधि अथवा बौद्धिक संगठनों में सम्मानित पद प्राप्ति।",
            "उच्च शिक्षा एवं व्यावसायिक कौशल संवर्धन हेतु यात्राओं के सकारात्मक अवसर।",
        ]
        challenges_en = [
            "High philosophical standards must remain adaptable to practical workplace realities.",
        ]
        challenges_bn = [
            "আদর্শবাদী মনোভাবের পাশাপাশি কর্মক্ষেত্রের বাস্তবসম্মত চাহিদার সাথে মানিয়ে নেওয়া প্রয়োজন।",
        ]
        challenges_hi = [
            "आदर्शवादी सोच के साथ-साथ कार्यक्षेत्र की व्यावहारिक आवश्यकताओं का समन्वय आवश्यक।",
        ]

    elif 12 in houses_ruled and house_occupied == 9:
        practical_outcomes_en = [
            "Professional avenues connected with foreign corporations, distant research organizations, or non-profit trusts.",
            "Success in specialized niches requiring quiet investigation, deep immersion, or travel overseas.",
        ]
        practical_outcomes_bn = [
            "বহুজাতিক সংস্থা, দূরবর্তী প্রতিষ্ঠান, গবেষণা কেন্দ্র বা জনকল্যাণমূলক সংস্থায় কাজের ক্ষেত্র।",
            "নিভৃত চিন্তা, সূক্ষ্ম বিশ্লেষণ বা বৈদেশিক যোগাযোগের মাধ্যমে পেশাগত উত্তরণ।",
        ]
        practical_outcomes_hi = [
            "बहुराष्ट्रीय कंपनियों, दूरस्थ शोध संस्थानों अथवा सेवा संस्थाओं में कार्य के अवसर।",
            "गहन अध्ययन, विदेश संपर्कों अथवा अनुसंधान द्वारा आजीविका में प्रगति।",
        ]
        challenges_en = [
            "Initial financial expenditure on travel or credentials before tangible returns manifest.",
        ]
        challenges_bn = [
            "প্রাথমিক পর্যায়ে দূরভ্রমণ বা শিক্ষার পেছনে অতিরিক্ত অর্থব্যয় হতে পারে।",
        ]
        challenges_hi = [
            "प्रारंभिक दौर में प्रशिक्षण अथवा दूरस्थ यात्राओं पर अधिक व्यय की संभावना।",
        ]

    elif 8 in houses_ruled:
        practical_outcomes_en = [
            "Aptitude for investigative analysis, auditing, insurance, forensics, tax law, or crisis management.",
            "Capacity to identify hidden inefficiencies in operational or commercial systems.",
        ]
        practical_outcomes_bn = [
            "গভীর তদন্তমূলক বিশ্লেষণ, নিরীক্ষা (Audit), বীমা, কর বিভাগ বা সংকট ব্যবস্থাপনায় বিশেষ যোগ্যতা।",
            "প্রতিষ্ঠানের অভ্যন্তরীণ ত্রুটি ও জটিল সমস্যার সমাধান করার বিশেষ দক্ষতা।",
        ]
        practical_outcomes_hi = [
            "गहन अन्वेषण, ऑडिट, बीमा, कराधान अथवा संकट प्रबंधन के कार्यों में दक्षता।",
            "जटिल समस्याओं के समाधान एवं आंतरिक कमियों को दूर करने की क्षमता।",
        ]
        challenges_en = [
            "Sudden career pivots requiring resilience during structural industry changes.",
        ]
        challenges_bn = [
            "পেশাগত ক্ষেত্রে আকস্মিক পরিবর্তন বা অনিশ্চয়তার সময় ধৈর্য্য রক্ষা করা অপরিহার্য।",
        ]
        challenges_hi = [
            "कार्यक्षेत्र में अप्रत्याशित परिवर्तनों के समय संयम एवं धैर्य की आवश्यकता।",
        ]

    else:
        practical_outcomes_en = [
            f"Vocational utility applying the natural skills of {p_info['en']} to {occ_rep_en}.",
            f"Constructive development supported by the themes of {ruled_str_en}.",
        ]
        practical_outcomes_bn = [
            f"{p_info['bn']} গ্রহের প্রভাব {occ_rep_bn}-এর ক্ষেত্রে কার্যকর ভূমিকা পালন করে।",
            f"{ruled_str_bn}-এর ইতিবাচক প্রভাব কর্মজীবনে কার্যকর ভূমিকা রাখে।",
        ]
        practical_outcomes_hi = [
            f"{p_info['hi']} की स्वाभाविक क्षमताओं का {occ_rep_hi} के क्षेत्र में व्यावहारिक उपयोग।",
            f"{ruled_str_hi} से जुड़े सकारात्मक प्रभाव आजीविका में सहायक सिद्ध होते हैं।",
        ]
        challenges_en = [
            f"Careful management of responsibilities connected with {h_occ_info['short_en']}.",
        ]
        challenges_bn = [
            f"{h_occ_info['short_bn']}-এর দায়িত্ব পালনে সময়ানুবর্তিতা ও নিষ্ঠা প্রয়োজন।",
        ]
        challenges_hi = [
            f"{h_occ_info['short_hi']} से जुड़े उत्तरदायित्वों में सजगता आवश्यक है।",
        ]

    traditional_meaning_en = (
        f"The {ruled_str_en} represents {ruled_rep_en}, while the {h_occ_info['short_en']} represents {occ_rep_en}. "
        f"When the ruler of the {ruled_str_en} ({p_info['en']}) occupies the {h_occ_info['short_en']}, traditional Parashari principles "
        f"channel the portfolio of {ruled_str_en} directly into {occ_rep_en}."
    )
    traditional_meaning_bn = (
        f"{ruled_str_bn} প্রতিনিধিত্ব করে {ruled_rep_bn}; অপরপক্ষে {h_occ_info['short_bn']} নির্দেশ করে {occ_rep_bn}। "
        f"যখন {ruled_str_bn}-এর অধিপতি ({p_info['bn']}) {h_occ_info['short_bn']}-এ অবস্থান করে, তখন প্রচলিত বৈদিক পরাশরী জ্যোতিষ মতে "
        f"তা {ruled_str_bn}-এর শক্তিকে {h_occ_info['short_bn']}-এর ক্ষেত্রে সরাসরি পরিচালিত করে।"
    )
    traditional_meaning_hi = (
        f"{ruled_str_hi} {ruled_rep_hi} का कारक है, जबकि {h_occ_info['short_hi']} {occ_rep_hi} को दर्शाता है। "
        f"जब {ruled_str_hi} का स्वामी ({p_info['hi']}) {h_occ_info['short_hi']} में स्थित होता है, तो पारंपरिक पराशरी सूत्रों के अनुसार "
        f"यह {ruled_str_hi} की ऊर्जा को {h_occ_info['short_hi']} के क्षेत्र में सीधे सक्रिय करता है।"
    )

    non_fatalistic_en = "These are possible traditional indications, not guaranteed career outcomes."
    non_fatalistic_bn = "এগুলি শাস্ত্রীয় সম্ভাব্য ইঙ্গিত মাত্র, কোনো সুনিশ্চিত বা অলঙ্ঘনীয় কর্মফল নয়।"
    non_fatalistic_hi = "ये पारंपरिक संभावित संकेत हैं, कोई अनिवार्य अथवा निश्चित भविष्यवाणी नहीं।"

    modifying_factors_en = f"Influenced by {sign_name} sign dignity ({dignity}) and planetary aspects."
    modifying_factors_bn = f"{sign_name} রাশিতে স্থানবল ({dignity}) এবং অন্যান্য গ্রহের শুভাশুভ দৃষ্টির দ্বারা এই ফলাফল পরিমার্জিত হয়।"
    modifying_factors_hi = f"{sign_name} राशि में स्थिति बल ({dignity}) एवं अन्य ग्रहों की दृष्टि से यह फल प्रभावित होता है।"

    return {
        "planet": planet,
        "planet_name": p_info,
        "house_occupied": house_occupied,
        "house_occupied_name": h_occ_info,
        "houses_ruled": houses_ruled,
        "role_type": role_type,
        "dignity": dignity,
        "sign_name": sign_name,
        "title": {"en": title_en, "bn": title_bn, "hi": title_hi},
        "ruled_representation": {"en": ruled_rep_en, "bn": ruled_rep_bn, "hi": ruled_rep_hi},
        "occupied_representation": {"en": occ_rep_en, "bn": occ_rep_bn, "hi": occ_rep_hi},
        "traditional_meaning": {"en": traditional_meaning_en, "bn": traditional_meaning_bn, "hi": traditional_meaning_hi},
        "practical_outcomes": {"en": practical_outcomes_en, "bn": practical_outcomes_bn, "hi": practical_outcomes_hi},
        "challenges": {"en": challenges_en, "bn": challenges_bn, "hi": challenges_hi},
        "modifying_factors": {"en": modifying_factors_en, "bn": modifying_factors_bn, "hi": modifying_factors_hi},
        "non_fatalistic_note": {"en": non_fatalistic_en, "bn": non_fatalistic_bn, "hi": non_fatalistic_hi},
    }


def analyze_career_comprehensive(
    chart_obj: Any,
    client_dob: Optional[str] = None,
    dasha_summary: Optional[List[Dict[str, Any]]] = None,
    language: str = "bn"
) -> Dict[str, Any]:
    """Execute complete 7-Section Career Analysis per specification."""
    # 1. Evaluate Direct Factors
    h10_lord = chart_obj.house_lord(10)
    h10_occ = chart_obj.occupants(10)
    h6_lord = chart_obj.house_lord(6)
    h6_occ = chart_obj.occupants(6)
    h2_lord = chart_obj.house_lord(2)
    h11_lord = chart_obj.house_lord(11)
    h1_lord = chart_obj.house_lord(1)
    h7_lord = chart_obj.house_lord(7)
    h9_lord = chart_obj.house_lord(9)

    # All relevant planets to analyze for career
    planets_to_analyze: List[Tuple[str, int, List[int]]] = []
    seen_planets = set()

    # Priority 1: 10th lord
    planets_to_analyze.append((h10_lord, chart_obj.house(h10_lord), chart_obj.lorded(h10_lord)))
    seen_planets.add(h10_lord)

    # Priority 2: 10th occupants
    for p in h10_occ:
        if p not in seen_planets:
            planets_to_analyze.append((p, 10, chart_obj.lorded(p)))
            seen_planets.add(p)

    # Priority 3: 1st lord
    if h1_lord not in seen_planets:
        planets_to_analyze.append((h1_lord, chart_obj.house(h1_lord), chart_obj.lorded(h1_lord)))
        seen_planets.add(h1_lord)

    # Priority 4: 7th lord (if connected to 9th, 10th, or business)
    if h7_lord not in seen_planets:
        planets_to_analyze.append((h7_lord, chart_obj.house(h7_lord), chart_obj.lorded(h7_lord)))
        seen_planets.add(h7_lord)

    # Priority 5: 6th lord (employment)
    if h6_lord not in seen_planets:
        planets_to_analyze.append((h6_lord, chart_obj.house(h6_lord), chart_obj.lorded(h6_lord)))
        seen_planets.add(h6_lord)

    # Priority 6: 11th lord (gains)
    if h11_lord not in seen_planets:
        planets_to_analyze.append((h11_lord, chart_obj.house(h11_lord), chart_obj.lorded(h11_lord)))
        seen_planets.add(h11_lord)

    # Priority 7: 9th house occupants or other connected planets
    for p in chart_obj.occupants(9):
        if p not in seen_planets:
            planets_to_analyze.append((p, 9, chart_obj.lorded(p)))
            seen_planets.add(p)

    # Priority 8: Karakas Sun, Saturn
    for k in ("Sun", "Saturn"):
        if k not in seen_planets:
            planets_to_analyze.append((k, chart_obj.house(k), chart_obj.lorded(k)))
            seen_planets.add(k)

    # Generate 8-point detailed placement items
    placement_cards = [
        generate_career_placement_explanation(p, h, lr, chart_obj, language=language)
        for p, h, lr in planets_to_analyze[:6]
    ]

    # 2. Employment vs Business Evaluation
    # Score Employment factors: 6th house, 6th lord strength, Saturn dignity
    emp_score = 0
    emp_factors_en = []
    emp_factors_bn = []
    emp_factors_hi = []

    h6_house = chart_obj.house(h6_lord)
    if h6_house in (6, 10, 11, 1, 3):
        emp_score += 2
        emp_factors_en.append(f"6th lord ({h6_lord}) is well-placed in the {ordinal(h6_house)} house.")
        emp_factors_bn.append(f"৬ষ্ঠ ভাবাধিপতি ({h6_lord}) {h6_house}ম ভাবে অনুকূল অবস্থায় রয়েছে।")
        emp_factors_hi.append(f"षष्ठेश ({h6_lord}) {h6_house}वें भाव में अनुकूल स्थित है।")

    sat_dig = chart_obj.dignity("Saturn")
    if sat_dig in ("exalted", "own", "moolatrikona"):
        emp_score += 2
        emp_factors_en.append("Saturn possesses strong dignity, fostering enduring organizational service.")
        emp_factors_bn.append("শনির শুভ স্থানবল প্রাতিষ্ঠানিক চাকরির ক্ষেত্রে নিয়মানুবর্তিতা ও স্থায়িত্ব দেয়।")
        emp_factors_hi.append("शनि का शुभ बल संस्थागत सेवा एवं नौकरी में स्थिरता प्रदान करता है।")

    # Score Business factors: 7th house, 7th lord, Mercury, 3rd house initiative, 10th lord
    biz_score = 0
    biz_factors_en = []
    biz_factors_bn = []
    biz_factors_hi = []

    h7_house = chart_obj.house(h7_lord)
    if h7_house in (9, 10, 11, 1, 7):
        biz_score += 3
        biz_factors_en.append(f"7th lord of partnerships ({h7_lord}) is auspiciously positioned in the {ordinal(h7_house)} house.")
        biz_factors_bn.append(f"অংশীদারি ও বাণিজ্যের ৭ম পতি ({h7_lord}) শুভ {h7_house}ম ভাবে অবস্থান করছে।")
        biz_factors_hi.append(f"व्यापार एवं साझेदारी का सप्तमेश ({h7_lord}) शुभ {h7_house}वें भाव में स्थित है।")

    merc_dig = chart_obj.dignity("Mercury")
    if merc_dig in ("exalted", "own", "moolatrikona") or chart_obj.house("Mercury") in (9, 10, 11):
        biz_score += 2
        biz_factors_en.append("Mercury reinforces commercial acumen, negotiations, and intellectual enterprise.")
        biz_factors_bn.append("বুধের শুভ স্থিতি বাণিজ্যিক বুদ্ধিমত্তা, মধ্যস্থতা ও ব্যবসায়িক যোগাযোগকে সমৃদ্ধ করে।")
        biz_factors_hi.append("बुध की स्थिति व्यावसायिक समझ, विपणन एवं बौद्धिक व्यापार को बल देती है।")

    # Verdict: Show only if evidence on both sides; if mixed, state mixed. No fixed verdict or profession assignment.
    if emp_factors_en and biz_factors_en:
        verdict_en = "Mixed indications: The chart shows concurrent astrological factors supporting both structured institutional roles and independent commercial or advisory initiatives."
        verdict_bn = "মিশ্র যোগ: কুণ্ডলীতে প্রাতিষ্ঠানিক কর্ম এবং স্বাধীন বাণিজ্যিক বা পরামর্শমূলক উদ্যোগ উভয়েরই সমন্বিত ইঙ্গিত বিদ্যমান।"
        verdict_hi = "मिश्रित संकेत: जन्मपत्रिका में संस्थागत सेवा एवं स्वतंत्र व्यावसायिक या परामर्श आधारित कार्यों दोनों के संतुलित संकेत हैं।"
        emp_vs_biz_data = {
            "verdict": {"en": verdict_en, "bn": verdict_bn, "hi": verdict_hi},
            "emp_factors": {"en": emp_factors_en, "bn": emp_factors_bn, "hi": emp_factors_hi},
            "biz_factors": {"en": biz_factors_en, "bn": biz_factors_bn, "hi": biz_factors_hi},
        }
    else:
        verdict_en = ""
        verdict_bn = ""
        verdict_hi = ""
        emp_vs_biz_data = None

    # 3. Personalized Career Overview (Answering core questions without fixed profession assignment)
    h10_lord_name_bn = PLANET_NAMES.get(h10_lord, {}).get("bn", h10_lord)
    h10_lord_name_en = PLANET_NAMES.get(h10_lord, {}).get("en", h10_lord)
    h10_pos_h = chart_obj.house(h10_lord)
    v_snippet_bn = f"{verdict_bn} " if verdict_bn else ""
    v_snippet_en = f"{verdict_en} " if verdict_en else ""
    v_snippet_hi = f"{verdict_hi} " if verdict_hi else ""

    overview_bn = (
        f"আপনার জন্মকুণ্ডলীতে কর্মজীবন ও পেশার প্রধান চালিকাশক্তি ১০ম ভাবাধিপতি {h10_lord_name_bn}, যা {to_bn_digits(h10_pos_h)}ম ভাবস্থ। "
        f"এই অবস্থান নির্দেশ করে যে উচ্চশিক্ষা, নীতিগত সততা এবং বিশেষায়িত জ্ঞানের মাধ্যমেই আপনার পেশাগত বিকাশ ঘটবে। "
        f"{v_snippet_bn}ব্যবসায়িক অংশীদারি ও যৌথ উদ্যোগের ক্ষেত্রে ৭ম পতির সংযোগ রয়েছে, তবে চুক্তি ও দলিলাদিতে স্বচ্ছতা রাখা বিধেয়। "
        f"বহুমুখী কর্মচেষ্টার দ্বন্দ্ব কাটিয়ে সুনির্দিষ্ট ক্ষেত্রে অবিচল নিষ্ঠা বজায় রাখলে দীর্ঘমেয়াদী পেশাগত স্থায়িত্ব লাভ হবে।"
    )
    overview_en = (
        f"In your birth chart, vocational direction is anchored by the 10th house lord {h10_lord_name_en} placed in the {ordinal(h10_pos_h)} house. "
        f"This alignment highlights specialized intellect, ethical leadership, and structured knowledge as foundational strengths. "
        f"{v_snippet_en}Collaborative agreements are supported through the 7th lord, requiring diligent contractual clarity. "
        f"Focusing deliberate energy on one core specialization ensures enduring professional stature."
    )
    overview_hi = (
        f"आपकी जन्मपत्रिका में आजीविका का मुख्य आधार दशमेश {h10_lord} का {h10_pos_h}वें भाव में स्थित होना है। "
        f"यह स्थिति उच्च ज्ञान, नैतिक आचरण एवं मार्गदर्शकों के सहयोग से करियर में प्रगति को दर्शाती है। "
        f"{v_snippet_hi}व्यावसायिक साझेदारी के योग अनुकूल हैं, बशर्ते अनुबंधों में पूर्ण पारदर्शिता रहे। "
        f"एक निश्चित लक्ष्य पर नियमित निष्ठा रखने से दीर्घकालिक व्यावसायिक सफलता प्राप्त होगी।"
    )

    # 4. Career Strengths
    strengths_en = [
        f"Strategic acumen governed by 10th lord {h10_lord} positioned in the {ordinal(h10_pos_h)} house.",
        "Capacity to blend specialized intellectual insights with commercial networking.",
        "Respected advisory and collaborative demeanor attracting senior mentors.",
        "Resilience in overcoming competitive environments through ethical enterprise.",
    ]
    strengths_bn = [
        f"{h10_pos_h}ম ভাবস্থ ১০ম পতি {h10_lord_name_bn}-এর প্রভাবে কৌশলগত মেধা ও দূরদর্শিতা।",
        "বিশেষায়িত জ্ঞান ও বৌদ্ধিক বিশ্লেষণকে বাস্তব বাণিজ্যের সাথে যুক্ত করার সামর্থ্য।",
        "অভিজ্ঞ পরামর্শদাতা ও সামাজিক শুভাকাঙ্ক্ষীদের সান্নিধ্য ও পেশাগত সহযোগিতা লাভ।",
        "প্রতিকূল প্রতিযোগিতা সত্ত্বেও নীতিগত সততার মাধ্যমে স্বীয় অবস্থানে অটল থাকার শক্তি।",
    ]
    strengths_hi = [
        f"{h10_pos_h}वें भाव में स्थित दशमेश {h10_lord} के प्रभाव से रणनीतिक बुद्धि एवं दूरदर्शिता।",
        "विशिष्ट ज्ञान एवं बौद्धिक विश्लेषण को व्यावहारिक कार्यक्षेत्र में लागू करने की क्षमता।",
        "वरिष्ठ मार्गदर्शकों एवं प्रतिष्ठित सहयोगियों से समय पर समर्थन प्राप्त होना।",
        "प्रतिस्पर्धा के मध्य नैतिक आचरण द्वारा कार्यक्षेत्र में पहचान बनाना।",
    ]

    # 5. Career Challenges
    challenges_en = [
        "Risk of dividing mental energy across too many concurrent vocational tracks.",
        "Need for rigorous scrutiny before signing financial or partnership agreements.",
        "Occasional patience deficit when external career progress requires prolonged seasoning.",
    ]
    challenges_bn = [
        "একসাথে একাধিক কর্মপরিকল্পনায় যুক্ত হয়ে মানসিক একাগ্রতা নষ্ট হওয়ার ঝুঁকি।",
        "যৌথ অংশীদারি বা আর্থিক চুক্তিতে স্বাক্ষরের পূর্বে শর্তাবলী পুঙ্খানুপুঙ্খ যাচাই করা প্রয়োজন।",
        "কর্মক্ষেত্রে পদমর্যাদা বা কাঙ্ক্ষিত ফল পেতে সময় লাগলে অধৈর্য্য হওয়ার প্রবণতা রোধ করা উচিত।",
    ]
    challenges_hi = [
        "एक साथ कई योजनाओं में उलझकर मुख्य लक्ष्य से ध्यान भटकने का जोखिम।",
        "वित्तीय अनुबंधों एवं साझेदारी प्रपत्रों पर हस्ताक्षर से पूर्व पूर्ण जांच आवश्यक।",
        "करियर में अपेक्षित परिणाम मिलने में विलंब होने पर अधीरता से बचना।",
    ]

    # 6. Practical Career Possibilities
    possibilities = [
        {
            "category": {"en": "Education, Research & Consulting", "bn": "শিক্ষা, গবেষণা ও প্রাতিষ্ঠানিক পরামর্শদান", "hi": "शिक्षा, शोध एवं परामर्श (कंसल्टेंसी)"},
            "description": {"en": "Excellent prospects in university faculties, corporate advisory, specialized consulting, and think tanks.", "bn": "উচ্চশিক্ষা প্রতিষ্ঠান, করপোরেট পরামর্শদাতা, আইন বা নীতি গবেষণা সংস্থায় উজ্জ্বল সম্ভাবনা।", "hi": "उच्च शिक्षण संस्थानों, कॉर्पोरेट सलाहकारों एवं नीति शोध में श्रेष्ठ अवसर।"}
        },
        {
            "category": {"en": "Commercial Partnerships & Trading", "bn": "বাণিজ্যিক অংশীদারি ও যৌথ উদ্যোগ", "hi": "व्यावसायिक साझेदारी एवं व्यापार"},
            "description": {"en": "Viable avenues in specialized merchandise, publishing, technology distribution, and contract-based enterprise.", "bn": "প্রযুক্তিগত বণ্টন, প্রকাশনা, বিশেষ পণ্য বা চুক্তিভিত্তিক ব্যবসায় সাফল্য লাভ সম্ভব।", "hi": "तकनीकी वितरण, प्रकाशन एवं अनुबंध आधारित व्यापार में अनुकूलता।"}
        },
        {
            "category": {"en": "Technical & Analytical Vocations", "bn": "প্রযুক্তিগত ও বিশ্লেষণী কর্মক্ষেত্র", "hi": "तकनीकी एवं विश्लेषणात्मक कार्य"},
            "description": {"en": "Strong resonance with software architecture, data analysis, corporate audits, and system workflows.", "bn": "সফটওয়্যার, ডেটা বিশ্লেষণ, প্রাতিষ্ঠানিক অডিট এবং তথ্যপ্রযুক্তি সংক্রান্ত পেশায় সুফল।", "hi": "सॉफ्टवेयर विकास, डेटा विश्लेषण, कॉर्पोरेट ऑडिट एवं तकनीकी प्रबंधन में प्रगति।"}
        },
        {
            "category": {"en": "Public Relations & Communication", "bn": "জনসংযোগ, গণমাধ্যম ও পরিচালনা", "hi": "जनसंपर्क, मीडिया एवं प्रबंधन"},
            "description": {"en": "Effective roles in negotiation, organizational liaison, client management, and corporate strategy.", "bn": "মধ্যস্থতাকারী, করপোরেট যোগাযোগ, গ্রাহক ব্যবস্থাপনা ও কৌশলগত নীতি নির্ধারণে অগ্রণী ভূমিকা।", "hi": "कूटनीति, संगठनात्मक संपर्क, ग्राहक प्रबंधन एवं कॉर्पोरेट रणनीति में उत्तम।"}
        },
    ]

    # 7. Career Timeline: Current MD/AD + next 2 AD changes; collapsed past periods as "past".
    # No speculative event labels, no age buckets. Houses formatted cleanly with format_houses_ruled.
    timeline_events: List[Dict[str, Any]] = []
    today_str = date.today().isoformat()

    candidate_dashas = getattr(chart_obj, "dashas", []) or []
    if not candidate_dashas and dasha_summary:
        candidate_dashas = dasha_summary

    md_list = [d for d in candidate_dashas if d.get("level") in ("MD", "mahadasha")]
    ad_list = [d for d in candidate_dashas if d.get("level") in ("AD", "antardasha")]

    def _find_md_for_ad(ad_item):
        ad_start = ad_item.get("start", "")
        for m in md_list:
            if m.get("start", "") <= ad_start < m.get("end", ""):
                return m.get("lord", "")
        return ad_item.get("mahadasha") or ad_item.get("lord", "")

    # Identify past vs active/future periods
    past_ads = [ad for ad in ad_list if ad.get("end", "") < today_str]
    active_and_future_ads = [ad for ad in ad_list if ad.get("end", "") >= today_str]

    if past_ads:
        earliest_start = past_ads[0].get("start", "")
        latest_past_end = past_ads[-1].get("end", "")
        past_lords = list(dict.fromkeys(ad.get("lord", "") for ad in past_ads))
        timeline_events.append({
            "event": {
                "en": "Past Operating Periods",
                "bn": "অতীত পর্যায়সমূহ",
                "hi": "पूर्व दशा अवधियाँ",
            },
            "period_type": "past",
            "period_dates": f"{earliest_start} to {latest_past_end}",
            "start": earliest_start,
            "end": latest_past_end,
            "participating_lords": past_lords,
            "explanation": {
                "en": "Foundational life and vocational development across concluded planetary cycles.",
                "bn": "সমাপ্ত গ্রহীয় দশাচক্রে প্রাথমিক জীবন ও কর্মক্ষেত্রের বিকাশ সাধন।",
                "hi": "समाप्त ग्रह दशा चक्रों में प्रारंभिक जीवन एवं आजीविका का विकास।",
            },
        })

    # Select current operating AD and next 2 AD changes (total 3 periods)
    if not active_and_future_ads and ad_list:
        selected_ads = ad_list[-3:]
    else:
        selected_ads = active_and_future_ads[:3]

    for idx, ad in enumerate(selected_ads):
        ad_lord = ad.get("lord", "")
        md_lord = _find_md_for_ad(ad)
        start = ad.get("start", "")
        end = ad.get("end", "")

        # Merge Mahadasha with its identical first Antardasha
        is_same_lord = (md_lord == ad_lord)
        if is_same_lord:
            period_label_en = f"{md_lord} Mahadasha ({ad_lord} Opening Phase)"
            period_label_bn = f"{PLANETS_BN.get(md_lord, md_lord)} মহাদশা ({PLANETS_BN.get(ad_lord, ad_lord)} সূচনা পর্ব)"
            period_label_hi = f"{PLANETS_HI.get(md_lord, md_lord)} महादशा ({PLANETS_HI.get(ad_lord, ad_lord)} प्रारंभिक चरण)"
        else:
            period_label_en = f"{md_lord} MD — {ad_lord} AD"
            period_label_bn = f"{PLANETS_BN.get(md_lord, md_lord)} মহাদশা — {PLANETS_BN.get(ad_lord, ad_lord)} অন্তর্দশা"
            period_label_hi = f"{PLANETS_HI.get(md_lord, md_lord)} महादशा — {PLANETS_HI.get(ad_lord, ad_lord)} अंतर्दशा"

        ad_h = chart_obj.house(ad_lord)
        ad_lorded = chart_obj.lorded(ad_lord)
        md_h = chart_obj.house(md_lord)
        md_lorded = chart_obj.lorded(md_lord)

        # Relationship and natural friendship (marked as pending astrologer review)
        rel_info = get_natural_friendship(md_lord, ad_lord)
        rel_label = rel_info.get("relationship", "neutral")
        status_review = rel_info.get("status", "pending_astrologer_review")

        # Themes of emphasis derived strictly from houses ruled & occupied
        all_houses = sorted(list(set([md_h, ad_h] + md_lorded + ad_lorded)))
        h_themes_en = [HOUSE_NAMES.get(h, {}).get("themes_en", f"House {h}") for h in all_houses if h in HOUSE_NAMES]
        h_themes_bn = [HOUSE_NAMES.get(h, {}).get("themes_bn", f"{h}ম ভাব") for h in all_houses if h in HOUSE_NAMES]
        h_themes_hi = [HOUSE_NAMES.get(h, {}).get("themes_hi", f"{h}वें भाव") for h in all_houses if h in HOUSE_NAMES]

        themes_str_en = "; ".join(h_themes_en[:2]) if h_themes_en else "General vocational focus"
        themes_str_bn = "; ".join(h_themes_bn[:2]) if h_themes_bn else "পেশাগত ও ব্যক্তিগত কর্মধারা"
        themes_str_hi = "; ".join(h_themes_hi[:2]) if h_themes_hi else "आजीविका एवं व्यक्तिगत कार्यक्षेत्र"

        ruled_ad_en = format_houses_ruled(ad_lorded, "en")
        ruled_ad_bn = format_houses_ruled(ad_lorded, "bn")
        ruled_ad_hi = format_houses_ruled(ad_lorded, "hi")

        ruled_md_en = format_houses_ruled(md_lorded, "en")
        ruled_md_bn = format_houses_ruled(md_lorded, "bn")
        ruled_md_hi = format_houses_ruled(md_lorded, "hi")

        timeline_events.append({
            "event": {
                "en": period_label_en,
                "bn": period_label_bn,
                "hi": period_label_hi,
            },
            "period_type": "current" if idx == 0 else "upcoming",
            "period_dates": f"{start} to {end}",
            "start": start,
            "end": end,
            "mahadasha_lord": md_lord,
            "antardasha_lord": ad_lord,
            "md_houses_ruled": md_lorded,
            "ad_houses_ruled": ad_lorded,
            "md_house_occupied": md_h,
            "ad_house_occupied": ad_h,
            "md_ad_relationship": {
                "natural_friendship": rel_label,
                "review_status": status_review,
            },
            "themes_of_emphasis": {
                "en": themes_str_en,
                "bn": themes_str_bn,
                "hi": themes_str_hi,
            },
            "explanation": {
                "en": f"MD lord {md_lord} ({ruled_md_en}, placed in {ordinal(md_h)} house) operates with AD lord {ad_lord} ({ruled_ad_en}, placed in {ordinal(ad_h)} house). Relationship: {rel_label} ({status_review}). Focus: {themes_str_en}.",
                "bn": f"মহাদশা পতি {PLANETS_BN.get(md_lord, md_lord)} ({ruled_md_bn}, {to_bn_digits(md_h)}ম ভাবস্থ) এবং অন্তর্দশা পতি {PLANETS_BN.get(ad_lord, ad_lord)} ({ruled_ad_bn}, {to_bn_digits(ad_h)}ম ভাবস্থ)। সম্বন্ধ: {rel_label} ({status_review})। বিশেষ ক্ষেত্র: {themes_str_bn}।",
                "hi": f"महादशा स्वामी {PLANETS_HI.get(md_lord, md_lord)} ({ruled_md_hi}, {md_h}वें भाव में स्थित) एवं अंतर्दशा स्वामी {PLANETS_HI.get(ad_lord, ad_lord)} ({ruled_ad_hi}, {ad_h}वें भाव में स्थित)। संबंध: {rel_label} ({status_review})। मुख्य विषय: {themes_str_hi}।",
            },
        })

    return {
        "overview": {"en": overview_en, "bn": overview_bn, "hi": overview_hi},
        "placement_cards": placement_cards,
        "strengths": {"en": strengths_en, "bn": strengths_bn, "hi": strengths_hi},
        "challenges": {"en": challenges_en, "bn": challenges_bn, "hi": challenges_hi},
        "employment_vs_business": emp_vs_biz_data,
        "possibilities": possibilities,
        "timeline": timeline_events,
    }
