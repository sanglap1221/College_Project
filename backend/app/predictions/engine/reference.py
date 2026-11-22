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
# (sign, from_deg, to_deg) -- DRAFT, tradition-dependent
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
# primary / supporting houses and karakas, from Rulebook section 12
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
def ordinal(n):
    return f"{n}{'th' if 10<=n%100<=20 else {1:'st',2:'nd',3:'rd'}.get(n%10,'th')}"
