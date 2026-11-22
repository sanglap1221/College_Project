from datetime import date
from .reference import *
def _d(s): return date.fromisoformat(s)
def active(chart, ref):
    ref=_d(ref) if isinstance(ref,str) else ref
    return [p for p in chart.dashas if _d(p["start"])<=ref<=_d(p["end"])]
def relation(chart,a,b):
    if a==b: return "same planet"
    if chart.sign(a)==chart.sign(b): return "conjunction"
    sa=[h for h in range(1,13) if SIGN_LORD[h]==b]; sb=[h for h in range(1,13) if SIGN_LORD[h]==a]
    if chart.sign(a) in sa and chart.sign(b) in sb: return "sign exchange"
    x,y=chart.aspects(a,b),chart.aspects(b,a)
    return "mutual aspect" if x and y else "aspect" if x or y else "no direct link"
def evidence(chart, ref_date):
    out=[]; act=active(chart,ref_date); by={p["level"]:p for p in act}
    for p in act:
        L=p["lord"]; lords=chart.lorded(L); h=chart.house(L)
        extra=f", ruling the {', '.join(ordinal(x) for x in lords)} house(s)" if lords else ""
        out.append({"rule_id":f"DASHA-{p['level']}","rule_version":"2.0.0","kind":"dasha",
          "houses":sorted(set([h]+lords)),"planets":[L],"direction":"neutral",
          "text":f"The {p['level']} of {L} (from {p['start']} to {p['end']}, as supplied) activates {L}, placed in the {ordinal(h)} house{extra}; the period may be read as emphasizing those areas.",
          "group":f"dasha:{p['level']}:{L}","facts":p,"timing":{"level":p["level"],"lord":L,"start":p["start"],"end":p["end"]}})
    if "MD" in by and "AD" in by:
        a,b=by["MD"]["lord"],by["AD"]["lord"]; rel=relation(chart,a,b)
        out.append({"rule_id":"DASHA-MD-AD-LINK","rule_version":"2.0.0","kind":"dasha",
          "houses":sorted({chart.house(a),chart.house(b)}),"planets":sorted({a,b}),"direction":"neutral",
          "text":f"The {a} Mahadasha and {b} Antardasha lords have this natal relationship: {rel}.",
          "group":f"dasha:link:{a}-{b}","facts":{"relation":rel},"timing":{"level":"AD","lord":b,"start":by["AD"]["start"],"end":by["AD"]["end"]}})
    return out
