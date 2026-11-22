from .reference import TOPICS, PLANETS, GRAHAS7

def relevant(items, topic, chart=None, group_usage=None):
    t = TOPICS[topic]
    pri = set(t.get("primary", []))
    sup = set(t.get("supporting", []))
    kar = set(t.get("karakas", []))
    res = []

    pri_lords = set()
    pri_occupants = set()
    pri_aspected = set()
    sup_lords = set()
    sup_occupants = set()
    sup_aspected = set()

    if chart is not None:
        for h in pri:
            pri_lords.add(chart.house_lord(h))
            for p in chart.occupants(h):
                pri_occupants.add(p)
        for p in PLANETS:
            if any(h in pri for h in chart.aspected_houses(p)):
                pri_aspected.add(p)

        for h in sup:
            sup_lords.add(chart.house_lord(h))
            for p in chart.occupants(h):
                sup_occupants.add(p)
        for p in PLANETS:
            if any(h in sup for h in chart.aspected_houses(p)):
                sup_aspected.add(p)

    for e in items:
        grp = e.get("group")
        if group_usage is not None and grp:
            if group_usage.get(grp, 0) >= 2:
                # Do not reuse the same evidence group in more than 2 topics
                continue

        role = None
        planets = set(e.get("planets", []))
        houses = set(e.get("houses", []))
        facts = e.get("facts", {})

        direct_primary = False
        is_primary = False
        if chart is not None:
            # Direct Primary: specifically the primary house lord or occupying the primary house
            if (facts.get("house") in pri and e.get("kind") == "lord_placement") or \
               (facts.get("house") in pri and e.get("kind") == "placement") or \
               (facts.get("placed_in") in pri):
                direct_primary = True
                is_primary = True
            elif (planets & pri_lords) or (facts.get("lord") in pri_lords):
                is_primary = True
            elif (planets & pri_occupants) or (planets & pri_aspected):
                is_primary = True
        else:
            if houses & pri:
                is_primary = True
                direct_primary = True

        if is_primary:
            role = "primary"
        else:
            is_supporting = False
            if chart is not None:
                if (planets & sup_lords) or (facts.get("lord") in sup_lords) or (facts.get("house") in sup and e.get("kind") == "lord_placement"):
                    is_supporting = True
                elif (planets & sup_occupants) or (facts.get("house") in sup and e.get("kind") == "placement") or (facts.get("placed_in") in sup):
                    is_supporting = True
                elif planets & sup_aspected:
                    is_supporting = True
            else:
                if houses & sup:
                    is_supporting = True

            if is_supporting:
                role = "supporting"
            elif kar & planets and e.get("kind") in ("placement", "dignity"):
                role = "karaka"
            else:
                continue

        # Sub-priority: direct primary (0) > secondary primary (1) > supporting (2) > karaka (3)
        p_rank = 0 if direct_primary else (1 if is_primary else (2 if role == "supporting" else 3))
        res.append(dict(e, role=role, priority_rank=p_rank))

    return sorted(res, key=lambda x: (x.get("priority_rank", 9), x.get("rule_id", "")))


def aggregate(items, topic, issues, chart=None, group_usage=None):
    rel = relevant(items, topic, chart=chart, group_usage=group_usage)
    groups = {}
    for e in rel:
        if e.get("direction") == "neutral":
            continue
        grp = e.get("group", e.get("rule_id"))
        groups.setdefault(grp, []).append(e)

    sup_groups = []
    chal_groups = []
    mixed_groups = []

    for g, es in groups.items():
        ds = {e.get("direction") for e in es}
        is_prim = any(e.get("role") == "primary" for e in es)
        if ds == {"supportive"}:
            sup_groups.append((is_prim, g, es))
        elif ds == {"challenging"}:
            chal_groups.append((is_prim, g, es))
        else:
            mixed_groups.append((is_prim, g, es))

    # Primary items come first, supporting items only fill remaining slots
    # Cap 3 supportive + 2 challenging per topic
    sup_groups.sort(key=lambda x: (not x[0], x[1]))
    chal_and_mixed = chal_groups + mixed_groups
    chal_and_mixed.sort(key=lambda x: (not x[0], x[1]))

    selected_sup = sup_groups[:3]
    selected_chal_mixed = chal_and_mixed[:2]

    selected_groups = selected_sup + selected_chal_mixed
    selected_items = []
    for _, g, es in selected_groups:
        selected_items.extend(es)
        if group_usage is not None:
            group_usage[g] = group_usage.get(g, 0) + 1

    sup_count = len(selected_sup)
    chal_count = sum(1 for is_p, g, es in selected_chal_mixed if {e.get("direction") for e in es} == {"challenging"})
    mixed_count = len(selected_chal_mixed) - chal_count
    prim_count = sum(1 for is_p, g, es in selected_groups if is_p)
    n = sup_count + chal_count + mixed_count
    dom = max(sup_count, chal_count) if n > 0 else 0

    if issues or n < 3:
        lvl = "Limited"
    elif n >= 4 and prim_count >= 1 and (dom / n >= 0.7) and min(sup_count, chal_count) <= 1 and mixed_count <= 1:
        lvl = "Convergent"
    else:
        lvl = "Moderate"

    # Lean must be "mixed" when mixed factors >= supportive factors
    if mixed_count >= sup_count or (sup_count == chal_count):
        lean = "mixed"
    elif sup_count > chal_count + mixed_count:
        lean = "predominantly supportive"
    elif chal_count > sup_count + mixed_count:
        lean = "predominantly challenging"
    else:
        lean = "mixed"

    why = (
        f"{n} independent factor groups ({sup_count} supportive, {chal_count} challenging, {mixed_count} mixed); "
        f"{prim_count} involve primary houses; duplicate rules sharing the same planet/placement counted once"
        + ("; chart data issues cap the level at Limited" if issues else "")
        + ". Labels are not probabilities."
    )

    return {
        "items": selected_items,
        "counts": {
            "supportive": sup_count,
            "challenging": chal_count,
            "mixed": mixed_count,
            "independent_groups": n,
        },
        "level": lvl,
        "lean": lean,
        "explanation": why,
    }
