"""Full Jyotish Prediction Pipeline implementing the 5-Stage Architecture.

Stage 1: Rule-based generation (RuleBook evaluation + Yoga detectors + Dasha timing).
Stage 2: Evidence construction (Grouping, deduplication, independent count, evidence level).
Stage 3: AI validation (Checks grounding against rulebook facts, flags deterministic bias).
Stage 4: Correction (AI rewrite strictly limited to supplied evidence or graceful fallback).
Stage 5: Final output (Structured prediction JSON + rich Markdown + validation audit).
"""

import datetime
import json
import logging
from typing import Any, Dict, List, Optional, Set

from .reference import TOPICS, HOUSE_DOMAIN, PLANET_KEYWORDS, ordinal
from .chart import Chart
from .rules import RuleBook, evaluate
from . import dasha as D
from . import evidence as E
from . import gate
from . import ai_service
from . import writer

logger = logging.getLogger("astro_app.predictions.pipeline")


def run_pipeline(
    chart_data: Dict[str, Any],
    topics: Optional[List[str]] = None,
    ref_date: Optional[str] = None,
    use_ai: bool = False,
) -> Dict[str, Any]:
    """Execute the complete prediction pipeline on trusted chart facts."""
    rb = RuleBook()
    chart = Chart(chart_data, rb.cfg)

    if not ref_date:
        ref_date = datetime.date.today().isoformat()

    requested_topics = topics if topics else list(TOPICS.keys())

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

    report: Dict[str, Any] = {
        "chart_id": chart.id,
        "ruleset": {
            "id": rb.cfg.get("ruleset_id", "parashari_core_v2"),
            "version": rb.cfg.get("version", "2.0.0"),
            "house_system": rb.cfg.get("house_system", "whole_sign"),
            "ayanamsa": rb.cfg.get("ayanamsa", "traditional_lahiri"),
        },
        "reference_date": ref_date,
        "language": "en",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "data_issues": chart.issues,
        "data_notes": chart.notes,
        "sections": [],
        "yoga_trace": [y for y in yoga_trace if y.get("passed")],
        "all_yogas_checked": len(yoga_trace),
        "dasha_summary": dasha_summary,
        "limitations": [
            "Vedic Jyotish interpretations are traditional, non-deterministic symbolic indications.",
            "Predictions are based on Parashari principles and do not replace legal, financial, or medical advice.",
            "Strict non-diagnostic health themes only. No fatalistic claims.",
        ],
    }

    ai_cfg = ai_service.get_ai_config()

    # Process each requested prediction topic
    for topic in requested_topics:
        if topic not in TOPICS:
            continue

        # Stage 2: Evidence Aggregation
        agg = E.aggregate([i for i in items if i.get("kind") != "dasha"], topic, chart.issues)
        timing_items = [e for e in E.relevant([i for i in items if i.get("kind") == "dasha"], topic)]

        # Generate Stage 1 / 2 narrative draft
        draft_markdown, used_items, section_data = writer.generate_topic_narrative(
            topic,
            agg,
            timing_items,
            chart_facts=chart.planets,
            max_items=rb.cfg.get("evidence", {}).get("max_items_per_side", 6),
        )

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

        # Check gate on baseline draft
        gate_problems = gate.check(
            draft_markdown,
            allowed_ids,
            allowed_houses,
            allowed_planets,
            allowed_dates,
            rb.forbidden,
        )

        final_text = draft_markdown
        status = "templated"
        notes: List[str] = []

        if gate_problems:
            notes.append("Baseline draft gate notices: " + "; ".join(gate_problems[:2]))

        # Stages 3 & 4: AI Validation and Review
        if use_ai and ai_cfg["is_configured"]:
            try:
                ai_parsed, ai_text, ai_notes = ai_service.ai_review_section(
                    topic,
                    TOPICS[topic]["title"],
                    used_items,
                    timing_items,
                    draft_markdown,
                )
                if ai_notes:
                    notes.extend(ai_notes)

                if ai_parsed and ai_text:
                    # Validate AI output with gate
                    ai_gate_probs = gate.check(
                        ai_text,
                        allowed_ids,
                        allowed_houses,
                        allowed_planets,
                        allowed_dates,
                        rb.forbidden,
                    )
                    if not ai_gate_probs:
                        final_text = ai_text
                        status = "reviewed"
                        # Enrich structured data with AI response fields
                        if "summary" in ai_parsed:
                            section_data["summary"] = ai_parsed["summary"]
                        if "supporting_factors" in ai_parsed and ai_parsed["supporting_factors"]:
                            section_data["supporting_factors"] = ai_parsed["supporting_factors"]
                        if "challenging_factors" in ai_parsed and ai_parsed["challenging_factors"]:
                            section_data["challenging_factors"] = ai_parsed["challenging_factors"]
                        if "validation" in ai_parsed:
                            section_data["validation"] = ai_parsed["validation"]
                    else:
                        notes.append("AI rewrite failed strict grounding gate; used verified rule draft.")
                        status = "templated_fallback"
                else:
                    status = "templated_fallback"
            except Exception as ex:
                logger.warning(f"Error during AI step for topic {topic}: {ex}")
                notes.append(f"AI review unavailable ({ex}); verified rulebook draft used.")
                status = "templated_fallback"
        elif use_ai:
            notes.append("AI API not configured; using verified rulebook draft.")
            status = "templated"

        section_data["prediction"] = final_text
        section_data["original_draft"] = draft_markdown
        section_data["status"] = status
        section_data["notes"] = notes
        section_data["rule_ids"] = sorted(allowed_ids)

        report["sections"].append(section_data)

    return report
