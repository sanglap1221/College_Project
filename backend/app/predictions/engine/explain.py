"""Rule Explanation Mapping System and Human-Readable Translation Engine.
Adheres strictly to Jyotish Rulebook v2 Section 20 & 21.

Translates technical rule IDs (e.g. HL-H05-IN-H09, PH-KETU-H11, DG-SUN-EXALTED)
into clear, simple, human-understandable explanations in English, Bengali, and Hindi,
while preserving internal rule IDs and conditions for the Advanced Astrologer view.
"""

import re
from typing import Any, Dict, List, Optional
from .reference import PLANETS

PLANET_NAMES = {
    "Sun": {"en": "Sun", "bn": "রবি (সূর্য)", "hi": "सूर्य"},
    "Moon": {"en": "Moon", "bn": "চন্দ্র", "hi": "चन्द्र"},
    "Mars": {"en": "Mars", "bn": "মঙ্গল", "hi": "मंगल"},
    "Mercury": {"en": "Mercury", "bn": "বুধ", "hi": "बुध"},
    "Jupiter": {"en": "Jupiter", "bn": "বৃহস্পতি", "hi": "गुरु (बृहस्पति)"},
    "Venus": {"en": "Venus", "bn": "শুক্র", "hi": "शुक्र"},
    "Saturn": {"en": "Saturn", "bn": "শনি", "hi": "शनि"},
    "Rahu": {"en": "Rahu", "bn": "রাহু", "hi": "राहु"},
    "Ketu": {"en": "Ketu", "bn": "কেতু", "hi": "केतु"},
}

HOUSE_NAMES = {
    1: {
        "en": "1st house (temperament, vitality and self-agency)",
        "bn": "১ম ভাব (তনু ভাব — ব্যক্তিত্ব, শারীরিক শক্তি ও আত্মপ্রকাশ)",
        "hi": "प्रथम भाव (तनु भाव — व्यक्तित्व, आत्मबल एवं शारीरिक स्वास्थ्य)",
        "short_en": "1st house",
        "short_bn": "১ম ভাব",
        "short_hi": "प्रथम भाव",
        "themes_en": "temperament, physical vitality, self-agency and individual expression",
        "themes_bn": "ব্যক্তিত্ব, শারীরিক উদ্যম, আত্মবিশ্বাস ও সামগ্রিক জীবনশক্তি",
        "themes_hi": "व्यक्तित्व, शारीरिक ऊर्जा, आत्मबल एवं व्यक्तिगत अभिव्यक्ति",
    },
    2: {
        "en": "2nd house (family, speech and accumulated wealth)",
        "bn": "২য় ভাব (ধন ভাব — সম্পদ, পরিবার, বাকশক্তি ও সঞ্চয়)",
        "hi": "द्वितीय भाव (धन भाव — संचित धन, कुटुंब एवं वाणी)",
        "short_en": "2nd house",
        "short_bn": "২য় ভাব",
        "short_hi": "द्वितीय भाव",
        "themes_en": "accumulated wealth, family lineage, speech clarity and financial stability",
        "themes_bn": "সঞ্চিত ধন, পারিবারিক সংহতি, বাকপটুতা ও আর্থিক নিরাপত্তা",
        "themes_hi": "संचित धन, पारिवारिक सुख, वाणी एवं वित्तीय स्थिरता",
    },
    3: {
        "en": "3rd house (courage, effort, communications and siblings)",
        "bn": "৩য় ভাব (সহজ ভাব — পরাক্রম, উদ্যম, যোগাযোগ ও ভ্রাতাভগ্নী)",
        "hi": "तृतीय भाव (सहज भाव — पराक्रम, साहस, संवाद एवं भाई-बहन)",
        "short_en": "3rd house",
        "short_bn": "৩য় ভাব",
        "short_hi": "तृतीय भाव",
        "themes_en": "courage, personal initiative, technical skills and communications",
        "themes_bn": "সাহস, নিজস্ব উদ্যোগ, যোগাযোগ ও ব্যবহারিক দক্ষতা",
        "themes_hi": "साहस, व्यक्तिगत प्रयास, संवाद एवं व्यावहारिक कौशल",
    },
    4: {
        "en": "4th house (home, inner peace, mother and foundational learning)",
        "bn": "৪র্থ ভাব (সুখ ভাব — গৃহ, মাতৃস্নেহ, মানসিক শান্তি ও প্রাথমিক বিদ্যা)",
        "hi": "चतुर्थ भाव (सुख भाव — गृह, माता, मानसिक शांति एवं प्राथमिक विद्या)",
        "short_en": "4th house",
        "short_bn": "৪র্থ ভাব",
        "short_hi": "चतुर्थ भाव",
        "themes_en": "domestic stability, emotional contentment, home environment and education",
        "themes_bn": "গৃহসুখ, মানসিক স্বস্তি, পারিবারিক আশ্রয় ও প্রাথমিক শিক্ষা",
        "themes_hi": "घरेलू स्थिरता, मानसिक शांति, पारिवारिक वातावरण एवं आधारभूत शिक्षा",
    },
    5: {
        "en": "5th house (intelligence, education, creativity and past merits)",
        "bn": "৫ম ভাব (বুদ্ধি ও সন্তান ভাব — মেধা, বিদ্যালাভ, সৃজনশীলতা ও পূর্বপুণ্য)",
        "hi": "पंचम भाव (संतान एवं बुद्धि भाव — मेधा, विद्या, रचनात्मकता एवं पूर्व पुण्य)",
        "short_en": "5th house",
        "short_bn": "৫ম ভাব",
        "short_hi": "पंचम भाव",
        "themes_en": "intelligence, creative intellect, higher education and auspicious discernment",
        "themes_bn": "শিক্ষা, বুদ্ধিমত্তা, সৃজনশীল উদ্ভাবন ও পূর্ববর্তী শুভ কর্মফল",
        "themes_hi": "बुद्धि, विद्या, रचनात्मक चिंतन एवं पूर्व संचित पुण्य",
    },
    6: {
        "en": "6th house (service, routines, contest and overcoming obstacles)",
        "bn": "৬ষ্ঠ ভাব (রিপু ভাব — কর্মতৎপরতা, প্রতিযোগিতা, সেবা ও বাধা উত্তরণ)",
        "hi": "षष्ठ भाव (शत्रु/रोग भाव — सेवा, प्रतियोगिता, कर्मठता एवं बाधा निवारण)",
        "short_en": "6th house",
        "short_bn": "৬ষ্ঠ ভাব",
        "short_hi": "षष्ठ भाव",
        "themes_en": "problem-solving, service, professional competition and health discipline",
        "themes_bn": "প্রতিযোগিতা মোকাবিলা, কর্মশৃঙ্খলা, সেবা ও স্বাস্থ্যসচেতনতা",
        "themes_hi": "समस्या समाधान, सेवा, पेशेवर प्रतिस्पर्धा एवं स्वास्थ्य अनुशासन",
    },
    7: {
        "en": "7th house (partnerships, marriage and significant agreements)",
        "bn": "৭ম ভাব (জায়া ভাব — দাম্পত্য, অংশীদারি ও সামাজিক চুক্তি)",
        "hi": "सप्तम भाव (जाया भाव — दांपत्य, साझेदारी एवं सामाजिक अनुबंध)",
        "short_en": "7th house",
        "short_bn": "৭ম ভাব",
        "short_hi": "सप्तम भाव",
        "themes_en": "committed relationships, marriage, business partnerships and public contracts",
        "themes_bn": "দাম্পত্য জীবন, দীর্ঘস্থায়ী অংশীদারি, পারস্পরিক বোঝাপড়া ও সামাজিক চুক্তি",
        "themes_hi": "वैवाहिक जीवन, व्यावसायिक साझेदारी एवं महत्वपूर्ण सामाजिक अनुबंध",
    },
    8: {
        "en": "8th house (transformation, shared resources and research)",
        "bn": "৮ম ভাব (রন্ধ্র ভাব — পরিবর্তন, নিগূঢ় বিষয় ও সংকট উত্তরণ)",
        "hi": "अष्टम भाव (परिवर्तन, गूढ़ रहस्य एवं आकस्मिक लाभ)",
        "short_en": "8th house",
        "short_bn": "৮ম ভাব",
        "short_hi": "अष्टम भाव",
        "themes_en": "inner transformation, research depth, crisis resilience and shared assets",
        "themes_bn": "মনস্তাত্ত্বিক রূপান্তর, গভীর অনুসন্ধান, সংকট উত্তরণ ও যৌথ বিষয়",
        "themes_hi": "आंतरिक रूपांतरण, गूढ़ अनुसंधान, संकट प्रबंधन एवं साझे संसाधन",
    },
    9: {
        "en": "9th house (dharma, higher learning, mentors and long journeys)",
        "bn": "৯ম ভাব (ভাগ্য ও ধর্ম ভাব — ধর্ম, উচ্চশিক্ষা, গুরুজন ও দূরভ্রমণ)",
        "hi": "नवम भाव (भाग्य एवं धर्म भाव — धर्म, उच्च विद्या, गुरु कृपा एवं लंबी यात्राएं)",
        "short_en": "9th house",
        "short_bn": "৯ম ভাব",
        "short_hi": "नवम भाव",
        "themes_en": "dharma, wisdom, ethical principles, guidance of mentors and fortune",
        "themes_bn": "উচ্চশিক্ষা, গুরুজনের সান্নিধ্য, ধর্মীয় নীতিবোধ ও ভাগ্যোন্নয়ন",
        "themes_hi": "धर्म, उच्च शिक्षा, गुरु कृपा, नैतिक मूल्य एवं भाग्योदय",
    },
    10: {
        "en": "10th house (career, authority, public status and contribution)",
        "bn": "১০ম ভাব (কর্ম ভাব — পেশা, সামাজিক সম্মান, কর্তৃত্ব ও দায়িত্ব)",
        "hi": "दशम भाव (कर्म भाव — आजीविका, प्रतिष्ठा, अधिकार एवं कर्मक्षेत्र)",
        "short_en": "10th house",
        "short_bn": "১০ম ভাব",
        "short_hi": "दशम भाव",
        "themes_en": "professional leadership, public contribution, vocation and social reputation",
        "themes_bn": "কর্মজীবন, সামাজিক মর্যাদা, নেতৃত্ব ও পেশাগত অবদান",
        "themes_hi": "आजीविका, सामाजिक मान-प्रतिष्ठा, नेतृत्व एवं कार्यक्षेत्र में योगदान",
    },
    11: {
        "en": "11th house (gains, professional networks, aspirations and income)",
        "bn": "১১শ ভাব (লাভ ভাব — আয়, প্রাপ্তি, সাফল্য ও সুহৃদ সংযোগ)",
        "hi": "एकादश भाव (लाभ भाव — आय, लाभ, मित्र मंडली एवं अभिलाषा पूर्ति)",
        "short_en": "11th house",
        "short_bn": "১১শ ভাব",
        "short_hi": "एकादश भाव",
        "themes_en": "financial gains, expansive networks, fulfillment of goals and community alliances",
        "themes_bn": "নিয়মিত আয়, সামাজিক পরিচিতি, লক্ষ্যপূরণ ও শুভাকাঙ্ক্ষীদের সমর্থন",
        "themes_hi": "वित्तीय लाभ, व्यापक संपर्क सूत्र, आकांक्षाओं की पूर्ति एवं आय वृद्धि",
    },
    12: {
        "en": "12th house (expenditure, retreat, foreign contexts and spiritual release)",
        "bn": "১২শ ভাব (ব্যয় ভাব — ব্যয়, নিভৃত সাধনা, আধ্যাত্মিকতা ও দূরযোগাযোগ)",
        "hi": "द्वादश भाव (व्यय भाव — व्यय, मोक्ष, वैराग्य एवं विदेश संबंध)",
        "short_en": "12th house",
        "short_bn": "১২শ ভাব",
        "short_hi": "द्वादश भाव",
        "themes_en": "spiritual introspection, foreign connections, private retreats and expenditures",
        "themes_bn": "নিভৃত সাধনা, বৈদেশিক সম্পর্ক, আধ্যাত্মিক একাগ্রতা ও অর্থব্যয়",
        "themes_hi": "आध्यात्मिक एकांत, विदेश संबंध, आत्म-चिंतन एवं व्यय प्रबंधन",
    },
}

PLANET_CORE_THEMES = {
    "Sun": {
        "en": "authority, personal vitality, father figure and conscious purpose",
        "bn": "কর্তৃত্ব, জীবনীশক্তি, আত্মমর্যাদা ও উদ্দেশ্যমুখী নেতৃত্ব",
        "hi": "नेतृत्व, आत्मबल, जीवन ऊर्जा एवं उद्देश्यपूर्ण निर्णय शक्ति",
    },
    "Moon": {
        "en": "emotional equilibrium, motherly nurturing, perception and intuitive clarity",
        "bn": "মন, মানসিক স্থিতি, সংবেদনশীলতা ও কল্পনাশক্তি",
        "hi": "मन, संवेदनशीलता, मानसिक शांति एवं सहजानुभूति",
    },
    "Mars": {
        "en": "courage, technical enterprise, decisive action and protective drive",
        "bn": "সাহস, তেজস্বী মনোভাব, প্রযুক্তিগত উদ্যোগ ও সুরক্ষা শক্তি",
        "hi": "साहस, तकनीकी क्षमता, पराक्रम एवं सुरक्षात्मक ऊर्जा",
    },
    "Mercury": {
        "en": "intellectual agility, commercial discernment, communication and rapid analysis",
        "bn": "মেধা, যোগাযোগ দক্ষতা, বাণিজ্যিক বিচারবুদ্ধি ও বিশ্লেষণ ক্ষমতা",
        "hi": "बुद्धि, व्यापारिक सूझबूझ, संवाद क्षमता एवं त्वरित विश्लेषण",
    },
    "Jupiter": {
        "en": "wisdom, expansion, spiritual mentorship, ethical principles and counsel",
        "bn": "জ্ঞান, আধ্যাত্মিক প্রজ্ঞা, উপদেশ প্রদান ও ধর্মভাব",
        "hi": "ज्ञान, मार्गदर्शन, नैतिक मूल्य, विस्तार एवं गुरु कृपा",
    },
    "Venus": {
        "en": "diplomatic grace, aesthetic harmony, relationship agreements and prosperity",
        "bn": "নান্দনিক দৃষ্টিভঙ্গি, দাম্পত্য প্রীতি, সামাজিক সৌহার্দ্য ও সুখস্বাচ্ছন্দ্য",
        "hi": "सौंदर्य बोध, सामंजस्य, वैवाहिक संबंध एवं सुख-समृद्धि",
    },
    "Saturn": {
        "en": "disciplined endurance, structural patience, karmic duty and perseverance",
        "bn": "শৃঙ্খলা, ধৈর্য্য, নিয়মনিষ্ঠা ও দীর্ঘমেয়াদী একাগ্রতা",
        "hi": "अनुशासन, धैर्य, कर्मनिष्ठा एवं सतत प्रयास",
    },
    "Rahu": {
        "en": "unconventional ambitions, global exploration and pioneering horizons",
        "bn": "প্রথাভাঙা উচ্চাকাঙ্ক্ষা, অভিনব দৃষ্টিভঙ্গি ও দূরদৃষ্টি",
        "hi": "नवीन महत्वाकांक्षाएं, आधुनिक सोच एवं अपरंपरागत दृष्टि",
    },
    "Ketu": {
        "en": "inward detachment, specialized mastery, spiritual insight and liberation",
        "bn": "নিরাসক্তি, গভীর অন্তর্দৃষ্টি, আধ্যাত্মিক একাগ্রতা ও নিগূঢ় বিদ্যা",
        "hi": "आत्म-चिंतन, गूढ़ ज्ञान, वैराग्य एवं आध्यात्मिक गहराई",
    },
}


def explain_rule(
    rule_id: str,
    factor_data: Optional[Dict[str, Any]] = None,
    chart_facts: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Translate an internal rule ID into complete human-readable explanations
    across English, Bengali, and Hindi with both Simple and Advanced Astrological perspectives.
    """
    rule_id_clean = str(rule_id).strip()
    data = factor_data or {}

    # 1. House Lord in House: HL-H{h1}-IN-H{h2}
    hl_match = re.match(r"^HL-H(\d+)-IN-H(\d+)$", rule_id_clean)
    if hl_match:
        h1 = int(hl_match.group(1))
        h2 = int(hl_match.group(2))
        h1_info = HOUSE_NAMES.get(h1, HOUSE_NAMES[1])
        h2_info = HOUSE_NAMES.get(h2, HOUSE_NAMES[1])

        tech_meaning = f"The {h1_info['short_en']} lord is placed in the {h2_info['short_en']}."

        simple_en = (
            f"The ruler of your {h1_info['short_en']} is positioned in your {h2_info['short_en']}. "
            f"In traditional Vedic astrology, this channels the significations of "
            f"{h1_info['themes_en']} directly into {h2_info['themes_en']}."
        )
        simple_bn = (
            f"আপনার {h1_info['short_bn']}-এর অধিপতি {h2_info['short_bn']}-এ অবস্থান করছে। "
            f"প্রচলিত বৈদিক জ্যোতিষ মতে, এই অবস্থান {h1_info['themes_bn']}-এর "
            f"সম্ভাবনাকে {h2_info['themes_bn']}-এর ক্ষেত্রে প্রত্যক্ষভাবে পরিচালিত করে।"
        )
        simple_hi = (
            f"आपके {h1_info['short_hi']} का स्वामी {h2_info['short_hi']} में स्थित है। "
            f"पारंपरिक वैदिक ज्योतिष के अनुसार, यह स्थिति {h1_info['themes_hi']} "
            f"की ऊर्जा को सीधे {h2_info['themes_hi']} में सक्रिय करती है।"
        )

        adv_en = (
            f"Rule {rule_id_clean}: Lord of H{h1} located in H{h2}. Parashari bhava-sambandha linking "
            f"{h1_info['short_en']} portfolio directly into {h2_info['short_en']} environment."
        )
        adv_bn = (
            f"সূত্র {rule_id_clean}: {h1_info['short_bn']}-এর অধিপতি {h2_info['short_bn']}-এ স্থিত। "
            f"পরাশরী ভাব-সম্বন্ধ অনুসারে এটি প্রথম ভাবের কার্যকারিতাকে দ্বিতীয় ভাবে সক্রিয় করে।"
        )
        adv_hi = (
            f"सूत्र {rule_id_clean}: {h1_info['short_hi']} के भावेश का {h2_info['short_hi']} में स्थित होना। "
            f"पराशरी भाव-संबंध सिद्धांत के आधार पर यह दोनों भावों की ऊर्जा को एकीकृत करता है।"
        )

        why_matters_en = (
            f"Because this house lord directly channels the core assets of {h1_info['short_en']} into "
            f"{h2_info['short_en']}, it shapes personal habits and life decisions in this sphere."
        )
        why_matters_bn = (
            f"যেহেতু এই ভাবাধিপতি {h1_info['short_bn']}-এর মূল সম্ভাবনাকে {h2_info['short_bn']}-এ প্রবাহিত করে, "
            f"তাই এটি সংশ্লিষ্ট ক্ষেত্রের সামগ্রিক গতিপ্রকৃতি নির্ধারণে বিশেষ ভূমিকা পালন করে।"
        )
        why_matters_hi = (
            f"चूंकि यह भावेश {h1_info['short_hi']} के प्रभाव को {h2_info['short_hi']} में संकेंद्रित करता है, "
            f"अतः यह इस क्षेत्र से संबंधित निर्णयों एवं संभावनाओं को प्रत्यक्ष रूप से प्रभावित करता है।"
        )

        example_en = f"This placement creates an active alignment for progress whenever personal initiative is applied during related dasha cycles."
        example_bn = f"সংশ্লিষ্ট দশা অন্তর্দশার প্রভাবে এই গ্রহাবস্থান উপযুক্ত প্রচেষ্টা ও একাগ্রতার সাথে কাঙ্ক্ষিত অগ্রগতি এনে দেয়।"
        example_hi = f"अनुकूल दशा-अंतर्दशा में यह स्थिति सतत प्रयासों के साथ इस क्षेत्र में उल्लेखनीय सफलता प्रदान करती है।"

        limits_en = "This influence is modulated by the dignity, conjunctions, and aspects of the house lord."
        limits_bn = "এই প্রভাব ভাবাধিপতির বলাবল, শুভাশুভ দৃষ্টি ও গ্রহসম্বন্ধের দ্বারা পরিমার্জিত হয়।"
        limits_hi = "यह परिणाम भावेश के बल, दृष्टि एवं युति के अनुसार रूपांतरित हो सकता है।"

        return {
            "rule_id": rule_id_clean,
            "category": "house_lord_in_house",
            "houses": [h1, h2],
            "planet": None,
            "technical_interpretation": tech_meaning,
            "simple_explanation": {"en": simple_en, "bn": simple_bn, "hi": simple_hi},
            "advanced_explanation": {"en": adv_en, "bn": adv_bn, "hi": adv_hi},
            "why_matters": {"en": why_matters_en, "bn": why_matters_bn, "hi": why_matters_hi},
            "example": {"en": example_en, "bn": example_bn, "hi": example_hi},
            "limitations": {"en": limits_en, "bn": limits_bn, "hi": limits_hi},
        }

    # 2. Planet in House: PH-{PLANET}-H{h}
    ph_match = re.match(r"^PH-([A-Z]+)-H(\d+)$", rule_id_clean)
    if ph_match:
        p_raw = ph_match.group(1).capitalize()
        h = int(ph_match.group(2))
        p_info = PLANET_NAMES.get(p_raw, {"en": p_raw, "bn": p_raw, "hi": p_raw})
        h_info = HOUSE_NAMES.get(h, HOUSE_NAMES[1])
        p_themes = PLANET_CORE_THEMES.get(p_raw, {"en": "vital energy", "bn": "গ্রহীয় প্রভাব", "hi": "ग्रहीय ऊर्जा"})

        tech_meaning = f"{p_info['en']} is placed in the {h_info['short_en']}."

        simple_en = (
            f"{p_info['en']} resides in your {h_info['short_en']}. "
            f"In classical Jyotish, this directs the symbolic energies of {p_info['en']} ({p_themes['en']}) "
            f"directly toward the affairs of the {h_info['short_en']} ({h_info['themes_en']})."
        )
        simple_bn = (
            f"{p_info['bn']} আপনার {h_info['short_bn']}-এ অবস্থান করছে। "
            f"বৈদিক জ্যোতিষ মতে, এর ফলে {p_info['bn']}-এর প্রতীকী গুণাবলী ({p_themes['bn']}) "
            f"সরাসরি আপনার {h_info['short_bn']}-এর বিষয়াবলীতে ({h_info['themes_bn']}) প্রযুক্ত হয়।"
        )
        simple_hi = (
            f"{p_info['hi']} आपके {h_info['short_hi']} में स्थित है। "
            f"वैदिक ज्योतिष के अनुसार, यह {p_info['hi']} की स्वाभाविक ऊर्जा ({p_themes['hi']}) "
            f"को {h_info['short_hi']} के कार्यक्षेत्र ({h_info['themes_hi']}) की ओर उन्मुख करता है।"
        )

        adv_en = f"Rule {rule_id_clean}: {p_info['en']} occupying house {h}. Karaka natural karakatva anchored in {h_info['short_en']}."
        adv_bn = f"সূত্র {rule_id_clean}: {p_info['bn']} {h_info['short_bn']}-এ স্থিত। পরাশরী কারকত্ব নীতি অনুযায়ী সংশ্লিষ্ট ভাবে ক্রিয়াশীল।"
        adv_hi = f"सूत्र {rule_id_clean}: {p_info['hi']} का {h_info['short_hi']} में अवस्थान। नैसर्गिक कारकत्व एवं भावाधिपत्य का समन्वय।"

        why_matters_en = f"The physical presence of {p_info['en']} in the {h_info['short_en']} highlights practical focus and sustained development here."
        why_matters_bn = f"{h_info['short_bn']}-এ {p_info['bn']}-এর স্থিতি এই ক্ষেত্রে কর্মদক্ষতা ও সচেতন মানসিকতা গঠনে সহায়ক।"
        why_matters_hi = f"{h_info['short_hi']} में {p_info['hi']} का वास इस क्षेत्र में सक्रियता एवं उद्देश्यपूर्ण विकास को प्रोत्साहित करता है।"

        example_en = f"During periods of {p_info['en']}, the themes of the {h_info['short_en']} come into sharp focus."
        example_bn = f"{p_info['bn']}-এর দশাকালে এই ভাবের বিষয়গুলি বিশেষ সক্রিয়তা লাভ করে।"
        example_hi = f"{p_info['hi']} की महादशा या अंतर्दशा के दौरान इस भाव से संबंधित विषयों में तीव्रता आती है।"

        limits_en = "Modulated by planetary sign dignity, combustion status, and incoming aspects."
        limits_bn = "রাশি বলাবল, অস্তমিত অবস্থা ও অন্যান্য গ্রহের শুভাশুভ দৃষ্টি সাপেক্ষে ফল বিচার্য।"
        limits_hi = "राशि बल, अस्त स्थिति एवं अन्य ग्रहों की दृष्टि के अनुसार फल नियंत्रित होता है।"

        return {
            "rule_id": rule_id_clean,
            "category": "planet_in_house",
            "houses": [h],
            "planet": p_raw,
            "technical_interpretation": tech_meaning,
            "simple_explanation": {"en": simple_en, "bn": simple_bn, "hi": simple_hi},
            "advanced_explanation": {"en": adv_en, "bn": adv_bn, "hi": adv_hi},
            "why_matters": {"en": why_matters_en, "bn": why_matters_bn, "hi": why_matters_hi},
            "example": {"en": example_en, "bn": example_bn, "hi": example_hi},
            "limitations": {"en": limits_en, "bn": limits_bn, "hi": limits_hi},
        }

    # 3. Dignity: DG-{PLANET}-{STATUS}
    dg_match = re.match(r"^DG-([A-Z]+)-([A-Z]+)$", rule_id_clean)
    if dg_match:
        p_raw = dg_match.group(1).capitalize()
        status = dg_match.group(2).lower()
        p_info = PLANET_NAMES.get(p_raw, {"en": p_raw, "bn": p_raw, "hi": p_raw})

        dignity_en = status.title()
        dignity_bn = "উচ্চস্থ" if status == "exalted" else "নীচস্থ" if status == "debilitated" else "স্বক্ষেত্রস্থ" if status == "own" else "মূলত্রিকোণস্থ"
        dignity_hi = "उच्च" if status == "exalted" else "नीच" if status == "debilitated" else "स्वगृही" if status == "own" else "मूलत्रिकोण"

        tech_meaning = f"{p_info['en']} is in its {dignity_en} sign dignity."

        simple_en = (
            f"{p_info['en']} is placed with {dignity_en} strength in your natal chart. "
            f"In classical astrology, strong planetary dignity allows the planet to express its gifts smoothly and reliably."
        )
        simple_bn = (
            f"আপনার জন্মকুণ্ডলীতে {p_info['bn']} {dignity_bn} মর্যাদায় অবস্থান করছে। "
            f"প্রথাগত জ্যোতিষ মতে, বলিষ্ঠ গ্রহাবস্থান নিজস্ব কার্যকারিতা প্রকাশে অনুকূল শক্তি জোগায়।"
        )
        simple_hi = (
            f"आपकी जन्मपत्रिका में {p_info['hi']} {dignity_hi} अवस्था में स्थित है। "
            f"वैदिक ज्योतिष के अनुसार, ग्रह का सुदृढ़ बल उसके शुभ प्रभावों को सरलता से अभिव्यक्त करता है।"
        )

        adv_en = f"Rule {rule_id_clean}: {p_info['en']} dignity evaluated as {status}. Parashari sthana bala calculation."
        adv_bn = f"সূত্র {rule_id_clean}: {p_info['bn']}-এর স্থানবল {dignity_bn} রূপে নিরূপিত।"
        adv_hi = f"सूत्र {rule_id_clean}: {p_info['hi']} का स्थानबल {dignity_hi} स्थिति के अंतर्गत मान्य।"

        why_matters_en = f"Planet dignity determines how consistently its symbolic qualities manifest across all ruled life areas."
        why_matters_bn = f"গ্রহের বলাবল তার আওতাধীন সমস্ত জীবনের ক্ষেত্রে ফলপ্রসূতার ধারাবাহিকতা নির্দেশ করে।"
        why_matters_hi = f"ग्रह का आत्मबल उसके आधिपत्य वाले सभी भावों के परिणामों की स्थिरता तय करता है।"

        example_en = f"A well-dignified planet grants natural resilience when navigating professional or personal crossroads."
        example_bn = f"সুদৃঢ় গ্রহাবস্থান জীবনের গুরুত্বপূর্ণ সন্ধিক্ষণে স্বাভাবিক মানসিক দৃঢ়তা প্রদান করে।"
        example_hi = f"सबल ग्रह जीवन के महत्वपूर्ण निर्णयों में स्वाभाविक आत्मविश्वास एवं स्थिरता प्रदान करता है।"

        limits_en = "Influenced by Navamsha (D9) dignity and aspectual modifications."
        limits_bn = "নবাংশ কুণ্ডলীর অবস্থান ও অন্যান্য গ্রহের দৃষ্টি অনুযায়ী বলের তারতম্য হতে পারে।"
        limits_hi = "नवांश कुंडली की स्थिति एवं अन्य ग्रहों की दृष्टि से बल में परिवर्तन संभव है।"

        return {
            "rule_id": rule_id_clean,
            "category": "dignity",
            "houses": [],
            "planet": p_raw,
            "technical_interpretation": tech_meaning,
            "simple_explanation": {"en": simple_en, "bn": simple_bn, "hi": simple_hi},
            "advanced_explanation": {"en": adv_en, "bn": adv_bn, "hi": adv_hi},
            "why_matters": {"en": why_matters_en, "bn": why_matters_bn, "hi": why_matters_hi},
            "example": {"en": example_en, "bn": example_bn, "hi": example_hi},
            "limitations": {"en": limits_en, "bn": limits_bn, "hi": limits_hi},
        }

    # 4. Yogas: YOGA-{NAME} or YOGA-CLUSTER-...
    if rule_id_clean.startswith("YOGA-"):
        parts = rule_id_clean.replace("YOGA-", "").split("-")
        yoga_type = parts[0].title()
        planets_involved = [p.title() for p in parts[1:] if p.title() in PLANETS]
        p_str_en = ", ".join(planets_involved) if planets_involved else "participating planets"
        p_str_bn = ", ".join([PLANET_NAMES.get(p, {}).get("bn", p) for p in planets_involved]) if planets_involved else "সংশ্লিষ্ট গ্রহসমূহ"
        p_str_hi = ", ".join([PLANET_NAMES.get(p, {}).get("hi", p) for p in planets_involved]) if planets_involved else "संबंधित ग्रह"

        if yoga_type == "Raja":
            simple_en = (
                f"The classical Raja Yoga is formed in your birth chart by {p_str_en} linking kendra and trikona houses. "
                f"In traditional Parashari texts, this combination supports authority, intellectual clarity, and enduring achievement."
            )
            simple_bn = (
                f"আপনার জন্মকুণ্ডলীতে কেন্দ্র ও ত্রিকোণাধিপতি {p_str_bn}-এর সংযোগে শাস্ত্রীয় রাজযোগ গঠিত হয়েছে। "
                f"পরাশরী নীতি মতে, এই শুভ যোগ কর্মদক্ষতা, নেতৃত্ব ও দীর্ঘস্থায়ী সাফল্যের সহায়ক।"
            )
            simple_hi = (
                f"आपकी जन्मपत्रिका में केंद्राधिपति एवं त्रिकोणाधिपति {p_str_hi} के संबंध से शास्त्रीय राजयोग का निर्माण हुआ है। "
                f"पारंपरिक वैदिक ग्रंथों में यह शुभ योग सम्मान, विवेकपूर्ण बुद्धि एवं दीर्घकालिक सफलता का सूचक है।"
            )
        else:
            simple_en = (
                f"The verified classical {yoga_type} Yoga ({p_str_en}) is active in your chart per Parashari canon, "
                f"supporting purposeful vitality and stability in its sphere."
            )
            simple_bn = (
                f"আপনার জন্মকুণ্ডলীতে শাস্ত্রীয় {yoga_type} যোগ ({p_str_bn}) গঠিত হয়েছে, যা সংশ্লিষ্ট ক্ষেত্রে ইতিবাচক স্থায়িত্ব দেয়।"
            )
            simple_hi = (
                f"आपकी जन्मपत्रिका में शास्त्रीय {yoga_type} योग ({p_str_hi}) निर्मित हुआ है, जो संबंधित क्षेत्र में स्थिरता प्रदान करता है।"
            )

        adv_en = f"Rule {rule_id_clean}: Classical yoga condition verified per Parashari canon."
        adv_bn = f"সূত্র {rule_id_clean}: পরাশরী শাস্ত্রীয় বিধি অনুযায়ী যোগটি সুনিশ্চিত।"
        adv_hi = f"सूत्र {rule_id_clean}: पराशरी शास्त्रीय सिद्धांतों के अनुसार योग की पुष्टि।"

        why_matters_en = "Classical yogas amplify overall chart strength and elevate favorable periods."
        why_matters_bn = "শাস্ত্রীয় শুভ যোগ সমগ্র জন্মকুণ্ডলীর শুভত্ব বৃদ্ধি করে এবং অনুকুল দশাকে ফলপ্রসূ করে।"
        why_matters_hi = "शास्त्रीय योग संपूर्ण कुंडली के सामर्थ्य को बढ़ाते हैं और अनुकूल दशाओं को विशेष फलदायी बनाते हैं।"

        example_en = "Activates notable milestones during participating planetary dasha cycles."
        example_bn = "যোগকারক গ্রহের দশাকালে জীবনে স্মরণীয় সাফল্য অর্জিত হতে পারে।"
        example_hi = "योगकारक ग्रहों की दशा में जीवन के महत्वपूर्ण लक्ष्यों की प्राप्ति होती है।"

        limits_en = "Requires strength in participating planets without combustion or malefic afflictions."
        limits_bn = "যোগকারী গ্রহগুলির অস্তহীনতা ও শুভদৃষ্টি যোগটির পূর্ণ কার্যকারিতা নিশ্চিত করে।"
        limits_hi = "संबंधित ग्रहों का अस्त न होना एवं शुभ दृष्टि में होना योग की पूर्ण फलप्राप्ति हेतु आवश्यक है।"

        return {
            "rule_id": rule_id_clean,
            "category": "yoga",
            "houses": [],
            "planet": None,
            "technical_interpretation": f"Formation of {yoga_type} Yoga.",
            "simple_explanation": {"en": simple_en, "bn": simple_bn, "hi": simple_hi},
            "advanced_explanation": {"en": adv_en, "bn": adv_bn, "hi": adv_hi},
            "why_matters": {"en": why_matters_en, "bn": why_matters_bn, "hi": why_matters_hi},
            "example": {"en": example_en, "bn": example_bn, "hi": example_hi},
            "limitations": {"en": limits_en, "bn": limits_bn, "hi": limits_hi},
        }

    # 5. General Fallback
    raw_desc = data.get("interpretation") or data.get("text") or rule_id_clean
    return {
        "rule_id": rule_id_clean,
        "category": "general",
        "houses": [],
        "planet": None,
        "technical_interpretation": raw_desc,
        "simple_explanation": {
            "en": f"Traditional astrological factor supporting balanced cultivation in this life sphere.",
            "bn": f"প্রথাগত জ্যোতিষ সূত্র যা সংশ্লিষ্ট জীবনের ক্ষেত্রে ভারসাম্যপূর্ণ উন্নয়নে সহায়ক।",
            "hi": f"पारंपरिक ज्योतिषीय सूत्र जो इस जीवन क्षेत्र में संतुलित विकास को बल प्रदान करता है।",
        },
        "advanced_explanation": {
            "en": f"Rule {rule_id_clean}: {raw_desc}",
            "bn": f"সূত্র {rule_id_clean}: {raw_desc}",
            "hi": f"सूत्र {rule_id_clean}: {raw_desc}",
        },
        "why_matters": {
            "en": "Serves as a symbolic benchmark for personal alignment and practical deliberation.",
            "bn": "ব্যক্তিগত কর্মপন্থা নির্ধারণ ও সিদ্ধান্ত গ্রহণের ক্ষেত্রে একটি নির্দেশক হিসেবে কাজ করে।",
            "hi": "व्यक्तिगत कार्यशैली एवं विचारशीलता के लिए एक मार्गदर्शक का कार्य करता है।",
        },
        "example": {
            "en": "Supports focused decision-making during favorable life phases.",
            "bn": "অনুকূল সময়ে সচেতন সিদ্ধান্ত গ্রহণে সহায়ক হয়।",
            "hi": "सकारात्मक समय में विवेकपूर्ण निर्णय लेने में सहायक होता है।",
        },
        "limitations": {
            "en": "Vedic Jyotish provides symbolic indicators rather than deterministic guarantees.",
            "bn": "বৈদিক জ্যোতিষ নিশ্চিত বিধিলিপি নয়, বরং সম্ভাবনা নির্দেশক।",
            "hi": "वैदिक ज्योतिष निश्चित भविष्यवाणी नहीं, अपितु संभावनाओं का संकेत है।",
        },
    }


def build_why_this_prediction(
    topic: str,
    agg: Dict[str, Any],
    used_items: List[Dict[str, Any]],
    chart_facts: Dict[str, Any],
) -> Dict[str, Any]:
    """Construct Section 20.B 6-point 'Why this prediction?' breakdown for a topic:
    1. What the planetary placement means.
    2. The specific house or planet involved.
    3. The life themes connected by the rule.
    4. Why this rule is relevant to this specific prediction.
    5. Any modifying factors (aspect, dignity, conjunction, cancellation).
    6. Supporting or contradicting factors from other rules.
    """
    explained_factors = []
    for item in used_items:
        rid = item.get("rule_id", "")
        if rid:
            explained_factors.append(explain_rule(rid, factor_data=item, chart_facts=chart_facts))

    primary_factor = explained_factors[0] if explained_factors else None

    # Point 1: Placement Meaning
    meaning_en = (
        primary_factor["simple_explanation"]["en"]
        if primary_factor
        else "Planetary placements in foundational houses create structural resonance for this life area."
    )
    meaning_bn = (
        primary_factor["simple_explanation"]["bn"]
        if primary_factor
        else "প্রধান ভাব ও সংশ্লিষ্ট গ্রহাবস্থান জীবনের এই ক্ষেত্রে সুদৃঢ় ভিত্তি রচনা করে।"
    )
    meaning_hi = (
        primary_factor["simple_explanation"]["hi"]
        if primary_factor
        else "प्रमुख भावों एवं संबंधित ग्रहों की स्थिति इस जीवन क्षेत्र के लिए एक मजबूत आधार तैयार करती है।"
    )

    # Point 2: Specific Houses/Planets Involved
    involved_houses = set()
    involved_planets = set()
    for ef in explained_factors:
        for h in ef.get("houses", []):
            involved_houses.add(h)
        if ef.get("planet"):
            involved_planets.add(ef["planet"])

    h_list_en = ", ".join([f"{HOUSE_NAMES.get(h, {}).get('short_en', f'{h}th house')}" for h in sorted(list(involved_houses))]) or "Primary houses"
    h_list_bn = ", ".join([f"{HOUSE_NAMES.get(h, {}).get('short_bn', f'{h} ভাব')}" for h in sorted(list(involved_houses))]) or "প্রধান ভাবসমূহ"
    h_list_hi = ", ".join([f"{HOUSE_NAMES.get(h, {}).get('short_hi', f'{h} भाव')}" for h in sorted(list(involved_houses))]) or "प्रमुख भाव"

    p_list_en = ", ".join([PLANET_NAMES.get(p, {}).get("en", p) for p in sorted(list(involved_planets))]) or "Relevant Grahas"
    p_list_bn = ", ".join([PLANET_NAMES.get(p, {}).get("bn", p) for p in sorted(list(involved_planets))]) or "সংশ্লিষ্ট গ্রহসমূহ"
    p_list_hi = ", ".join([PLANET_NAMES.get(p, {}).get("hi", p) for p in sorted(list(involved_planets))]) or "संबंधित ग्रह"

    involved_en = f"Primary houses involved: {h_list_en}; Active planets: {p_list_en}."
    involved_bn = f"সংশ্লিষ্ট ভাবসমূহ: {h_list_bn}; সক্রিয় গ্রহসমূহ: {p_list_bn}।"
    involved_hi = f"संबद्ध भाव: {h_list_hi}; सक्रिय ग्रह: {p_list_hi}।"

    # Point 3: Life Themes Connected
    themes_en = (
        f"Harmonizes foundational personal agency with long-term responsibilities, ethical conduct, and methodical growth."
    )
    themes_bn = (
        f"ব্যক্তিগত উদ্যম, নৈতিক কর্তব্য এবং নিয়মিত প্রচেষ্টার সমন্বয়ে দীর্ঘমেয়াদী স্থায়িত্ব প্রতিষ্ঠা করে।"
    )
    themes_hi = (
        f"व्यक्तिगत पुरुषार्थ, नैतिक आचरण एवं नियमित अभ्यास के संतुलन से दीर्घकालिक सफलता सुनिश्चित करता है।"
    )

    # Point 4: Relevance to this Specific Prediction
    rel_en = (
        f"Parashari rules establish that angular and trinal house connections direct innate strengths directly into concrete life outcomes."
    )
    rel_bn = (
        f"পরাশরী শাস্ত্রীয় নীতি অনুসারে কেন্দ্র ও কোণ ভাবের সংযোগ সহজাত প্রতিভাকে বাস্তব সাফল্যে রূপান্তর করতে সাহায্য করে।"
    )
    rel_hi = (
        f"पराशरी ज्योतिषीय सिद्धांतों के अनुसार केंद्र एवं त्रिकोण भावों का संबंध स्वाभाविक क्षमताओं को प्रत्यक्ष परिणामों में बदलता है।"
    )

    # Point 5: Modifying Factors
    mod_en = (
        "Aspectual influences, sign lord dignity, and retrograde motions modulate the timing and texture of outcomes."
    )
    mod_bn = (
        "দৃষ্টি বিনিময়, রাশিপতির বলাবল এবং বক্রী বা অস্তমিত অবস্থা ফলাফলের সময়কাল ও তীব্রতা পরিমার্জন করে।"
    )
    mod_hi = (
        "ग्रह दृष्टि, राशि स्वामी का बल एवं वक्री या अस्त स्थिति परिणामों की गति एवं तीव्रता को नियंत्रित करते हैं।"
    )

    # Point 6: Synthesis of Supporting vs Contradicting
    sup_cnt = agg.get("counts", {}).get("supportive", 0)
    ctr_cnt = agg.get("counts", {}).get("challenging", 0)
    syn_en = (
        f"Evidence synthesis reveals {sup_cnt} supportive factors and {ctr_cnt} modifying factors, yielding a {agg.get('level', 'Moderate')} ({agg.get('lean', 'mixed')}) indication."
    )
    syn_bn = (
        f"শাস্ত্রীয় প্রমাণ বিশ্লেষণে {sup_cnt}টি অনুকূল যোগ এবং {ctr_cnt}টি পরিমার্জনকারী ইঙ্গিত পাওয়া গেছে, যা সামগ্রিকভাবে {agg.get('level', 'Moderate')} ফলাফল নির্দেশ করে।"
    )
    syn_hi = (
        f"प्रमाणों के विश्लेषण से {sup_cnt} सकारात्मक एवं {ctr_cnt} परिमार्जक घटक प्राप्त हुए हैं, जो {agg.get('level', 'Moderate')} संतुलित परिणाम का संकेत देते हैं।"
    )

    return {
        "placement_meaning": {"en": meaning_en, "bn": meaning_bn, "hi": meaning_hi},
        "involved_factors": {"en": involved_en, "bn": involved_bn, "hi": involved_hi},
        "life_themes": {"en": themes_en, "bn": themes_bn, "hi": themes_hi},
        "relevance": {"en": rel_en, "bn": rel_bn, "hi": rel_hi},
        "modifying_factors": {"en": mod_en, "bn": mod_bn, "hi": mod_hi},
        "synthesis": {"en": syn_en, "bn": syn_bn, "hi": syn_hi},
        "explained_factors": explained_factors,
    }
