from datetime import date, timedelta
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

def _direction_for_lord(chart, L):
    """Evaluate whether a planet's dasha influence is supportive/challenging/mixed
    based on dignity, house placement, and lordship of benefic/malefic houses."""
    h = chart.house(L)
    lords = chart.lorded(L)
    dig = chart.dignity(L)

    supportive = 0
    challenging = 0

    # Dignity factors
    if dig == "exalted": supportive += 2
    elif dig == "moolatrikona": supportive += 2
    elif dig == "own": supportive += 1
    elif dig == "debilitated": challenging += 2

    # House placement factors
    if h in KENDRA or h in TRIKONA: supportive += 1
    if h in DUSTHANA: challenging += 1

    # Lordship of benefic/malefic houses
    for lh in lords:
        if lh in KENDRA or lh in TRIKONA: supportive += 1
        if lh in DUSTHANA: challenging += 1

    if supportive > challenging: return "supportive"
    if challenging > supportive: return "challenging"
    return "mixed"

def evidence(chart, ref_date):
    out=[]; act=active(chart,ref_date); by={p["level"]:p for p in act}
    for p in act:
        L=p["lord"]; lords=chart.lorded(L); h=chart.house(L)
        direction = _direction_for_lord(chart, L)
        extra=f", ruling the {', '.join(ordinal(x) for x in lords)} house(s)" if lords else ""
        out.append({"rule_id":f"DASHA-{p['level']}","rule_version":"2.0.0","kind":"dasha",
          "houses":sorted(set([h]+lords)),"planets":[L],"direction":direction,
          "text":f"The {p['level']} of {L} (from {p['start']} to {p['end']}, as supplied) activates {L}, placed in the {ordinal(h)} house{extra}; the period may be read as emphasizing those areas.",
          "group":f"dasha:{p['level']}:{L}","facts":p,"timing":{"level":p["level"],"lord":L,"start":p["start"],"end":p["end"]}})
    if "MD" in by and "AD" in by:
        a,b=by["MD"]["lord"],by["AD"]["lord"]; rel=relation(chart,a,b)
        # Evaluate combined MD+AD direction
        md_dir = _direction_for_lord(chart, a)
        ad_dir = _direction_for_lord(chart, b)
        combined = "supportive" if md_dir=="supportive" and ad_dir=="supportive" else \
                   "challenging" if md_dir=="challenging" and ad_dir=="challenging" else "mixed"
        out.append({"rule_id":"DASHA-MD-AD-LINK","rule_version":"2.0.0","kind":"dasha",
          "houses":sorted({chart.house(a),chart.house(b)}),"planets":sorted({a,b}),"direction":combined,
          "text":f"The {a} Mahadasha and {b} Antardasha lords have this natal relationship: {rel}. Combined influence: {combined}.",
          "group":f"dasha:link:{a}-{b}","facts":{"relation":rel,"md_direction":md_dir,"ad_direction":ad_dir},"timing":{"level":"AD","lord":b,"start":by["AD"]["start"],"end":by["AD"]["end"]}})
    return out

def current_dasha(chart, ref_date):
    """Return the currently active Mahadasha and Antardasha for ref_date.
    Reuses existing chart.dashas (flat list from service.py) — no new calculations."""
    ref=_d(ref_date) if isinstance(ref_date,str) else ref_date
    act = [p for p in chart.dashas if _d(p["start"])<=ref<=_d(p["end"])]
    md = next((p for p in act if p["level"]=="mahadasha"), None)
    ad = next((p for p in act if p["level"]=="antardasha"), None)
    return {"mahadasha": md, "antardasha": ad}

def upcoming_antardashas(chart, ref_date, limit=6):
    """Return upcoming Antardasha periods after ref_date.
    Reuses existing chart.dashas — no new calculations."""
    ref=_d(ref_date) if isinstance(ref_date,str) else ref_date
    future = []
    for p in chart.dashas:
        if p["level"]=="antardasha" and _d(p["start"]) > ref:
            future.append(p)
    future.sort(key=lambda x: _d(x["start"]))
    return future[:limit]

def event_timing_windows(chart, ref_date, topic, lookback_days=365):
    """Generate event timing windows for a topic based on Antardasha periods
    where the Antardasha lord connects to the topic's primary/supporting houses.
    Reuses existing chart.dashas — no new calculations."""
    from .reference import TOPICS
    t = TOPICS.get(topic, {"primary": [], "supporting": [], "karakas": []})
    pri = set(t.get("primary", []))
    sup = set(t.get("supporting", []))
    kar = set(t.get("karakas", []))

    ref=_d(ref_date) if isinstance(ref_date,str) else ref_date
    windows = []

    # Build planet relevance sets for the topic
    pri_lords = set()
    pri_occupants = set()
    pri_aspected = set()
    for h in pri:
        pri_lords.add(chart.house_lord(h))
        for p in chart.occupants(h):
            pri_occupants.add(p)
    for p in PLANETS:
        if any(h in pri for h in chart.aspected_houses(p)):
            pri_aspected.add(p)

    sup_lords = set()
    for h in sup:
        sup_lords.add(chart.house_lord(h))

    # Scan all Antardasha periods for windows
    for entry in chart.dashas:
        if entry["level"] != "antardasha":
            continue
        ad_start = _d(entry["start"])
        ad_end = _d(entry["end"])
        ad_lord = entry["lord"]
        md_lord = entry.get("mahadasha_lord") or entry["lord"]  # fallback

        # Window must be in the future relative to ref_date or currently active
        if ad_end <= ref:
            continue

        window_start = max(ad_start, ref)
        if window_start > ad_end:
            continue

        # Check if Antardasha lord connects to topic houses
        connects = False
        connection_detail = []
        if ad_lord in pri_lords:
            connects = True
            connection_detail.append(f"rules primary house(s): {sorted(h for h in pri if chart.house_lord(h)==ad_lord)}")
        if ad_lord in pri_occupants:
            connects = True
            connection_detail.append(f"occupies primary house(s): {sorted(h for h in pri if chart.house(ad_lord)==h)}")
        if ad_lord in pri_aspected:
            connects = True
            connection_detail.append(f"aspects primary house(s)")
        if ad_lord in sup_lords:
            connects = True
            connection_detail.append(f"rules supporting house(s): {sorted(h for h in sup if chart.house_lord(h)==ad_lord)}")
        if ad_lord in kar:
            connects = True
            connection_detail.append(f"is karaka for {topic}")

        if not connects:
            continue

        direction = _direction_for_lord(chart, ad_lord)
        md_direction = _direction_for_lord(chart, md_lord) if md_lord != ad_lord else direction

        windows.append({
            "mahadasha_lord": md_lord,
            "antardasha_lord": ad_lord,
            "start_date": entry["start"],
            "end_date": entry["end"],
            "direction": direction,
            "md_direction": md_direction,
            "connection": "; ".join(connection_detail),
            "strength": "strong" if direction=="supportive" and md_direction=="supportive" else \
                        "moderate" if direction in ("supportive","mixed") or md_direction in ("supportive","mixed") else \
                        "weak",
        })

    windows.sort(key=lambda w: _d(w["start_date"]))
    return windows
