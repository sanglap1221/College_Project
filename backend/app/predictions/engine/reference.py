"""Static reference tables. Dignity degrees and all classical conventions are
DRAFT until verified against your chosen edition (see source.status in rules)."""
SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio",
         "Sagittarius","Capricorn","Aquarius","Pisces"]
PLANETS = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]
GRAHAS7 = PLANETS[:7]
SIGN_LORD = {1:"Mars",2:"Venus",3:"Mercury",4:"Moon",5:"Sun",6:"Mercury",
             7:"Venus",8:"Mars",9:"Jupiter",10:"Saturn",11:"Saturn",12:"Jupiter"}
EXALT = {"Sun":1,"Moon":2,"Mars":10,"Mercury":6,"Jupiter":4,"Venus":12,"Saturn":7}
DEBIL = {"Sun":7,"Moon":8,"Mars":4,"Mercury":12,"Jupiter":10,"Venus":6,"Saturn":1}
OWN = {"Sun":[5],"Moon":[4],"Mars":[1,8],"Mercury":[3,6],"Jupiter":[9,12],
       "Venus":[2,7],"Saturn":[10,11]}
MOOLATRIKONA = {"Sun":(5,0,20),"Moon":(2,4,30),"Mars":(1,0,12),"Mercury":(6,16,20),
                "Jupiter":(9,0,10),"Venus":(7,0,15),"Saturn":(11,0,20)}
ASPECT_OFFSETS = {"Sun":[7],"Moon":[7],"Mercury":[7],"Venus":[7],
                  "Mars":[4,7,8],"Jupiter":[5,7,9],"Saturn":[3,7,10]}
KENDRA=[1,4,7,10]; TRIKONA=[1,5,9]; DUSTHANA=[6,8,12]; UPACHAYA=[3,6,10,11]
MALEFIC=["Sun","Mars","Saturn","Rahu","Ketu"]; BENEFIC=["Jupiter","Venus","Mercury"]

HOUSE_DOMAIN = {
 1:"embodiment, temperament and agency",
 2:"family context, speech and accumulated resources",
 3:"effort, courage, skills and communication",
 4:"home, inner security and the foundations of learning",
 5:"learning, creativity and children (traditional framing)",
 6:"service, routines, contest and obstacles",
 7:"partnerships and agreements",
 8:"change, shared resources and research",
 9:"dharma, mentors and higher learning",
 10:"vocation, responsibility and visible contribution",
 11:"gains, networks and goals",
 12:"expenditure, retreat, and foreign or inward contexts"}

PLANET_KEYWORDS = {
 "Sun":"authority, visibility, purpose and leadership",
 "Moon":"mind, emotional processing and receptivity",
 "Mars":"initiative, courage, assertion and technical action",
 "Mercury":"analysis, language, commerce and learning",
 "Jupiter":"knowledge, counsel, growth and ethics",
 "Venus":"relationships, aesthetics, diplomacy and comforts",
 "Saturn":"discipline, endurance, systems and responsibility",
 "Rahu":"unconventional ambition, amplification and experimentation",
 "Ketu":"detachment, inward focus and specialization"}

TOPICS = {
 "personality":{"title":"Personality and tendencies","primary":[1],"supporting":[],"karakas":["Moon"]},
 "career":{"title":"Career and vocation","primary":[10],"supporting":[6,2,11,1,9,3],"karakas":["Sun","Saturn","Mercury","Mars"]},
 "finance":{"title":"Finances and wealth themes","primary":[2,11],"supporting":[5,9,10,4],"karakas":[]},
 "education":{"title":"Education and learning","primary":[4,5,9],"supporting":[2,3],"karakas":["Mercury","Jupiter"]},
 "marriage":{"title":"Relationships and partnerships","primary":[7],"supporting":[2,5,8],"karakas":["Venus","Jupiter"]},
 "children":{"title":"Children and parenthood (traditional symbolism)","primary":[5],"supporting":[],"karakas":["Jupiter"]},
 "family_home":{"title":"Family and home","primary":[2,4],"supporting":[7,8],"karakas":["Moon"]},
 "property":{"title":"Property and vehicles","primary":[4],"supporting":[2,11],"karakas":["Mars"]},
 "travel":{"title":"Travel and foreign connection","primary":[9,12],"supporting":[3,7,4],"karakas":[]},
 "health":{"title":"Health-related traditional themes (non-diagnostic)","primary":[1],"supporting":[6,8,12],"karakas":["Moon","Sun"],"restricted":True},
 "spirituality":{"title":"Spirituality and values","primary":[9,12],"supporting":[5],"karakas":["Jupiter","Ketu","Moon"]},
 "communication":{"title":"Siblings, communication and initiative","primary":[3],"supporting":[11],"karakas":["Mars","Mercury"]},
 "disputes_service":{"title":"Service, routines and disputes","primary":[6],"supporting":[3,10,11],"karakas":[]},
}

TOPIC_TITLES = {
    "en": {
        "personality": "Personality and tendencies",
        "career": "Career and vocation",
        "finance": "Finances and wealth themes",
        "education": "Education and learning",
        "marriage": "Relationships and partnerships",
        "children": "Children and parenthood (traditional symbolism)",
        "family_home": "Family and home",
        "property": "Property and vehicles",
        "travel": "Travel and foreign connection",
        "health": "Health-related traditional themes (non-diagnostic)",
        "spirituality": "Spirituality and values",
        "communication": "Siblings, communication and initiative",
        "disputes_service": "Service, routines and disputes",
    },
    "bn": {
        "personality": "ব্যক্তিত্ব ও চারিত্রিক বৈশিষ্ট্য",
        "career": "কর্মজীবন ও পেশা",
        "finance": "অর্থ ও সম্পদ যোগ",
        "education": "শিক্ষা ও বিদ্যালাভ",
        "marriage": "দাম্পত্য ও সম্পর্ক",
        "children": "সন্তান ও পরিবার",
        "family_home": "গৃহ ও পারিবারিক পরিবেশ",
        "property": "সম্পত্তি ও যানবাহন",
        "travel": "ভ্রমণ ও দূরসংযোগ",
        "health": "স্বাস্থ্য ও জীবনীশক্তি (প্রথাগত বিচার)",
        "spirituality": "আধ্যাত্মিকতা ও ধর্মভাব",
        "communication": "যোগাযোগ, ভাইবোন ও উদ্যম",
        "disputes_service": "সেবা ও বাধা উত্তরণ",
    },
    "hi": {
        "personality": "व्यक्तित्व एवं स्वभाव",
        "career": "आजीविका एवं कार्यक्षेत्र",
        "finance": "वित्त एवं धन संपत्ति योग",
        "education": "शिक्षा एवं विद्या",
        "marriage": "वैवाहिक जीवन एवं साझेदारी",
        "children": "संतान एवं पारिवारिक योग",
        "family_home": "परिवार एवं गृह सुख",
        "property": "भूमि, भवन एवं वाहन",
        "travel": "यात्रा एवं विदेश संपर्क",
        "health": "स्वास्थ्य एवं ऊर्जा (पारंपरिक संकेत)",
        "spirituality": "अध्यात्म एवं धार्मिक विचार",
        "communication": "संवाद, भ्रातृ सुख एवं पराक्रम",
        "disputes_service": "सेवा, प्रतियोगिता एवं निवारण",
    },
}

def ordinal(n):
    return f"{n}{'th' if 10<=n%100<=20 else {1:'st',2:'nd',3:'rd'}.get(n%10,'th')}"
