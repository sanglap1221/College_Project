from .reference import *
class ChartError(ValueError): pass

class Chart:
    """Wraps chart facts supplied by the trusted calculation engine.
    Never recomputes positions; only derives whole-sign houses and checks consistency."""
    def __init__(self, data, cfg=None):
        self.cfg = cfg or {}
        self.id = data.get("chart_id", "unknown")
        self.issues, self.notes = [], []
        self.lagna = int(data["lagna_sign"])
        if not 1 <= self.lagna <= 12: raise ChartError("lagna_sign must be 1-12")
        self.planets = {}
        for n in PLANETS:
            p = (data.get("planets") or {}).get(n)
            if p is None: raise ChartError(f"missing planet: {n}")
            sign = int(p["sign"])
            if not 1 <= sign <= 12: raise ChartError(f"{n}: sign must be 1-12")
            house = (sign - self.lagna) % 12 + 1
            if "house" in p and int(p["house"]) != house:
                raise ChartError(f"{n}: supplied house {p['house']} != whole-sign house {house}")
            if p.get("degree") is None:
                self.notes.append(f"{n}: degree not supplied (degree-based dignity skipped)")
            self.planets[n] = {"sign":sign,"degree":p.get("degree"),"house":house,
                               "retrograde":p.get("retrograde"),"combust":p.get("combust")}
        if (self.planets["Rahu"]["sign"] - self.planets["Ketu"]["sign"]) % 12 != 6:
            self.issues.append("Rahu and Ketu are not in opposite signs")
        self.dashas = data.get("dashas", [])
        if not self.dashas: self.notes.append("no dasha data supplied; timing section skipped")

    def sign(self, p): return self.planets[p]["sign"]
    def house(self, p): return self.planets[p]["house"]
    def house_sign(self, h): return (self.lagna + h - 2) % 12 + 1
    def house_lord(self, h): return SIGN_LORD[self.house_sign(h)]
    def lorded(self, p): return [h for h in range(1,13) if self.house_lord(h) == p]
    def occupants(self, h): return [p for p in PLANETS if self.house(p) == h]
    def aspect_offsets(self, p):
        if p in ("Rahu","Ketu"): return self.cfg.get("node_aspects",[7])
        return ASPECT_OFFSETS[p]
    def aspected_houses(self, p):
        return [(self.house(p) + o - 2) % 12 + 1 for o in self.aspect_offsets(p)]
    def aspects(self, a, b): return self.house(b) in self.aspected_houses(a)
    def rel_house(self, p, ref):  # house of p counted from ref planet's sign
        return (self.sign(p) - self.sign(ref)) % 12 + 1

    def dignity(self, p):
        if p not in GRAHAS7: return None  # nodes: no default dignity (configurable, disputed)
        s, d = self.sign(p), self.planets[p]["degree"]
        mt = MOOLATRIKONA.get(p)
        if EXALT[p] == s: return "exalted"
        if DEBIL[p] == s: return "debilitated"
        if mt and mt[0] == s and d is not None and mt[1] <= d < mt[2]: return "moolatrikona"
        if s in OWN[p]: return "own"
        return None
    def in_own_or_exalted(self, p):
        return p in GRAHAS7 and (self.sign(p) in OWN[p] or self.sign(p) == EXALT[p])
