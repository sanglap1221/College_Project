import json, os
from .reference import *
from . import yogas as Y
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def load(name):
    with open(os.path.join(ROOT,name),encoding="utf-8") as f: return json.load(f)

class RuleBook:
    def __init__(self):
        self.cfg=load("config/ruleset.json")
        self.ph={(r["conditions"]["planet"],r["conditions"]["house"]):r for r in load("rules/planet_in_house.json")}
        self.hl={(r["conditions"]["lord_of_house"],r["conditions"]["placed_in_house"]):r for r in load("rules/house_lord_in_house.json")}
        self.dg={(r["conditions"]["planet"],r["conditions"]["dignity"]):r for r in load("rules/dignity.json")}
        self.yoga={y["id"]:y for y in load("rules/yogas.json")}
        self.forbidden=load("rules/forbidden_claims.json")["patterns"]
    def yoga_family(self,yid):
        for k,v in self.yoga.items():
            if k==yid or (k.endswith("*") and yid.startswith(k[:-1])): return v

def ev(rule_id,version,kind,houses,planets,direction,text,group,facts):
    return {"rule_id":rule_id,"rule_version":version,"kind":kind,"houses":sorted(set(houses)),
            "planets":sorted(set(planets)),"direction":direction,"text":text,"group":group,"facts":facts}

def evaluate(chart, rb):
    out, en = [], rb.cfg["enabled"]
    if en["planet_in_house"]:
        for p in PLANETS:
            r=rb.ph[(p,chart.house(p))]; h=chart.house(p); lords=chart.lorded(p)
            extra=f" It also rules the {', '.join(ordinal(x) for x in lords)} house(s)." if lords else ""
            out.append(ev(r["id"],r["version"],"placement",[h]+lords,[p],r["effect_direction"],
                r["interpretation_template"]+extra,f"placement:{p}",{"planet":p,"house":h,"sign":SIGNS[chart.sign(p)-1],"rules":lords}))
    if en["house_lord_in_house"]:
        for h in range(1,13):
            L=chart.house_lord(h); p=chart.house(L); r=rb.hl[(h,p)]
            out.append(ev(r["id"],r["version"],"lord_placement",[h,p],[L],r["effect_direction"],
                f"({L}) "+r["interpretation_template"],f"placement:{L}",{"house":h,"lord":L,"placed_in":p}))
    if en["dignity"]:
        for p in GRAHAS7:
            d=chart.dignity(p)
            if d:
                r=rb.dg[(p,d)]
                out.append(ev(r["id"],r["version"],"dignity",[chart.house(p)]+chart.lorded(p),[p],r["effect_direction"],
                    r["interpretation_template"],f"dignity:{p}",{"planet":p,"dignity":d}))
    trace=[]
    if en["yogas"]:
        for y in Y.detect_all(chart, rb.cfg):
            trace.append(y)
            if not y["passed"]: continue
            fam=rb.yoga_family(y["id"]); ps=", ".join(y["planets"])
            t=fam["template"].format(name=y["name"],planets=ps,planets_first=y["planets"][0])
            out.append(ev(y["id"],fam["version"],"yoga",y["houses"],y["planets"],fam["direction"],t,
                          "yoga:"+"+".join(sorted(y["planets"])),{"yoga":y["name"],"conditions":y["conditions"]}))
    return out, trace
