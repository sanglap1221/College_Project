import json, os
from .reference import *
from . import yogas as Y

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return json.load(f)

class RuleBook:
    def __init__(self):
        self.cfg = load("config/ruleset.json")
        self.ph = {(r["conditions"]["planet"], r["conditions"]["house"]): r for r in load("rules/planet_in_house.json")}
        self.hl = {(r["conditions"]["lord_of_house"], r["conditions"]["placed_in_house"]): r for r in load("rules/house_lord_in_house.json")}
        self.dg = {(r["conditions"]["planet"], r["conditions"]["dignity"]): r for r in load("rules/dignity.json")}
        self.yoga = {y["id"]: y for y in load("rules/yogas.json")}
        self.forbidden = load("rules/forbidden_claims.json")["patterns"]

    def yoga_family(self, yid):
        if yid.startswith("YOGA-CLUSTER-"):
            return {
                "name": "Conjunction Cluster",
                "version": "2.0.0",
                "direction": "supportive",
                "template": "{name} concentrates the combined planetary energies of {planets} into a single focal domain.",
            }
        for k, v in self.yoga.items():
            if k == yid or (k.endswith("*") and yid.startswith(k[:-1])):
                return v
        return {
            "name": "Classical Yoga",
            "version": "2.0.0",
            "direction": "supportive",
            "template": "{name} formed by {planets}.",
        }

def ev(rule_id, version, kind, houses, planets, direction, text, group, facts):
    return {
        "rule_id": rule_id,
        "rule_version": version,
        "kind": kind,
        "houses": sorted(set(houses)),
        "planets": sorted(set(planets)),
        "direction": direction,
        "text": text,
        "group": group,
        "facts": facts,
    }

def evaluate(chart, rb):
    out, en = [], rb.cfg["enabled"]
    if en["planet_in_house"]:
        for p in PLANETS:
            r = rb.ph[(p, chart.house(p))]
            h = chart.house(p)
            lords = chart.lorded(p)
            extra = f" It also rules the {', '.join(ordinal(x) for x in lords)} house(s)." if lords else ""
            txt = (r["interpretation_template"] + extra).replace("first house's themes", "that house's themes")
            out.append(ev(
                r["id"],
                r["version"],
                "placement",
                [h] + lords,
                [p],
                r["effect_direction"],
                txt,
                f"placement:{p}",
                {"planet": p, "house": h, "sign": SIGNS[chart.sign(p) - 1], "rules": lords},
            ))
    if en["house_lord_in_house"]:
        for h in range(1, 13):
            L = chart.house_lord(h)
            p = chart.house(L)
            r = rb.hl[(h, p)]
            direction = r["effect_direction"]
            # Lords of houses 6, 8, 12 placed in kendra/trikona must be direction "mixed", not "supportive"
            if h in (6, 8, 12) and (p in KENDRA or p in TRIKONA):
                direction = "mixed"
            txt = r["interpretation_template"].replace("first house's themes", "that house's themes")
            out.append(ev(
                r["id"],
                r["version"],
                "lord_placement",
                [h, p],
                [L],
                direction,
                f"({L}) " + txt,
                f"placement:{L}",
                {"house": h, "lord": L, "placed_in": p},
            ))
    if en["dignity"]:
        for p in GRAHAS7:
            d = chart.dignity(p)
            if d:
                r = rb.dg[(p, d)]
                txt = r["interpretation_template"].replace("first house's themes", "that house's themes")
                out.append(ev(
                    r["id"],
                    r["version"],
                    "dignity",
                    [chart.house(p)] + chart.lorded(p),
                    [p],
                    r["effect_direction"],
                    txt,
                    f"dignity:{p}",
                    {"planet": p, "dignity": d},
                ))
    trace = []
    if en["yogas"]:
        for y in Y.detect_all(chart, rb.cfg):
            trace.append(y)
            if not y["passed"]:
                continue
            fam = rb.yoga_family(y["id"])
            ps = ", ".join(y["planets"])
            p_first = y["planets"][0] if y["planets"] else ""
            t = fam["template"].format(name=y["name"], planets=ps, planets_first=p_first)
            out.append(ev(
                y["id"],
                fam["version"],
                "yoga",
                y["houses"],
                y["planets"],
                fam["direction"],
                t,
                "yoga:" + "+".join(sorted(y["planets"])),
                {"yoga": y["name"], "conditions": y["conditions"]},
            ))
    return out, trace
