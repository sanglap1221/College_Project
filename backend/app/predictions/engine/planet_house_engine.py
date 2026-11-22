"""Planet-in-House Result Interpretation Engine.
Adheres strictly to traditional Parashari Vedic Jyotish principles.

Generates 3-Level structured interpretations for all 9 classical planets across all 12 houses:
- Level A: Traditional Placement Indications (Positive, Challenges, Life Area Impacts)
- Level B: Personalized Natal Synthesis (Combining actual Ascendant-derived Lordships, Sign Dignity, Conjunctions, Aspects)
- Level C: Time-Based Vimshottari Dasha Timing Activation
- Advanced Parashari Technical Matrix & Rule IDs
Supported in English, Bengali (বাংলা), and Hindi (हिन्दी).
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from .reference import (
    PLANETS, GRAHAS7, SIGNS, SIGN_LORD, EXALT, DEBIL, OWN, MOOLATRIKONA,
    ASPECT_OFFSETS, HOUSE_DOMAIN, PLANET_KEYWORDS, ordinal
)
from .explain import PLANET_NAMES, HOUSE_NAMES, PLANET_CORE_THEMES

# Classical Planet Significations & Domains
PLANET_SIGNIFICATORS = {
    "Sun": {
        "en": "vitality, soul purpose, leadership, paternal lineage, and public prestige",
        "bn": "আত্মশক্তি, পিতৃবংশ, নেতৃত্ব, সামাজিক সম্মান ও জীবনীশক্তি",
        "hi": "आत्मबल, नेतृत्व, पितृ पक्ष, सामाजिक प्रतिष्ठा एवं जीवन ऊर्जा",
    },
    "Moon": {
        "en": "mental tranquility, perception, mother, emotional equilibrium, and public interaction",
        "bn": "মন, মানসিক শান্তি, মাতৃস্নেহ, সংবেদনশীলতা ও জনসম্পর্ক",
        "hi": "मन, मानसिक शांति, मातृ सुख, संवेदनशीलता एवं जनसंपर्क",
    },
    "Mars": {
        "en": "drive, technical enterprise, courage, land, siblings, and executive action",
        "bn": "পরাক্রম, প্রযুক্তিগত সাহস, ভ্রাতৃসম্পর্ক, ভূমি ও দৃঢ় পদক্ষেপ",
        "hi": "साहस, तकनीकी क्षमता, पराक्रम, भूमि, भाई-बहन एवं निर्णायक कार्रवाई",
    },
    "Mercury": {
        "en": "analytical intellect, commerce, communication, speech, learning, and adaptability",
        "bn": "বিশ্লেষণী মেধা, বাণিজ্য, যোগাযোগ, বাকপটুতা ও বহুমুখী শিক্ষা",
        "hi": "विश्लेषणात्मक बुद्धि, व्यापार, संवाद, वाणी एवं अनुकूलनशीलता",
    },
    "Jupiter": {
        "en": "spiritual wisdom, expansion, counsel, dharma, wealth, and children",
        "bn": "আধ্যাত্মিক জ্ঞান, ধর্মভাব, উপদেশ, আর্থিক প্রাচুর্য ও সন্তানসুখ",
        "hi": "आध्यात्मिक ज्ञान, धर्म, मार्गदर्शन, धन-धान्य एवं संतान सुख",
    },
    "Venus": {
        "en": "relationship harmony, arts, vehicle comfort, aesthetics, diplomacy, and prosperity",
        "bn": "দাম্পত্য সৌহার্দ্য, কলা ও নান্দনিকতা, বাহনসুখ, সামাজিক সৌহার্দ্য ও ঐশ্বর্য",
        "hi": "वैवाहिक सामंजस्य, कला, वाहन सुख, सौंदर्य बोध, कूटनीति एवं समृद्धि",
    },
    "Saturn": {
        "en": "endurance, structured discipline, longevity, perseverance, and professional duty",
        "bn": "নিয়মনিষ্ঠা, ধৈর্য্য, দীর্ঘায়ু, কর্মশৃঙ্খল ও সেবামুখী দায়িত্ব",
        "hi": "धैर्य, अनुशासन, दीर्घायु, सतत परिश्रम एवं कर्मठता",
    },
    "Rahu": {
        "en": "unconventional ambitions, experimentation, modern frontiers, and foreign horizons",
        "bn": "প্রথাভাঙা উচ্চাকাঙ্ক্ষা, আধুনিক উদ্ভাবন ও দূরদেশীয় যোগাযোগ",
        "hi": "अपरंपरागत महत्वाकांक्षा, नवाचार, आधुनिक तकनीक एवं विदेश संबंध",
    },
    "Ketu": {
        "en": "spiritual detachment, specialized analytical depth, inward mastery, and liberation",
        "bn": "আধ্যাত্মিক একাগ্রতা, নিরাসক্তি, নিগূঢ় জ্ঞান ও আত্মদর্শন",
        "hi": "आध्यात्मिक गहराई, वैराग्य, गूढ़ ज्ञान एवं आत्म-चिंतन",
    },
}

# 9 Planets x 12 Houses Base Interpretations Matrix
# Each house index is 1..12
PLANET_HOUSE_DATA: Dict[str, Dict[int, Dict[str, Any]]] = {
    "Sun": {
        1: {
            "title": {"en": "Sun in the 1st House", "bn": "১ম ভাবে রবি (সূর্য)", "hi": "प्रथम भाव में सूर्य"},
            "simple": {
                "en": "The Sun in the 1st house confers strong presence, commanding vitality, dignified self-reliance, and natural leadership instincts.",
                "bn": "১ম ভাবে রবির অবস্থান বলিষ্ঠ ব্যক্তিত্ব, আত্মমর্যাদাবোধ, নেতৃত্ব দেওয়ার স্বাভাবিক প্রবৃত্তি ও উজ্জ্বল জীবনীশক্তি প্রদান করে।",
                "hi": "प्रथम भाव में सूर्य स्थित होने से जातक में प्रभावशाली व्यक्तित्व, आत्मसम्मान, प्राकृतिक नेतृत्व क्षमता एवं उत्तम जीवन ऊर्जा रहती है।",
            },
            "positive": {
                "en": ["Dignified personal demeanor and self-confidence", "Natural executive and organizational instincts", "Strong immune resistance and purposeful drive"],
                "bn": ["দৃঢ় আত্মবিশ্বাস ও ব্যক্তিত্বের মর্যাদা", "নেতৃত্ব ও সাংগঠনিক কাজের স্বাভাবিক দক্ষতা", "শারীরিক তেজ ও উদ্দেশ্যমুখী উদ্যম"],
                "hi": ["दृढ़ आत्मविश्वास एवं गरिमामय व्यक्तित्व", "प्राकृतिक नेतृत्व एवं संगठनात्मक क्षमता", "सकारात्मक दृष्टिकोण एवं उद्देश्यपूर्ण ऊर्जा"],
            },
            "challenges": {
                "en": ["Tendency toward impatience or ego friction with peers", "Overheating constitution or stress-induced fatigue"],
                "bn": ["অধৈর্য্য ভাব বা অহংবোধের কারণে মতভেদ", "অতিরিক্ত কাজের চাপে ক্লান্তি ও উত্তেজনা"],
                "hi": ["अहंकार अथवा अधीरता के कारण वैचारिक मतभेद", "कार्यभार के कारण मानसिक तनाव"],
            },
            "life_areas": {
                "career": {"en": "Favors administrative, authoritative, government, and managerial roles.", "bn": "প্রশাসনিক, সরকারি এবং নেতৃত্বমূলক পেশায় অনুকূল ফল দেয়।", "hi": "प्रशासनिक, सरकारी एवं प्रबंधकीय कार्यों में विशेष सफलता मिलती है।"},
                "finance": {"en": "Income through independent enterprise and authoritative standing.", "bn": "স্বাধীন উদ্যোগ ও প্রতিষ্ঠিত অবস্থানের মাধ্যমে সম্মানজনক উপার্জন।", "hi": "स्वतंत्र प्रयासों एवं उच्च पद के माध्यम से आर्थिक स्थिरता।"},
                "relationship": {"en": "Demands mutual respect; needs balance to prevent dominating partners.", "bn": "পারস্পরিক শ্রদ্ধাবোধ অপরিহার্য; অংশীদারের সাথে নম্র আচরণ বজায় রাখা প্রয়োজন।", "hi": "परस्पर सम्मान आवश्यक है; संबंधों में अत्यधिक प्रभुत्व से बचना चाहिए।"},
            },
        },
        2: {
            "title": {"en": "Sun in the 2nd House", "bn": "২য় ভাবে রবি (সূর্য)", "hi": "द्वितीय भाव में सूर्य"},
            "simple": {
                "en": "The Sun in the 2nd house directs authoritative energy toward accumulated assets, family reputation, and articulate, principled speech.",
                "bn": "২য় ভাবে রবির অবস্থান পারিবারিক ঐতিহ্য, স্পষ্ট ও বলিষ্ঠ বাকশক্তি এবং আর্থিক দায়িত্বশীলতার পরিচায়ক।",
                "hi": "द्वितीय भाव में सूर्य स्थित होने से पारिवारिक प्रतिष्ठा, स्पष्ट वाणी एवं वित्तीय उत्तरदायित्व में वृद्धि होती है।",
            },
            "positive": {
                "en": ["Commanding, persuasive vocal presence", "Stewardship over family assets and heritage", "Principled financial self-discipline"],
                "bn": ["স্পষ্ট ও প্রভাবশালী কণ্ঠস্বর", "পারিবারিক মর্যাদা ও সম্পদ রক্ষায় আন্তরিকতা", "আর্থিক নীতিনিষ্ঠা ও সুষম দৃষ্টিভঙ্গি"],
                "hi": ["प्रभावशाली एवं ओजस्वी वाणी", "पारिवारिक संपत्ति एवं मान-सम्मान की रक्षा", "आर्थिक अनुशासन एवं सिद्धांतवादी सोच"],
            },
            "challenges": {
                "en": ["Bluntness in speech leading to momentary family friction", "Financial expenditures on status symbols"],
                "bn": ["স্পষ্টভাষিতার কারণে স্বজনদের সাথে ভুল বোঝাবুঝি", "মর্যাদারক্ষার তাগিদে মাত্রাতিরিক্ত ব্যয়"],
                "hi": ["अत्यधिक स्पष्टवादिता से परिजनों से वैचारिक मतभेद", "प्रतिष्ठा हेतु अनावश्यक व्यय की प्रवृत्ति"],
            },
            "life_areas": {
                "career": {"en": "Thrives in finance, corporate governance, and speech-driven vocations.", "bn": "অর্থনীতি, প্রাতিষ্ঠানিক পরিচালনা ও প্রবচন সংক্রান্ত পেশায় সাফল্য।", "hi": "वित्तीय प्रबंधन, शासन एवं वक्तृत्व आधारित कार्यक्षेत्र में प्रगति।"},
                "finance": {"en": "Progressive accumulation when speculation is disciplined.", "bn": "নিয়মতান্ত্রিক বিনিয়োগের মাধ্যমে সঞ্চয় সুদৃঢ় হয়।", "hi": "नियमित एवं विवेकपूर्ण निवेश से संचित धन में वृद्धि।"},
                "relationship": {"en": "Family dynamics require diplomatic communication.", "bn": "পারিবারিক সম্পর্কের ক্ষেত্রে কোমল শব্দচয়ন আবশ্যক।", "hi": "पारिवारिक सामंजस्य हेतु विनम्र संवाद आवश्यक है।"},
            },
        },
        3: {
            "title": {"en": "Sun in the 3rd House", "bn": "৩য় ভাবে রবি (সূর্য)", "hi": "तृतीय भाव में सूर्य"},
            "simple": {
                "en": "The Sun in the 3rd house is traditionally considered very supportive, fostering courageous initiative, determination, and enterprise.",
                "bn": "৩য় ভাবে রবির স্থিতি অসীম সাহস, দৃঢ় মানসিকতা, স্বাধীন উদ্যোগ এবং প্রত্যয়ী যোগাযোগ নির্দেশ করে।",
                "hi": "तृतीय भाव में सूर्य अत्यंत शुभ माना जाता है, जो अदम्य पराक्रम, साहस, दृढ़ संकल्प एवं सफल पहल प्रदान करता है।",
            },
            "positive": {
                "en": ["Resolute courage and refusal to submit to obstacles", "Pioneering drive in commerce and media", "Active and respected fraternal standing"],
                "bn": ["অদম্য সাহস ও বাধা অতিক্রম করার অনমনীয় শক্তি", "উদ্যোগ ও যোগাযোগে পথপ্রদর্শকের ভূমিকা", "ভ্রাতা ও সমাজে সুপ্রতিষ্ঠিত অবস্থান"],
                "hi": ["अडिग साहस एवं कठिनाइयों से न घबराने की क्षमता", "व्यवसाय एवं संवाद में अग्रणी भूमिका", "समाज में सम्मानित एवं पराक्रमी पहचान"],
            },
            "challenges": {
                "en": ["Impulsive risk-taking or friction with younger associates", "Overexertion through continuous physical restlessness"],
                "bn": ["কখনও কখনও অতিরিক্ত ঝুঁকি নেওয়ার প্রবণতা", "অবিরাম কর্মব্যস্ততার কারণে শারীরিক ক্লান্তি"],
                "hi": ["अति-उत्साह में जोखिम लेने की प्रवृत्ति", "निरंतर भागदौड़ से शारीरिक थकावट"],
            },
            "life_areas": {
                "career": {"en": "Excellent for journalism, communications, marketing, and military or technical enterprise.", "bn": "সাংবাদিকতা, প্রযুক্তি, সামরিক ও স্বাধীন ব্যবসায় বিশেষ শুভ।", "hi": "मीडिया, संचार, तकनीकी क्षेत्र एवं स्वतंत्र उद्यम हेतु उत्तम।"},
                "finance": {"en": "Gains through calculated personal effort and commercial skills.", "bn": "নিজস্ব প্রচেষ্টা ও দক্ষতার মাধ্যমে অর্জিত সম্পদ।", "hi": "स्वयं के बाहुबल एवं कौशल द्वारा अर्जित धन।"},
                "relationship": {"en": "May assume a dominant parental role toward siblings.", "bn": "ভাইবোনদের অভিভাবকের মতো দায়িত্ব পালনের প্রবণতা।", "hi": "भाई-बहनों के प्रति अभिभावकत्व की भावना।"},
            },
        },
        4: {
            "title": {"en": "Sun in the 4th House", "bn": "৪র্থ ভাবে রবি (সূর্য)", "hi": "चतुर्थ भाव में सूर्य"},
            "simple": {
                "en": "The Sun in the 4th house anchors personal authority into the domestic hearth, land, family roots, and core security.",
                "bn": "৪র্থ ভাবে রবি গৃহের কেন্দ্রবিন্দুতে কর্তৃত্ব, পারিবারিক ঐতিহ্য ও বাস্তু বিষয়ে সচেতনতা এনে দেয়।",
                "hi": "चतुर्थ भाव में सूर्य जातक के प्रभाव को गृह, भूमि, पारिवारिक परंपरा एवं आंतरिक सुरक्षा से जोड़ता है।",
            },
            "positive": {
                "en": ["Deep loyalty to family roots and ancestral heritage", "Capacity to acquire solid immovable property", "Strong domestic protective instincts"],
                "bn": ["পারিবারিক ঐতিহ্যের প্রতি গভীর নিষ্ঠা", "স্থাবর সম্পত্তি ও গৃহসুখ অর্জনের সামর্থ্য", "পরিবারের সুরক্ষায় নিবেদিতপ্রাণ ভূমিকা"],
                "hi": ["पारिवारिक परंपरा के प्रति समर्पण", "अचल संपत्ति एवं भूमि-भवन प्राप्ति के अवसर", "गृह एवं परिवार की सुरक्षा हेतु सजगता"],
            },
            "challenges": {
                "en": ["Inner restlessness or emotional distance from domestic calm", "Occasional friction over domestic management"],
                "bn": ["মানসিক স্থিরতার অভাব বা গৃহে অতিরিক্ত কর্তৃত্বের সংঘাত", "পারিবারিক বিষয়ে মতপার্থক্য"],
                "hi": ["आंतरिक शांति में कमी अथवा गृह में मतभेद", "पारिवारिक निर्णयों में अत्यधिक कठोरता"],
            },
            "life_areas": {
                "career": {"en": "Favors real estate, architecture, governance, and institutional management.", "bn": "রিয়েল এস্টেট, বাস্তু, প্রশাসন ও শিক্ষা প্রতিষ্ঠানে সাফল্য।", "hi": "भूमि-भवन, संस्थागत प्रबंधन एवं प्रशासनिक क्षेत्र में प्रगति।"},
                "finance": {"en": "Assets linked to property, vehicles, and ancestral foundations.", "bn": "সম্পত্তি ও পৈতৃক সম্পদের মাধ্যমে আর্থিক নিরাপত্তা।", "hi": "भूमि, वाहन एवं पैतृक संपत्ति से वित्तीय सुदृढ़ता।"},
                "relationship": {"en": "Cultivating emotional softness enriches domestic peace.", "bn": "মানসিক কোমলতা পারিবারিক সুখ বহুলাংশে বৃদ্ধি করে।", "hi": "संवेदनशील दृष्टिकोण से गृहस्थ जीवन अधिक सुखद बनता है।"},
            },
        },
        5: {
            "title": {"en": "Sun in the 5th House", "bn": "৫ম ভাবে রবি (সূর্য)", "hi": "पंचम भाव में सूर्य"},
            "simple": {
                "en": "The Sun in the 5th house ignites creative brilliance, intellectual pride, strategic discernment, and leadership in education.",
                "bn": "৫ম ভাবে রবির অবস্থান তীক্ষ্ণ মেধা, উদ্ভাবনী সৃজনশীলতা, আত্মপ্রত্যয় এবং উচ্চশিক্ষায় নেতৃত্ব প্রদানের ক্ষমতা দেয়।",
                "hi": "पंचम भाव में सूर्य कुशाग्र बुद्धि, रचनात्मक प्रतिभा, आत्मगौरव एवं उच्च विद्या में नेतृत्व क्षमता प्रदान करता है।",
            },
            "positive": {
                "en": ["Sharp intellect and strategic problem-solving talent", "Commanding creative expression and artistic vision", "High ethical and philosophical discernment"],
                "bn": ["কৌশলী বিচারবুদ্ধি ও প্রখর বিশ্লেষণ ক্ষমতা", "সৃজনশীল কাজে মৌলিক চিন্তা ও শিল্পবোধ", "উচ্চ নৈতিক মূল্যবোধ ও জ্ঞানের প্রতি অনুরাগ"],
                "hi": ["तीक्ष्ण बौद्धिक क्षमता एवं रणनीतिक सूझबूझ", "रचनात्मक कार्यों में मौलिकता एवं कलात्मक दृष्टि", "उच्च नैतिक मूल्य एवं ज्ञानार्जन की ललक"],
            },
            "challenges": {
                "en": ["Intellectual stubbornness or sensitivity to criticism", "Occasional worries regarding children's temperament"],
                "bn": ["নিজের মতের প্রতি মাত্রাতিরিক্ত অনমনীয়তা", "সন্তানের সাথে সাময়িক মতাদর্শগত দূরত্ব"],
                "hi": ["वैचारिक हठधर्मिता अथवा आलोचना के प्रति संवेदनशीलता", "संतान के स्वभाव को लेकर कुछ चिंताएं"],
            },
            "life_areas": {
                "career": {"en": "Excellent for politics, research, advisory, creative arts, and higher education.", "bn": "রাজনীতি, গবেষণা, পরামর্শদান, কলা ও উচ্চশিক্ষায় বিশেষ সাফল্য।", "hi": "राजनीति, शोध, परामर्श, कला एवं उच्च शिक्षण में उत्कृष्ट।"},
                "finance": {"en": "Gains through intellect, calculated investments, and counsel.", "bn": "মেধাভিত্তিক কাজ ও দূরদর্শী বিনিয়োগের মাধ্যমে আর্থিক লাভ।", "hi": "बौद्धिक कौशल एवं सुविचारित निवेश से धन लाभ।"},
                "relationship": {"en": "Romance is passionate though requires personal humility.", "bn": "সম্পর্কে আবেগপ্রবণ হলেও বিনম্রতা বজায় রাখা জরুরি।", "hi": "प्रेम संबंधों में निष्ठा के साथ विनम्रता आवश्यक है।"},
            },
        },
        6: {
            "title": {"en": "Sun in the 6th House", "bn": "৬ষ্ঠ ভাবে রবি (সূর্য)", "hi": "षष्ठ भाव में सूर्य"},
            "simple": {
                "en": "The Sun in the 6th house is an outstanding placement for victory over competitors, health resilience, and solving complex problems.",
                "bn": "৬ষ্ঠ ভাবে রবি শত্রুনাশক, প্রতিকূলতা জয় করার শক্তি, বলিষ্ঠ কর্মদক্ষতা এবং স্বাস্থ্য পুনরুদ্ধারের অন্যতম প্রধান সহায়ক।",
                "hi": "षष्ठ भाव में सूर्य शत्रुओं पर विजय, रोग प्रतिरोधक क्षमता, कार्यकुशलता एवं कठिन चुनौतियों को हल करने हेतु श्रेष्ठ है।",
            },
            "positive": {
                "en": ["Triumph over adversaries and competitive superiority", "Vigorous work ethic and meticulous problem resolution", "Strong physical constitution overcoming acute imbalances"],
                "bn": ["প্রতিযোগিতায় বিজয় ও শত্রুর পরাভব", "কঠোর পরিশ্রমী মানসিকতা ও সমস্যা সমাধানের দক্ষতা", "শারীরিক রোগ প্রতিরোধে স্বাভাবিক তেজ"],
                "hi": ["प्रतिस्पर्धा में उत्कृष्ट सफलता एवं विरोधियों का शमन", "अथक परिश्रम एवं जटिल समस्याओं का समाधान", "रोगों से लड़ने की स्वाभाविक शारीरिक क्षमता"],
            },
            "challenges": {
                "en": ["Excessive friction with subordinates if empathy is neglected", "Risk of acidity or stress-related exhaustion"],
                "bn": ["সহকর্মীদের সাথে সংবেদনশীলতার অভাবে দূরত্ব সৃষ্টি", "অতিরিক্ত খাটুনির ফলে শারীরিক ক্লান্তি বা অম্লতা"],
                "hi": ["सहकर्मियों के साथ समन्वय में कठोरता", "अत्यधिक कार्यभार से स्वास्थ्य में असंतुलन"],
            },
            "life_areas": {
                "career": {"en": "Favors civil service, law, medicine, litigation, defense, and consulting.", "bn": "সরকারি চাকরি, আইন, চিকিৎসা, সামরিক ও পরামর্শমূলক পেশায় অগ্রণী।", "hi": "प्रशासनिक सेवा, विधि, चिकित्सा, रक्षा एवं परामर्श क्षेत्र में उत्तम।"},
                "finance": {"en": "Progress through disciplined debt management and professional service.", "bn": "নিয়মিত সেবা ও বিচক্ষণ আর্থিক শৃঙ্খলার মাধ্যমে সমৃদ্ধি।", "hi": "ऋण मुक्ति एवं नियमित सेवा कार्यों से निरंतर आर्थिक लाभ।"},
                "relationship": {"en": "Keep workplace critical analysis outside domestic affairs.", "bn": "কর্মক্ষেত্রের কঠোর মনোভাব গৃহে প্রয়োগ না করাই শ্রেয়।", "hi": "कार्यक्षेत्र के तनाव को पारिवारिक जीवन से दूर रखें।"},
            },
        },
        7: {
            "title": {"en": "Sun in the 7th House", "bn": "৭ম ভাবে রবি (সূর্য)", "hi": "सप्तम भाव में सूर्य"},
            "simple": {
                "en": "The Sun in the 7th house projects authority into public partnerships, social agreements, and committed relationships.",
                "bn": "৭ম ভাবে রবির অবস্থান জনসমক্ষে ব্যক্তিত্বের প্রতিষ্ঠা, প্রভাবশালী অংশীদারি ও সামাজিক চুক্তিতে গুরুত্ব আনে।",
                "hi": "सप्तम भाव में सूर्य सार्वजनिक साझेदारी, सामाजिक अनुबंध एवं वैवाहिक संबंधों में प्रभावशीलता लाता है।",
            },
            "positive": {
                "en": ["Alliances with influential, respectable individuals", "Public standing characterized by dignity and integrity", "Skill in negotiating high-profile agreements"],
                "bn": ["প্রভাবশালী ও মর্যাদাশীল ব্যক্তিদের সাথে অংশীদারি", "জনসাধারণের মধ্যে সম্মানিত ও নীতিবান ভাবমূর্তি", "গুরুত্বপূর্ণ সামাজিক চুক্তি সম্পাদনের দক্ষতা"],
                "hi": ["प्रतिष्ठित एवं प्रभावशाली व्यक्तियों से साझेदारी", "समाज में सम्मानित एवं नीतिनिष्ठ पहचान", "महत्वपूर्ण समझौतों के क्रियान्वयन में दक्षता"],
            },
            "challenges": {
                "en": ["Ego dynamics within marriage requiring mutual compromise", "Tendency to overshadow partners"],
                "bn": ["দাম্পত্যে ব্যক্তিত্বের সংঘাত এড়িয়ে সমঝোতা প্রয়োজন", "সঙ্গীর মতামতের প্রতি সমগুরুত্ব দেওয়া জরুরি"],
                "hi": ["दांपत्य जीवन में अहं का टकराव रोकने हेतु सामंजस्य आवश्यक", "साझेदार के विचारों को समुचित सम्मान देना चाहिए"],
            },
            "life_areas": {
                "career": {"en": "Thrives in public relations, diplomacy, law, and joint ventures.", "bn": "জনসংযোগ, কূটনীতি, আইন ও ব্যবসায়িক অংশীদারিতে সাফল্য।", "hi": "जनसंपर्क, कूटनीति, विधि एवं संयुक्त उपक्रमों में प्रगति।"},
                "finance": {"en": "Prosperity through transparent legal contracts.", "bn": "স্বচ্ছ সামাজিক ও বাণিজ্যিক চুক্তির মাধ্যমে উপার্জন।", "hi": "पारदर्शी कानूनी अनुबंधों के माध्यम से आर्थिक लाभ।"},
                "relationship": {"en": "Patience and shared leadership sustain marital harmony.", "bn": "ধৈর্য্য ও পারস্পরিক মর্যাদা দাম্পত্যের ভিত্তি সুদৃঢ় করে।", "hi": "धैर्य एवं साझा समझ से वैवाहिक जीवन सुखी रहता है।"},
            },
        },
        8: {
            "title": {"en": "Sun in the 8th House", "bn": "৮ম ভাবে রবি (সূর্য)", "hi": "अष्टम भाव में सूर्य"},
            "simple": {
                "en": "The Sun in the 8th house directs conscious vitality into deep research, psychological resilience, crisis mastery, and transformative knowledge.",
                "bn": "৮ম ভাবে রবির স্থিতি গভীর গবেষণা, সংকটে নির্ভীক মানসিকতা, রূপান্তর ও নিগূঢ় বিষয়ের প্রতি বিশেষ আকর্ষণ নির্দেশ করে।",
                "hi": "अष्टम भाव में सूर्य गहन अनुसंधान, संकट प्रबंधन, आंतरिक रूपांतरण एवं गूढ़ विद्याओं में सफलता प्रदान करता है।",
            },
            "positive": {
                "en": ["Exceptional investigative instinct and intellectual stamina", "Ability to rebuild with greater dignity after life crises", "Fascination with esoteric sciences and heritage assets"],
                "bn": ["নিগূঢ় বিষয় উদ্ঘাটনের গভীর ক্ষমতা", "জীবনের যেকোনো সংকট থেকে ঘুরে দাঁড়ানোর অদ্ভুত মানসিক তেজ", "গুপ্তবিদ্যা ও প্রাচীন জ্ঞানের প্রতি গভীর শ্রদ্ধা"],
                "hi": ["गहन खोज एवं अनुसंधान की अद्भुत क्षमता", "संकट की घड़ी में अदम्य साहस एवं पुनरुत्थान", "गूढ़ रहस्यों एवं प्राचीन विद्याओं में रुचि"],
            },
            "challenges": {
                "en": ["Sudden fluctuations in public vitality or parental health", "Need for emotional transparency during transitions"],
                "bn": ["কর্মক্ষেত্রে আকস্মিক পরিবর্তন বা পিতৃস্বাস্থ্য সচেতনতা", "মানসিক চাপ সামলাতে নিভৃত সাধনার প্রয়োজন"],
                "hi": ["कार्यक्षेत्र में अचानक परिवर्तन अथवा पिता के स्वास्थ्य पर ध्यान", "कठिन समय में भावनात्मक पारदर्शिता बनाए रखना"],
            },
            "life_areas": {
                "career": {"en": "Excels in surgery, forensics, insurance, tax auditing, geology, and occult research.", "bn": "অস্ত্রোপচার, ফরেনসিক, বীমা, কর বিভাগ ও প্রাচীন গবেষণায় শুভ।", "hi": "शल्य चिकित्सा, फॉरेंसिक, बीमा, कराधान एवं गूढ़ शोध में उत्तम।"},
                "finance": {"en": "Gains through inheritances, settlements, and shared investments.", "bn": "উত্তরাধিকার, যৌথ বিনিয়োগ ও আকস্মিক আর্থিক প্রাপ্তির যোগ।", "hi": "पैतृक संपत्ति, बीमा दावों एवं साझा निवेश से लाभ।"},
                "relationship": {"en": "Values deep, transformative bonds over superficial pleasantries.", "bn": "ভঙ্গুর সম্পর্কের চেয়ে গভীর বিশ্বাসযোগ্য সম্পর্ককে প্রাধান্য দেয়।", "hi": "संबंधों में ऊपरी दिखावे की जगह गहरी निष्ठा को महत्व।"},
            },
        },
        9: {
            "title": {"en": "Sun in the 9th House", "bn": "৯ম ভাবে রবি (সূর্য)", "hi": "नवम भाव में सूर्य"},
            "simple": {
                "en": "The Sun in the 9th house establishes an illustrious alignment of dharma, fortune, mentors, higher education, and philosophical dignity.",
                "bn": "৯ম ভাবে রবির অবস্থান ভাগ্যোদয়ে সহায়ক, ধর্মপরায়ণতা, গুরুজনের সান্নিধ্য এবং উচ্চশিক্ষায় গৌরবোজ্জ্বল সাফল্যের পরিচায়ক।",
                "hi": "नवम भाव में सूर्य भाग्योदय, धार्मिक निष्ठा, गुरु कृपा एवं उच्च शिक्षा में उत्कृष्ट सफलता का कारक है।",
            },
            "positive": {
                "en": ["Strong moral compass and philosophical conviction", "Respect from mentors, teachers, and scholars", "Auspicious long-distance journeys broadening horizons"],
                "bn": ["দৃঢ় নীতিবোধ ও সত্যনিষ্ঠ ধর্মভাব", "শিক্ষক, গুরুজন ও মনীষীদের স্নেহ ও সম্মান লাভ", "দূরভ্রমণের মাধ্যমে প্রজ্ঞা ও ভাগ্যোন্নয়ন"],
                "hi": ["सुदृढ़ नैतिक मूल्य एवं आध्यात्मिक निष्ठा", "गुरुजनों, शिक्षकों एवं विद्वानों से आदर", "दूरस्थ यात्राओं से ज्ञान एवं भाग्य की वृद्धि"],
            },
            "challenges": {
                "en": ["Dogmatic defense of personal beliefs", "High expectations placed on teachers and guides"],
                "bn": ["নিজের মতবাদের প্রতি অতিরিক্ত গোঁড়ামি এড়ানো শ্রেয়", "গুরুজনদের বিষয়ে অতিরিক্ত প্রত্যাশা"],
                "hi": ["अपने विचारों के प्रति अत्यधिक कट्टरता से बचना", "शिक्षकों एवं मार्गदर्शकों से अत्यधिक अपेक्षाएं"],
            },
            "life_areas": {
                "career": {"en": "Thrives in academia, law, publishing, foreign advisory, and spiritual institutions.", "bn": "বিশ্ববিদ্যালয়, আইন, প্রকাশনা ও আন্তর্জাতিক পরামর্শে সাফল্য।", "hi": "शिक्षा, विधि, प्रकाशन, अंतरराष्ट्रीय परामर्श एवं धार्मिक संस्थाओं में प्रगति।"},
                "finance": {"en": "Steadfast wealth supported by principled actions and dharma.", "bn": "নীতিনিষ্ঠ কর্ম ও ভাগ্যের অনুকূলতায় দীর্ঘমেয়াদী ধনযোগ।", "hi": "धार्मिक आचरण एवं न्यायसंगत कार्यों से स्थिर धन लाभ।"},
                "relationship": {"en": "Deep reverence for family customs and spiritual companions.", "bn": "পারিবারিক সংস্কৃতি ও আত্মিক সংযোগকে মর্যাদা দান।", "hi": "पारिवारिक संस्कृति एवं वैचारिक समानता वाले संबंध।"},
            },
        },
        10: {
            "title": {"en": "Sun in the 10th House", "bn": "১০ম ভাবে রবি (সূর্য)", "hi": "दशम भाव में सूर्य"},
            "simple": {
                "en": "The Sun achieves Digbala (directional strength) in the 10th house, representing one of the finest positions for career authority, renown, and executive leadership.",
                "bn": "১০ম ভাবে রবি দিগ্বল (দিকশক্তি) লাভ করে, যা কর্মজীবনে সর্বোচ্চ প্রতিষ্ঠা, সুনাম, নেতৃত্ব ও প্রশাসনিক সাফল্যের শ্রেষ্ঠ সংকেত।",
                "hi": "दशम भाव में सूर्य दिग्बली होता है, जो आजीविका में सर्वोच्च प्रतिष्ठा, प्रशासनिक अधिकार एवं ख्याति हेतु सर्वोत्तम है।",
            },
            "positive": {
                "en": ["Apex professional achievements and public recognition", "Commanding leadership respected across organizations", "Unyielding sense of civic responsibility and honor"],
                "bn": ["কর্মক্ষেত্রে শীর্ষস্থান অর্জন ও সামাজিক স্বীকৃতি", "দৃঢ় নেতৃত্ব ও প্রশাসনিক ক্ষেত্রে মর্যাদা", "কর্তব্যের প্রতি নিখাদ নিষ্ঠা ও সততা"],
                "hi": ["कार्यक्षेत्र में शीर्ष पद एवं सामाजिक प्रतिष्ठा", "संगठनों में आदरणीय एवं प्रभावी नेतृत्व", "कर्तव्यनिष्ठा एवं समाज में उच्च मान-सम्मान"],
            },
            "challenges": {
                "en": ["Excessive career absorption overshadowing domestic life", "Sensitivity to professional status and hierarchy"],
                "bn": ["কাজের চাপে পারিবারিক সময় ব্যাহত হওয়ার আশঙ্কা", "কর্মক্ষেত্রের সম্মান নিয়ে অতিরিক্ত সচেতনতা"],
                "hi": ["कार्य में अत्यधिक व्यस्तता से गृहस्थ जीवन पर प्रभाव", "पद एवं प्रतिष्ठा को लेकर अत्यधिक संवेदनशीलता"],
            },
            "life_areas": {
                "career": {"en": "Exemplary for government administration, corporate directorships, politics, and industry captains.", "bn": "প্রশাসন, সরকারি উচ্চপদ, রাজনীতি ও বৃহৎ প্রতিষ্ঠানের নেতৃত্বে অপ্রতিরোধ্য।", "hi": "सरकारी उच्च पद, कॉर्पोरेट प्रबंधन, राजनीति एवं उद्योग जगत में अग्रणी।"},
                "finance": {"en": "Substantial financial standing through prominent contribution.", "bn": "মর্যাদাপূর্ণ কর্মের মাধ্যমে স্থায়ী ও সমৃদ্ধ আর্থিক ভিত্তি।", "hi": "उच्च पद एवं प्रतिष्ठा के माध्यम से विपुल धन संपदा।"},
                "relationship": {"en": "Requires conscious effort to allocate quality domestic time.", "bn": "কর্মের পাশাপাশি পরিবারকে গুণগত সময় দেওয়া প্রয়োজন।", "hi": "व्यस्त दिनचर्या के बीच परिवार को पर्याप्त समय देना चाहिए।"},
            },
        },
        11: {
            "title": {"en": "Sun in the 11th House", "bn": "১১শ ভাবে রবি (সূর্য)", "hi": "एकादश भाव में सूर्य"},
            "simple": {
                "en": "The Sun in the 11th house is traditionally an auspicious Upachaya placement, assuring realization of ambitions, influential alliances, and steady financial growth.",
                "bn": "১১শ ভাবে রবি উপচয় ভাবস্থ হওয়ায় অত্যন্ত শুভ, যা উচ্চাকাঙ্ক্ষা পূরণ, প্রভাবশালী শুভাকাঙ্ক্ষী এবং নিরবচ্ছিন্ন আয়বৃদ্ধি নিশ্চিত করে।",
                "hi": "एकादश भाव में सूर्य का होना अत्यंत शुभ है, जो महत्वाकांक्षाओं की पूर्ति, प्रभावशाली मित्रों का सहयोग एवं निरंतर आय दिलाता है।",
            },
            "positive": {
                "en": ["Steady accomplishment of major life aspirations", "Influential, distinguished social network and mentors", "Consistent, resilient streams of revenue"],
                "bn": ["জীবনের কাঙ্ক্ষিত লক্ষ্য ও স্বপ্নের বাস্তবায়ন", "সমাজে প্রতিষ্ঠিত ও প্রভাবশালী বন্ধুমহল", "নিয়মিত ও সম্মানজনক আয়ের প্রবাহ"],
                "hi": ["जीवन के महत्वपूर्ण लक्ष्यों की सहज पूर्ति", "प्रतिष्ठित एवं प्रभावशाली मित्रों का समर्थन", "नियमित एवं सुदृढ़ आय के स्रोत"],
            },
            "challenges": {
                "en": ["Expectation of unconditional deference from friends", "Balancing individual ambitions with collective welfare"],
                "bn": ["বন্ধুমহলে অতিরিক্ত কর্তৃত্ব প্রদর্শনের প্রবণতা এড়ানো", "ব্যক্তিগত স্বার্থ ও সামাজিক কল্যাণের ভারসাম্য"],
                "hi": ["मित्र मंडली में अत्यधिक प्रभुत्व जमाने की इच्छा", "व्यक्तिगत आकांक्षाओं एवं सामाजिक हित में संतुलन"],
            },
            "life_areas": {
                "career": {"en": "Favors corporate leadership, community mobilization, technology networks, and policy.", "bn": "বৃহৎ সংগঠন, প্রযুক্তিগত যোগাযোগ ও নীতি নির্ধারণে বিশেষ লাভ।", "hi": "कॉर्पोरेट प्रबंधन, तकनीकी नेटवर्क एवं नीति निर्माण में सफलता।"},
                "finance": {"en": "Magnificent gains supported by enterprise and executive standing.", "bn": "কাজের মাধ্যমে ধারাবাহিক ও সমৃদ্ধ আর্থিক প্রাপ্তি।", "hi": "प्रयासों एवं प्रतिष्ठा के बल पर उत्कृष्ट आर्थिक लाभ।"},
                "relationship": {"en": "Generous ally who commands loyalty across social circles.", "bn": "বন্ধুদের প্রতি উদার ও বিশ্বস্ত ব্যক্তিত্ব।", "hi": "सामाजिक दायरे में एक उदार एवं निष्ठावान साथी।"},
            },
        },
        12: {
            "title": {"en": "Sun in the 12th House", "bn": "১২শ ভাবে রবি (সূর্য)", "hi": "द्वादश भाव में सूर्य"},
            "simple": {
                "en": "The Sun in the 12th house channels soul energy toward inward self-discovery, spiritual illumination, foreign connections, and selfless philanthropy.",
                "bn": "১২শ ভাবে রবির অবস্থান অন্তর্মুখী আধ্যাত্মিক সাধনা, আত্মজ্ঞান, বৈদেশিক যোগাযোগ ও জনকল্যাণমূলক ত্যাগের পরিচায়ক।",
                "hi": "द्वादश भाव में सूर्य आंतरिक आत्म-साक्षात्कार, आध्यात्मिक प्रकाश, विदेश संबंध एवं परोपकार की भावना को जागृत करता है।",
            },
            "positive": {
                "en": ["Deep spiritual detachment and philosophical tranquility", "Success in foreign territories, distant institutions, or retreats", "Benevolent and philanthropic impulse without ego"],
                "bn": ["গভীর আধ্যাত্মিক ভাব ও নিভৃত মানসিক শান্তি", "বিদেশ বা দূরবর্তী সংস্থায় কাজের মাধ্যমে সাফল্য", "নিঃস্বার্থ জনকল্যাণ ও দানশীল মনোভাব"],
                "hi": ["गहरी आध्यात्मिक शांति एवं वैराग्य भाव", "विदेशों अथवा दूरस्थ संस्थानों में उत्तम सफलता", "अहंकार रहित परोपकारी एवं दानशील आचरण"],
            },
            "challenges": {
                "en": ["Feeling overlooked in conventional public settings", "Need to manage expenditures on private projects"],
                "bn": ["প্রথাগত জনসমক্ষে কখনও কখনও নিঃসঙ্গতার অনুভূতি", "ব্যয় নিয়ন্ত্রণের প্রতি বিশেষ নজর রাখা আবশ্যক"],
                "hi": ["पारंपरिक सामाजिक माहौल में उपेक्षित महसूस करना", "अनावश्यक व्ययों पर विवेकपूर्ण नियंत्रण आवश्यक"],
            },
            "life_areas": {
                "career": {"en": "Excels in multinational firms, hospitals, research foundations, and spiritual retreats.", "bn": "আন্তর্জাতিক সংস্থা, হাসপাতাল, গবেষণা কেন্দ্র ও আধ্যাত্মিক প্রতিষ্ঠানে শুভ।", "hi": "बहुराष्ट्रीय कंपनियों, अस्पतालों, शोध केंद्रों एवं आध्यात्मिक आश्रमों में प्रगति।"},
                "finance": {"en": "Gains from foreign connections; requires budgeting to prevent drain.", "bn": "বৈদেশিক সূত্রে লাভ হলেও ব্যয় নিয়ন্ত্রণে সজাগ থাকতে হবে।", "hi": "विदेश संपर्कों से लाभ; वित्तीय अनुशासन से धन संचय।"},
                "relationship": {"en": "Cherishes privacy and peaceful, secluded companionship.", "bn": "নিভৃত ও শান্ত পারিবারিক সাহচর্য পছন্দ করে।", "hi": "एकांत एवं शांतिपूर्ण दांपत्य को प्राथमिकता।"},
            },
        },
    },
    # The matrix for other planets follows the same rich structure.
}

# Generic Generator for the remaining 8 planets (Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu)
# across all 12 houses to guarantee a 100% complete 9x12 matrix.
def _get_base_matrix_entry(planet: str, house: int) -> Dict[str, Any]:
    # Check if pre-defined
    if planet in PLANET_HOUSE_DATA and house in PLANET_HOUSE_DATA[planet]:
        return PLANET_HOUSE_DATA[planet][house]

    p_info = PLANET_NAMES.get(planet, {"en": planet, "bn": planet, "hi": planet})
    h_info = HOUSE_NAMES.get(house, HOUSE_NAMES[1])
    sig = PLANET_SIGNIFICATORS.get(planet, {"en": "vital energy", "bn": "গ্রহীয় শক্তি", "hi": "ग्रहीय ऊर्जा"})

    title_en = f"{p_info['en']} in the {h_info['short_en']}"
    title_bn = f"{h_info['short_bn']}-এ {p_info['bn']}"
    title_hi = f"{h_info['short_hi']} में {p_info['hi']}"

    simple_en = (
        f"{p_info['en']} in the {h_info['short_en']} traditionally directs its core energies of {sig['en']} "
        f"into {h_info['themes_en']}."
    )
    simple_bn = (
        f"{h_info['short_bn']}-এ {p_info['bn']}-এর স্থিতি প্রথাগতভাবে {sig['bn']}-এর প্রতীকী শক্তিকে "
        f"{h_info['themes_bn']}-এর ক্ষেত্রে সক্রিয় করে তোলে।"
    )
    simple_hi = (
        f"{h_info['short_hi']} में {p_info['hi']} की स्थिति {sig['hi']} के प्रभाव को "
        f"{h_info['themes_hi']} के क्षेत्र में विशेष रूप से उन्मुख करती है।"
    )

    pos_en = [
        f"Constructive development across {h_info['themes_en']}",
        f"Natural resonance with {sig['en']}",
        "Focus and personal dedication over time",
    ]
    pos_bn = [
        f"{h_info['themes_bn']}-এর ক্ষেত্রে গঠনমূলক অগ্রগতি",
        f"{sig['bn']}-এর শুভ প্রভাবের স্ফুরণ",
        "সময়ের সাথে সাথে আত্মবিশ্বাস ও স্থিরতার বিকাশ",
    ]
    pos_hi = [
        f"{h_info['themes_hi']} के क्षेत्र में सकारात्मक विकास",
        f"{sig['hi']} के शुभ गुणों का प्रकटीकरण",
        "सतत अभ्यास एवं धैर्य से उल्लेखनीय सफलता",
    ]

    chal_en = [
        f"Mindful balance required when managing {h_info['themes_en']}",
        "Patience during adverse planetary transits",
    ]
    chal_bn = [
        f"{h_info['themes_bn']} পরিচালনার ক্ষেত্রে সম্যক সতর্কতা আবশ্যক",
        "প্রতিকূল গ্রহীয় গোচরে ধৈর্য্য রক্ষা করা প্রয়োজন",
    ]
    chal_hi = [
        f"{h_info['themes_hi']} के संदर्भ में संतुलित दृष्टिकोण आवश्यक",
        "विपरीत गोचर के समय संयम एवं धैर्य की आवश्यकता",
    ]

    car_en = f"Applies {p_info['en']}'s natural skills toward vocational responsibilities."
    car_bn = f"{p_info['bn']}-এর স্বাভাবিক গুণাবলী কর্মক্ষেত্রে ইতিবাচক প্রয়োগ নিশ্চিত করে।"
    car_hi = f"{p_info['hi']} के स्वाभाविक कौशल कार्यक्षेत्र में सहायक सिद्ध होते हैं।"

    fin_en = f"Influences financial stability according to sign dignity and house support."
    fin_bn = f"রাশি বলাবল ও ভাবাধিপতির অনুকূলতায় আর্থিক স্থায়িত্ব বজায় থাকে।"
    fin_hi = f"राशि बल एवं भावेश के सहयोग से वित्तीय संतुलन बना रहता है।"

    rel_en = f"Demands open communication and mutual respect in personal bonds."
    rel_bn = f"পারস্পরিক সম্পর্কে খোলাখুলি আলোচনা ও শ্রদ্ধাবোধ সৌহার্দ্য রক্ষা করে।"
    rel_hi = f"व्यक्तिगत संबंधों में संवाद एवं आदर भाव आवश्यक है।"

    return {
        "title": {"en": title_en, "bn": title_bn, "hi": title_hi},
        "simple": {"en": simple_en, "bn": simple_bn, "hi": simple_hi},
        "positive": {"en": pos_en, "bn": pos_bn, "hi": pos_hi},
        "challenges": {"en": chal_en, "bn": chal_bn, "hi": chal_hi},
        "life_areas": {
            "career": {"en": car_en, "bn": car_bn, "hi": car_hi},
            "finance": {"en": fin_en, "bn": fin_bn, "hi": fin_hi},
            "relationship": {"en": rel_en, "bn": rel_bn, "hi": rel_hi},
        },
    }


def get_planet_house_interpretation(
    planet: str,
    house: int,
    chart_obj: Any,
    dasha_summary: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Build the comprehensive 3-Level Planet-in-House Interpretation:
    - Level A: Traditional Placement Indications (Positive, Challenges, Life Areas)
    - Level B: Personalized Birth Chart Synthesis (House Lordships, Sign, Dignity, Conjunctions, Aspects)
    - Level C: Time-Based Vimshottari Dasha Timing Activation
    - Advanced Parashari Analysis Matrix
    """
    p_info = PLANET_NAMES.get(planet, {"en": planet, "bn": planet, "hi": planet})
    h_info = HOUSE_NAMES.get(house, HOUSE_NAMES[1])
    base = _get_base_matrix_entry(planet, house)

    # ─────────────────────────────────────────────────────────────────
    # LEVEL B: PERSONALIZED BIRTH CHART ANALYSIS
    # ─────────────────────────────────────────────────────────────────
    sign_idx = chart_obj.sign(planet)  # 1..12
    sign_name = SIGNS[sign_idx - 1]
    dignity = chart_obj.dignity(planet) or "neutral"
    is_retro = bool(chart_obj.planets[planet].get("retrograde"))
    is_combust = bool(chart_obj.planets[planet].get("combust"))

    # Actual House Lordships for this Ascendant
    lorded_houses = chart_obj.lorded(planet)  # e.g. [7, 10]
    lorded_str_en = ", ".join([f"{ordinal(h)} house" for h in lorded_houses]) if lorded_houses else "no direct rulership (Nodes)"
    lorded_str_bn = ", ".join([f"{h}ম ভাব" for h in lorded_houses]) if lorded_houses else "কোনো নির্দিষ্ট ভাবাধিপত্য নেই (রাহু/কেতু)"
    lorded_str_hi = ", ".join([f"{h}वें भाव" for h in lorded_houses]) if lorded_houses else "कोई प्रत्यक्ष स्वामित्व नहीं (छाया ग्रह)"

    # Conjunctions (other planets in the same house)
    all_occupants = chart_obj.occupants(house)
    conjunct_planets = [p for p in all_occupants if p != planet]
    conj_str_en = ", ".join(conjunct_planets) if conjunct_planets else "none"
    conj_str_bn = ", ".join([PLANET_NAMES.get(p, {}).get("bn", p) for p in conjunct_planets]) if conjunct_planets else "কেউ নেই"
    conj_str_hi = ", ".join([PLANET_NAMES.get(p, {}).get("hi", p) for p in conjunct_planets]) if conjunct_planets else "कोई नहीं"

    # Aspects received
    aspecting_planets = [p for p in PLANETS if p != planet and chart_obj.aspects(p, planet)]
    asp_str_en = ", ".join(aspecting_planets) if aspecting_planets else "none"
    asp_str_bn = ", ".join([PLANET_NAMES.get(p, {}).get("bn", p) for p in aspecting_planets]) if aspecting_planets else "কেউ নেই"
    asp_str_hi = ", ".join([PLANET_NAMES.get(p, {}).get("hi", p) for p in aspecting_planets]) if aspecting_planets else "कोई नहीं"

    # Personalized Narrative Synthesis
    if lorded_houses:
        lord_narrative_en = (
            f"In your birth chart, {p_info['en']} is the ruler of the {lorded_str_en}. "
            f"By occupying your {h_info['short_en']} in {sign_name}, it directly channels the vitality and portfolios of your "
            f"{lorded_str_en} into {h_info['short_en']} matters. "
        )
        lord_narrative_bn = (
            f"আপনার জন্মকুণ্ডলীতে {p_info['bn']} হলো {lorded_str_bn}-এর অধিপতি। "
            f"{sign_name} রাশিতে আপনার {h_info['short_bn']}-এ অবস্থান করার ফলে এটি {lorded_str_bn}-এর সম্ভাবনাকে "
            f"সরাসরি {h_info['short_bn']}-এর জীবনক্ষেত্রে প্রবাহিত করছে। "
        )
        lord_narrative_hi = (
            f"आपकी जन्मपत्रिका में {p_info['hi']} {lorded_str_hi} का स्वामी है। "
            f"{sign_name} राशि में आपके {h_info['short_hi']} में स्थित होने से यह {lorded_str_hi} की ऊर्जा को "
            f"प्रत्यक्ष रूप से {h_info['short_hi']} के क्षेत्र में संकेंद्रित करता है। "
        )
    else:
        lord_narrative_en = (
            f"In your birth chart, {p_info['en']} sits in {sign_name} within the {h_info['short_en']}. "
            f"As a karmic node, its expression is primarily shaped by its dispositor and aspecting influences. "
        )
        lord_narrative_bn = (
            f"আপনার জন্মকুণ্ডলীতে {p_info['bn']} {sign_name} রাশিতে {h_info['short_bn']}-এ অবস্থান করছে। "
            f"একটি ছায়া গ্রহ হিসেবে এর ফলাফল মূলত সংশ্লিষ্ট রাশিপতির শুভাশুভ বলের ওপর নির্ভরশীল। "
        )
        lord_narrative_hi = (
            f"आपकी जन्मपत्रिका में {p_info['hi']} {sign_name} राशि में {h_info['short_hi']} में स्थित है। "
            f"छाया ग्रह होने के कारण इसका फल राशि स्वामी एवं दृष्टि संबंधों के आधार पर रूपांतरित होता है। "
        )

    # Context Modifiers Narrative
    mod_items_en = []
    mod_items_bn = []
    mod_items_hi = []

    if dignity in ("exalted", "own", "moolatrikona"):
        mod_items_en.append(f"It possesses favorable dignity ({dignity}), strengthening its constructive potential.")
        mod_items_bn.append(f"এটি শুভ স্থানবল ({dignity}) নিয়ে অবস্থিত, যা অনুকূল ফলদানে বিশেষ সহায়ক।")
        mod_items_hi.append(f"यह शुभ स्थानबल ({dignity}) में स्थित है, जो सकारात्मक फल देने में सहायक है।")
    elif dignity == "debilitated":
        mod_items_en.append("It sits in debilitation, suggesting initial tests and requiring conscious self-discipline.")
        mod_items_bn.append("এটি নীচস্থ অবস্থায় রয়েছে, যা প্রাথমিক পরীক্ষা ও সচেতন আত্মসংযমের ইঙ্গিত দেয়।")
        mod_items_hi.append("यह नीच अवस्था में है, जो प्रारंभिक चुनौतियों एवं धैर्य की आवश्यकता को दर्शाता है।")

    if is_retro:
        mod_items_en.append("Retrograde motion intensifies inward reflection and unconventional application of its talents.")
        mod_items_bn.append("বক্রী গতির কারণে এর প্রভাব অন্তর্মুখী হয় এবং গতানুগতিকতার বাইরে নতুন দৃষ্টিভঙ্গি দেয়।")
        mod_items_hi.append("वक्री गति के कारण इसका प्रभाव गहन आत्म-चिंतन एवं नवाचार को प्रेरित करता है।")

    if is_combust:
        mod_items_en.append("Combustion by the Sun suggests internalizing its significations and cultivating patience.")
        mod_items_bn.append("রবির সান্নিধ্যে অস্তমিত হওয়ায় নিজস্ব গুণাবলী প্রকাশের ক্ষেত্রে ধৈর্য্য প্রয়োজন।")
        mod_items_hi.append("सूर्य के निकट अस्त होने से आंतरिक धैर्य एवं संयम की आवश्यकता होती है।")

    if conjunct_planets:
        mod_items_en.append(f"Conjunction with {conj_str_en} blends multiple planetary motivations in this house.")
        mod_items_bn.append(f"{conj_str_bn}-এর সাথে সহাবস্থান একাধিক গ্রহীয় শক্তির বিশেষ সমাবেশ ঘটিয়েছে।")
        mod_items_hi.append(f"{conj_str_hi} के साथ युति इस भाव में बहुआयामी ऊर्जा का संचार करती है।")

    if aspecting_planets:
        mod_items_en.append(f"Incoming aspects from {asp_str_en} cast modulating oversight onto this placement.")
        mod_items_bn.append(f"{asp_str_bn}-এর শুভাশুভ দৃষ্টি এর ফলাফলের সময়কাল ও প্রকাশকে পরিমার্জিত করে।")
        mod_items_hi.append(f"{asp_str_hi} की दृष्टि इसके परिणामों की गति एवं स्वरूप को प्रभावित करती है।")

    personalized_en = lord_narrative_en + " " + " ".join(mod_items_en)
    personalized_bn = lord_narrative_bn + " " + " ".join(mod_items_bn)
    personalized_hi = lord_narrative_hi + " " + " ".join(mod_items_hi)

    # ─────────────────────────────────────────────────────────────────
    # LEVEL C: TIME-BASED TIMING ACTIVATION (VIMSHOTTARI DASHA)
    # ─────────────────────────────────────────────────────────────────
    active_dasha_en = []
    active_dasha_bn = []
    active_dasha_hi = []

    if dasha_summary:
        for d in dasha_summary:
            lord = d.get("lord", "")
            if lord == planet or (lorded_houses and chart_obj.house_lord(house) == lord):
                active_dasha_en.append(f"{d.get('level', '').capitalize()} of {lord} (Active: {d.get('start', '')} to {d.get('end', '')})")
                active_dasha_bn.append(f"{lord}-এর {d.get('level', '')} (সময়কাল: {d.get('start', '')} থেকে {d.get('end', '')})")
                active_dasha_hi.append(f"{lord} की {d.get('level', '')} (अवधि: {d.get('start', '')} से {d.get('end', '')})")

    if not active_dasha_en:
        active_dasha_en.append(f"Major activation occurs during future Vimshottari Mahadasha and Antardasha cycles of {p_info['en']}.")
        active_dasha_bn.append(f"{p_info['bn']}-এর বিংশোত্তরী মহাদশা ও অন্তর্দশা চলাকালীন এই ভাবফল বিশেষভাবে সক্রিয় হয়।")
        active_dasha_hi.append(f"{p_info['hi']} की विंशोत्तरी महादशा एवं अंतर्दशा के दौरान यह फल विशेष सक्रिय होता है।")

    # ─────────────────────────────────────────────────────────────────
    # LEVEL D: ADVANCED PARASHARI ANALYSIS & RULE IDS
    # ─────────────────────────────────────────────────────────────────
    rule_id = f"PH-{planet.upper()}-H{house:02d}"
    basis_rule_ids = [rule_id]
    for lh in lorded_houses:
        basis_rule_ids.append(f"HL-H{lh:02d}-IN-H{house:02d}")

    return {
        "planet": planet,
        "planet_name": p_info,
        "house": house,
        "house_name": h_info,
        "sign_name": sign_name,
        "sign_index": sign_idx,
        "dignity": dignity,
        "is_retrograde": is_retro,
        "is_combust": is_combust,
        "lorded_houses": lorded_houses,
        "conjunct_planets": conjunct_planets,
        "aspecting_planets": aspecting_planets,
        # Level A: Traditional Indications
        "traditional": {
            "title": base["title"],
            "simple_explanation": base["simple"],
            "positive_results": base["positive"],
            "possible_challenges": base["challenges"],
            "life_areas": base["life_areas"],
        },
        # Level B: Personalized Birth Chart Analysis
        "personalized": {
            "explanation": {"en": personalized_en, "bn": personalized_bn, "hi": personalized_hi},
            "lorded_str": {"en": lorded_str_en, "bn": lorded_str_bn, "hi": lorded_str_hi},
            "sign_and_dignity": f"{sign_name} ({dignity})",
            "conjunctions_str": {"en": conj_str_en, "bn": conj_str_bn, "hi": conj_str_hi},
            "aspects_str": {"en": asp_str_en, "bn": asp_str_bn, "hi": asp_str_hi},
        },
        # Level C: Timing & Dasha Relevance
        "timing": {
            "activation_periods": {"en": active_dasha_en, "bn": active_dasha_bn, "hi": active_dasha_hi},
            "planet_lord": planet,
        },
        # Level D: Advanced Technical Parashari Matrix
        "advanced": {
            "rule_id": rule_id,
            "basis_rule_ids": basis_rule_ids,
            "bhava_sambandha": f"{planet} (Lord of {lorded_houses}) positioned in House {house}",
            "dignity_status": dignity,
            "retrograde": is_retro,
            "combust": is_combust,
        },
    }


def generate_all_planetary_interpretations(
    chart_obj: Any,
    dasha_summary: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Generate structured 3-Level interpretations for all 9 planets in this chart."""
    results = []
    for p in PLANETS:
        h = chart_obj.house(p)
        item = get_planet_house_interpretation(p, h, chart_obj, dasha_summary=dasha_summary)
        results.append(item)
    return results
