"""Prediction Service orchestrating chart calculation, rulebook execution,
AI validation pipeline, caching, and persistence.
"""

import datetime
import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from app.astrology.calculations import (
    calculate_chart,
    resolve_location,
    ZODIAC_SIGNS_BN,
    format_sign_compact_bn,
)
from app.db import (
    save_prediction_record,
    get_prediction_record,
    update_prediction_section_record,
)
from .engine.pipeline import run_pipeline
from .engine.reference import TOPICS, HOUSE_DOMAIN, PLANET_KEYWORDS, ordinal
from .engine import ai_service

logger = logging.getLogger("astro_app.predictions.service")

# In-memory prediction cache keyed by chart_hash + ruleset_version
_PREDICTION_REPORT_CACHE: Dict[str, Dict[str, Any]] = {}

CORE_LIFE_TOPICS = [
    "career",
    "finance",
    "marriage",
    "health",
    "education",
    "spirituality",
    "family_home",
    "travel",
]


def compute_chart_hash(input_data: Dict[str, Any]) -> str:
    """Generate a deterministic hash from birth input parameters to detect outdated predictions."""
    raw = (
        f"{input_data.get('dob')}_{input_data.get('time')}_{input_data.get('place')}_"
        f"{input_data.get('latitude')}_{input_data.get('longitude')}_{input_data.get('ayanamsa_mode')}"
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _clean_float(val: Any) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    val_str = str(val).strip()
    if not val_str:
        return None
    try:
        return float(val_str)
    except (ValueError, TypeError):
        return None


def prepare_chart_facts_from_input(payload: Any) -> Tuple[Dict[str, Any], Any, str]:
    """Calculate the chart using the existing calculation engine and extract Jyotish Rulebook input facts."""
    if isinstance(payload, dict):
        place = payload.get("place", "Kolkata")
        lat = _clean_float(payload.get("latitude"))
        lon = _clean_float(payload.get("longitude"))
        tz = payload.get("timezone")
        dob = payload.get("dob")
        if isinstance(dob, str):
            dob = datetime.date.fromisoformat(dob)
        birth_time = payload.get("time")
        if isinstance(birth_time, str):
            birth_time = datetime.time.fromisoformat(birth_time)
        raw_overrides = payload.get("planet_overrides")
        override_moon_longitude = _clean_float(payload.get("override_moon_longitude"))
        override_ascendant_longitude = _clean_float(payload.get("override_ascendant_longitude"))
        name = payload.get("name", "Client")
        report_id = payload.get("report_id", "chart-unknown")
        ayanamsa_mode = payload.get("ayanamsa_mode", "traditional")
        birth_time_fold = payload.get("birth_time_fold")
    else:
        place = payload.place
        lat = _clean_float(getattr(payload, "latitude", None))
        lon = _clean_float(getattr(payload, "longitude", None))
        tz = getattr(payload, "timezone", None)
        dob = payload.dob
        if isinstance(dob, str):
            dob = datetime.date.fromisoformat(dob)
        birth_time = getattr(payload, "time", None)
        if isinstance(birth_time, str):
            birth_time = datetime.time.fromisoformat(birth_time)
        raw_overrides = getattr(payload, "planet_overrides", None)
        override_moon_longitude = _clean_float(getattr(payload, "override_moon_longitude", None))
        override_ascendant_longitude = _clean_float(getattr(payload, "override_ascendant_longitude", None))
        name = getattr(payload, "name", "Client")
        report_id = getattr(payload, "report_id", "chart-unknown")
        ayanamsa_mode = getattr(payload, "ayanamsa_mode", "traditional")
        birth_time_fold = getattr(payload, "birth_time_fold", None)

    planet_overrides = None
    if isinstance(raw_overrides, dict):
        planet_overrides = {k: _clean_float(v) for k, v in raw_overrides.items() if _clean_float(v) is not None}

    loc = resolve_location(place, lat, lon, tz)

    chart = calculate_chart(
        dob=dob,
        birth_time=birth_time,
        place=place,
        latitude=loc.latitude,
        longitude=loc.longitude,
        timezone=loc.timezone,
        planet_overrides=planet_overrides,
        override_moon_longitude=override_moon_longitude,
        override_ascendant_longitude=override_ascendant_longitude,
        ayanamsa_mode=ayanamsa_mode,
        birth_time_fold=birth_time_fold,
    )

    chart_input = {
        "dob": str(dob),
        "time": str(birth_time),
        "place": place,
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "ayanamsa_mode": ayanamsa_mode,
    }
    chart_hash = compute_chart_hash(chart_input)

    # Format chart facts strictly adhering to Jyotish Rulebook JSON input specification
    planets_dict = {}
    for p in chart.planets:
        p_name = getattr(p, "name_en", getattr(p, "name", ""))
        if p_name == "Ketu":
            degree = None
        else:
            degree = round(p.longitude % 30.0, 4)

        planets_dict[p_name] = {
            "sign": p.sign_index + 1,
            "house": p.house,
            "degree": degree,
            "retrograde": bool(p.is_retrograde),
            "combust": bool(p.is_combust),
        }

    # Extract Vimshottari dasha periods
    dashas_list = []
    if hasattr(chart, "dashas") and chart.dashas:
        for md in chart.dashas:
            md_lord = getattr(md, "lord_en", getattr(md, "planet", ""))
            md_start = str(md.start_date)
            md_end = str(md.end_date)
            dashas_list.append({
                "level": "mahadasha",
                "lord": md_lord,
                "start": md_start,
                "end": md_end,
            })
            if hasattr(md, "antardashas") and md.antardashas:
                for ad in md.antardashas:
                    ad_lord = getattr(ad, "lord_en", getattr(ad, "planet", ""))
                    ad_start = str(ad.start_date)
                    ad_end = str(ad.end_date)
                    dashas_list.append({
                        "level": "antardasha",
                        "lord": ad_lord,
                        "start": ad_start,
                        "end": ad_end,
                    })

    chart_facts = {
        "chart_id": report_id,
        "lagna_sign": chart.lagna_sign_index + 1,
        "planets": planets_dict,
        "dashas": dashas_list,
    }

    return chart_facts, chart, chart_hash


def generate_prediction_report(
    report_id: str,
    payload: Any,
    use_ai: bool = False,
    topics: Optional[List[str]] = None,
    ref_date: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    force_regenerate: bool = False,
    include_technical_appendix: bool = False,
) -> Dict[str, Any]:
    """Generate a complete prediction report with caching per chart_hash + ruleset_version."""
    if provider or model:
        ai_service.update_runtime_ai_config(provider=provider, model=model)

    chart_facts, chart, chart_hash = prepare_chart_facts_from_input(payload)
    chart_facts["chart_id"] = report_id

    ruleset_version = "2.0.0"
    cache_key = f"{chart_hash}_{ruleset_version}_{use_ai}_{provider}_{model}_{include_technical_appendix}"

    if not force_regenerate and cache_key in _PREDICTION_REPORT_CACHE:
        logger.info(f"Returning cached prediction report for cache key: {cache_key}")
        cached_rep = dict(_PREDICTION_REPORT_CACHE[cache_key])
        cached_rep["report_id"] = report_id
        return cached_rep

    if not ref_date:
        ref_date = datetime.date.today().isoformat()

    # Default to 8 core life topics if topics not explicitly provided
    requested_topics = topics if topics else CORE_LIFE_TOPICS

    # Run the 5-stage rulebook engine
    report = run_pipeline(
        chart_data=chart_facts,
        topics=requested_topics,
        ref_date=ref_date,
        use_ai=use_ai,
    )

    report["report_id"] = report_id
    report["chart_hash"] = chart_hash
    report["include_technical_appendix"] = include_technical_appendix
    report["customer"] = {
        "name": getattr(payload, "name", "") if not isinstance(payload, dict) else payload.get("name", ""),
        "dob": str(getattr(payload, "dob", "")) if not isinstance(payload, dict) else str(payload.get("dob", "")),
        "time": str(getattr(payload, "time", "")) if not isinstance(payload, dict) else str(payload.get("time", "")),
        "place": getattr(payload, "place", "") if not isinstance(payload, dict) else payload.get("place", ""),
    }
    report["chart_overview"] = {
        "lagna_sign_name": chart.lagna_sign,
        "lagna_sign_index": chart.lagna_sign_index,
        "lagna_degree": chart.lagna_degree,
        "rashi_sign_name": chart.rashi_sign,
        "rashi_sign_index": chart.rashi_sign_index,
        "nakshatra_name": chart.nakshatra.name,
        "nakshatra_pada": chart.nakshatra.pada,
        "nakshatra_lord": chart.nakshatra.lord,
        "ayanamsa": chart.ayanamsa,
        "gana": chart.gana,
        "varna": chart.varna,
    }

    # Generate an executive overview <= 120 words
    overview_sentences = [
        f"This natal chart analysis is established with {chart.lagna_sign} Lagna and {chart.rashi_sign} Moon.",
        "Planetary placements show purposeful vitality across foundational life areas.",
        "Parashari rules highlight steady development when personal initiative is aligned with disciplined ethical conduct.",
        "Current planetary periods indicate a pivotal chapter for consolidating skills and expanding professional agency."
    ]
    report["executive_overview"] = " ".join(overview_sentences)

    ai_status = ai_service.get_ai_config()
    report["ai_meta"] = {
        "used_ai": use_ai and ai_status["is_configured"],
        "provider": ai_status["provider"] if (use_ai and ai_status["is_configured"]) else "none",
        "model": ai_status["model"] if (use_ai and ai_status["is_configured"]) else "rulebook_engine",
    }

    # Cache report
    _PREDICTION_REPORT_CACHE[cache_key] = report

    # Save to MongoDB
    save_prediction_record(report)

    return report


def get_prediction_by_id(report_id: str, current_hash: Optional[str] = None) -> Optional[Dict[str, Any]]:
    doc = get_prediction_record(report_id)
    if not doc:
        return None

    if current_hash and doc.get("chart_hash"):
        doc["is_outdated"] = (doc.get("chart_hash") != current_hash)
    else:
        doc["is_outdated"] = False

    return doc


def regenerate_prediction_section(
    report_id: str,
    topic: str,
    use_ai: bool = False,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    payload: Optional[Any] = None,
) -> Dict[str, Any]:
    doc = get_prediction_record(report_id)
    if not doc and payload:
        return generate_prediction_report(
            report_id, payload, use_ai=use_ai, topics=[topic], provider=provider, model=model, force_regenerate=True
        )

    if not doc:
        raise ValueError(f"Prediction report '{report_id}' not found.")

    if provider or model:
        ai_service.update_runtime_ai_config(provider=provider, model=model)

    if payload:
        chart_facts, _, _ = prepare_chart_facts_from_input(payload)
    else:
        chart_facts = {
            "chart_id": report_id,
            "lagna_sign": doc["chart_overview"]["lagna_sign_index"] + 1,
            "planets": {},
            "dashas": [],
        }

    single_report = run_pipeline(
        chart_data=chart_facts,
        topics=[topic],
        ref_date=doc.get("reference_date"),
        use_ai=use_ai,
    )

    if not single_report["sections"]:
        raise ValueError(f"Failed to generate section for topic '{topic}'.")

    updated_section = single_report["sections"][0]
    replaced = False
    for idx, s in enumerate(doc.get("sections", [])):
        if s.get("topic") == topic:
            doc["sections"][idx] = updated_section
            replaced = True
            break

    if not replaced:
        doc.setdefault("sections", []).append(updated_section)

    save_prediction_record(doc)
    return doc


def save_manual_edit(report_id: str, topic: str, content: str) -> bool:
    success = update_prediction_section_record(report_id, topic, content)
    if success:
        # Invalidate in-memory cache
        for k in list(_PREDICTION_REPORT_CACHE.keys()):
            _PREDICTION_REPORT_CACHE.pop(k, None)
    return success
