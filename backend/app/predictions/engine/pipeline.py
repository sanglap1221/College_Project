"""Full Jyotish Prediction Pipeline implementing the 5-Stage Architecture.

Stage 1: Rule-based generation (RuleBook evaluation + Yoga detectors + Dasha timing).
Stage 2: Evidence construction (Relevance matching, group capping, independent count).
Stage 3: AI batch generation & compliance audit (in 1 generation + 1 audit call).
Stage 4: Grounding gate & code limit enforcement (40-70 word overview, <=18 word themes).
Stage 5: Final output (Structured prediction JSON + rich Markdown + validation audit).
"""

import datetime
import json
import logging
from typing import Any, Dict, List, Optional, Set

from .reference import TOPICS, HOUSE_DOMAIN, PLANET_KEYWORDS, ordinal, CANONICAL_TOPIC_ORDER
from .chart import Chart
from .rules import RuleBook, evaluate
from . import dasha as D
from . import evidence as E
from . import gate
from . import ai_service
from . import writer
from .planet_house_engine import generate_all_planetary_interpretations
from . import career_engine

logger = logging.getLogger("astro_app.predictions.pipeline")


def run_pipeline(
    chart_data: Dict[str, Any],
    topics: Optional[List[str]] = None,
    ref_date: Optional[str] = None,
    use_ai: bool = False,
    language: str = "en",
) -> Dict[str, Any]:
    """Execute the complete prediction pipeline on trusted chart facts."""
    rb = RuleBook()
    chart = Chart(chart_data, rb.cfg)

    if not ref_date:
        ref_date = datetime.date.today().isoformat()

    # Enforce canonical topic ordering across all charts & languages
    order_map = {t: i for i, t in enumerate(CANONICAL_TOPIC_ORDER)}
    requested_topics = sorted(
        [t for t in (topics if topics else CANONICAL_TOPIC_ORDER) if t in TOPICS],
        key=lambda x: order_map.get(x, 999)
    )

    # Stage 1: Evaluate deterministic rules & yogas
    items, yoga_trace = evaluate(chart, rb)

    # Dasha activations
    timing_all: List[Dict[str, Any]] = []
    if rb.cfg.get("enabled", {}).get("dasha") and chart.dashas:
        timing_all = D.evidence(chart, ref_date)
        items.extend(timing_all)

    # Active dasha info for quick display
    active_dashas = D.active(chart, ref_date)
    dasha_summary = [
        {
            "level": d.get("level"),
            "lord": d.get("lord"),
            "start": d.get("start"),
            "end": d.get("end"),
        }
        for d in active_dashas
    ]

    # Current dasha (MD + AD) for the reference date
    current = D.current_dasha(chart, ref_date)
    current_dasha_info = {
        "mahadasha": current["mahadasha"],
        "antardasha": current["antardasha"],
    }

    # Upcoming Antardasha periods (future windows)
    upcoming_ads = D.upcoming_antardashas(chart, ref_date, limit=12)

    report: Dict[str, Any] = {
        "chart_id": chart.id,
        "ruleset": {
            "id": rb.cfg.get("ruleset_id", "parashari_core_v2"),
            "version": rb.cfg.get("version", "2.0.0"),
            "house_system": rb.cfg.get("house_system", "whole_sign"),
            "ayanamsa": rb.cfg.get("ayanamsa", "traditional_lahiri"),
        },
        "reference_date": ref_date,
        "language": language,
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "data_issues": chart.issues,
        "data_notes": chart.notes,
        "sections": [],
        "yoga_trace": [y for y in yoga_trace if y.get("passed")],
        "all_yogas_checked": len(yoga_trace),
        "dasha_summary": dasha_summary,
        "current_dasha": current_dasha_info,
        "upcoming_antardashas": upcoming_ads,
        "planetary_interpretations": generate_all_planetary_interpretations(
            chart_obj=chart,
            dasha_summary=dasha_summary,
        ),
        "limitations": [
            "Vedic Jyotish interpretations are traditional, non-deterministic symbolic indications.",
            "Predictions are based on Parashari principles and do not replace legal, financial, or medical advice.",
            "Strict non-diagnostic health themes only. No fatalistic claims.",
        ],
    }

    ai_cfg = ai_service.get_ai_config()

    # Track evidence group usage across topics: max 2 uses per group
    group_usage: Dict[str, int] = {}
    topics_packages: Dict[str, Any] = {}

    # Stage 2: Aggregate evidence and generate baseline templated drafts
    for topic in requested_topics:
        if topic not in TOPICS:
            continue

        agg = E.aggregate(
            [i for i in items if i.get("kind") != "dasha"],
            topic,
            chart.issues,
            chart=chart,
            group_usage=group_usage,
        )
        timing_items = [e for e in E.relevant([i for i in items if i.get("kind") == "dasha"], topic, chart=chart)]

        clean_prose, used_items, section_data = writer.generate_topic_narrative(
            topic,
            agg,
            timing_items,
            chart_facts=chart.planets,
            chart=chart,
            max_items=rb.cfg.get("evidence", {}).get("max_items_per_side", 5),
            language=language,
        )

        # Omit empty sections with zero evidence groups
        if agg.get("counts", {}).get("independent_groups", 0) == 0:
            continue

        allowed_ids: Set[str] = {e["rule_id"] for e in used_items if "rule_id" in e}
        allowed_houses: Set[int] = {h for e in used_items for h in e.get("houses", [])}
        allowed_planets: Set[str] = {p for e in used_items for p in e.get("planets", [])}
        allowed_dates: Set[str] = {
            v
            for e in used_items
            if "timing" in e and isinstance(e["timing"], dict)
            for k, v in e["timing"].items()
            if k in ("start", "end")
        }

        topics_packages[topic] = {
            "title": TOPICS[topic]["title"],
            "agg": agg,
            "used_items": used_items,
            "timing_items": timing_items,
            "section_data": section_data,
            "allowed_ids": allowed_ids,
            "allowed_houses": allowed_houses,
            "allowed_planets": allowed_planets,
            "allowed_dates": allowed_dates,
            "timing_windows": D.event_timing_windows(chart, ref_date, topic),
        }

    # Stage 3 & 4: Optional Batched AI Generation & Audit
    ai_results: Dict[str, Dict[str, Any]] = {}
    ai_notes: List[str] = []

    if use_ai and ai_cfg["is_configured"]:
        try:
            ai_results, ai_notes = ai_service.ai_generate_and_audit_all_topics(
                topics_packages=topics_packages,
                dasha_summary=dasha_summary,
            )
        except Exception as exc:
            logger.warning(f"Batched AI generation failed: {exc}")
            ai_notes.append(f"AI review unavailable ({exc}); verified template used.")

    # Assemble final section outputs
    for topic in requested_topics:
        if topic not in topics_packages:
            continue

        pkg = topics_packages[topic]
        section_data = pkg["section_data"]
        allowed_ids = pkg["allowed_ids"]
        allowed_houses = pkg["allowed_houses"]
        allowed_planets = pkg["allowed_planets"]
        allowed_dates = pkg["allowed_dates"]

        status = "templated"
        notes: List[str] = []
        if ai_notes:
            notes.extend(ai_notes)

        # Check if AI produced valid topic output
        if topic in ai_results:
            ai_topic = ai_results[topic]
            test_text = (
                f"{ai_topic.get('overview', '')} "
                + " ".join(ai_topic.get("themes", []))
                + " "
                + " ".join(ai_topic.get("challenges", []))
            )

            gate_probs = gate.check(
                test_text,
                allowed_ids,
                allowed_houses,
                allowed_planets,
                allowed_dates,
                rb.forbidden,
            )

            if not gate_probs:
                # Apply AI output
                section_data["overview"] = ai_topic["overview"]
                section_data["themes"] = ai_topic["themes"]
                section_data["challenges"] = ai_topic["challenges"]
                section_data["basis_ids"] = ai_topic["basis_ids"]
                section_data["summary"] = ai_topic["overview"]
                section_data["prediction"] = ai_topic["overview"]
                status = "reviewed"
            else:
                notes.append("AI draft contained ungrounded claims; reverted to verified template.")
                status = "templated_fallback"
        elif use_ai:
            status = "templated_fallback"

        section_data["status"] = status
        section_data["notes"] = notes
        section_data["rule_ids"] = sorted(list(allowed_ids))
        section_data["timing_windows"] = pkg["timing_windows"]

        if topic == "career":
            try:
                c_analysis = career_engine.analyze_career_comprehensive(
                    chart_obj=chart,
                    client_dob=chart_data.get("dob"),
                    dasha_summary=dasha_summary,
                    language=language,
                )
                section_data["career_analysis"] = c_analysis
                if status != "reviewed" and c_analysis.get("overview", {}).get(language):
                    section_data["overview"] = c_analysis["overview"][language]
                    section_data["summary"] = c_analysis["overview"][language]
                    section_data["prediction"] = c_analysis["overview"][language]
                    for l_code in ("en", "bn", "hi"):
                        if l_code in section_data.get("translations", {}):
                            section_data["translations"][l_code]["overview"] = c_analysis["overview"].get(l_code, "")
                            section_data["translations"][l_code]["summary"] = c_analysis["overview"].get(l_code, "")
            except Exception as c_exc:
                logger.warning(f"Career comprehensive analysis failed: {c_exc}")

        report["sections"].append(section_data)

    return report
