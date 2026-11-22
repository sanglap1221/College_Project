"""Condition-by-condition yoga detectors. All DRAFT: validate against your edition and
astrologer-reviewed fixtures before enabling in production."""
from .reference import *
def _r(id_, name, conds, planets, houses):
    return {"id":id_,"name":name,"conditions":conds,"passed":all(c["pass"] for c in conds),
            "planets":planets,"houses":houses}

def pancha_mahapurusha(c, cfg):
    names = {"Mars":"Ruchaka","Mercury":"Bhadra","Jupiter":"Hamsa","Venus":"Malavya","Saturn":"Sasha"}
    out = []
    for p, nm in names.items():
        h = c.house(p)
        out.append(_r(f"YOGA-PMP-{p.upper()}", f"{nm} Yoga",
            [{"cond":f"{p} in own or exalted sign","pass":c.in_own_or_exalted(p)},
             {"cond":f"{p} in a kendra (1/4/7/10) from Lagna","pass":h in KENDRA}], [p],[h]))
    return out

def gaja_kesari(c, cfg):
    rel = c.rel_house("Jupiter","Moon")
    conds = [{"cond":"Jupiter in kendra from Moon","pass":rel in KENDRA}]
    if cfg.get("yoga",{}).get("gaja_kesari_require_jupiter_not_debilitated", True):
        conds.append({"cond":"Jupiter not debilitated (variant)","pass":c.dignity("Jupiter")!="debilitated"})
    return [_r("YOGA-GAJAKESARI","Gaja-Kesari Yoga",conds,["Jupiter","Moon"],[c.house("Jupiter"),c.house("Moon")])]

def viparita(c, cfg):
    names = {6:"Harsha",8:"Sarala",12:"Vimala"}; out=[]
    for h, nm in names.items():
        L = c.house_lord(h)
        out.append(_r(f"YOGA-VRY-{h}", f"{nm} Viparita Raja Yoga",
            [{"cond":f"Lord of {h}th ({L}) placed in 6th/8th/12th","pass":c.house(L) in DUSTHANA}],[L],[h,c.house(L)]))
    return out

def raja_and_yogakaraka(c, cfg):
    K = {h:c.house_lord(h) for h in (4,7,10)}; T = {h:c.house_lord(h) for h in (5,9)}
    out, seen = [], set()
    for p in GRAHAS7:
        lk = [h for h in K if K[h]==p]; lt = [h for h in T if T[h]==p]
        if lk and lt:
            out.append(_r(f"YOGA-YOGAKARAKA-{p.upper()}", f"Yogakaraka {p}",
              [{"cond":f"{p} lords kendra {lk} and trikona {lt}","pass":True}],[p],lk+lt))
    for hk, a in K.items():
        for ht, b in T.items():
            if a == b: continue
            key = tuple(sorted((a,b)))
            if key in seen: continue
            conj = c.sign(a)==c.sign(b)
            exch = c.sign(a) in [h for h in range(1,13) if SIGN_LORD[h]==b] and \
                   c.sign(b) in [h for h in range(1,13) if SIGN_LORD[h]==a]
            mut = c.aspects(a,b) and c.aspects(b,a)
            if conj or exch or mut:
                seen.add(key)
                rel = "conjunction" if conj else "sign exchange" if exch else "mutual aspect"
                out.append(_r(f"YOGA-RAJA-{key[0].upper()}-{key[1].upper()}","Raja-yoga combination",
                  [{"cond":f"Kendra lord {a} ({hk}th) and trikona lord {b} ({ht}th) linked by {rel}","pass":True}],
                  [a,b],[hk,ht]))
    return out

def neecha_bhanga(c, cfg):
    out=[]
    for p in GRAHAS7:
        if c.dignity(p)!="debilitated": continue
        disp = SIGN_LORD[c.sign(p)]; exl = SIGN_LORD[EXALT[p]]
        def kend(x): return c.house(x) in KENDRA or c.rel_house(x,"Moon") in KENDRA
        conds=[{"cond":f"{p} debilitated","pass":True},
               {"cond":f"Dispositor {disp} in kendra from Lagna or Moon","pass":kend(disp)},
               {"cond":f"Lord of {p}'s exaltation sign ({exl}) in kendra from Lagna or Moon","pass":kend(exl)}]
        ok = conds[0]["pass"] and (conds[1]["pass"] or conds[2]["pass"])  # mode 'any'
        out.append({"id":f"YOGA-NB-{p.upper()}","name":f"Neecha-bhanga candidate for {p}","conditions":conds,
                    "passed":ok,"planets":[p,disp,exl],"houses":[c.house(p)]})
    return out

DETECTORS=[pancha_mahapurusha,gaja_kesari,viparita,raja_and_yogakaraka,neecha_bhanga]
def detect_all(c, cfg):
    res=[]
    for d in DETECTORS: res+=d(c,cfg)
    return res
