"""Prediction Service orchestrating chart calculation, rulebook execution,
AI validation pipeline, and MongoDB persistence.
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


def compute_chart_hash(input_data: Dict[str, Any]) -> str:
    """Generate a deterministic hash from birth input parameters to detect outdated predictions."""
    raw = f"{input_data.get('dob')}_{input_data.get('time')}_{input_data.get('place')}_{input_data.get('latitude')}_{input_data.get('longitude')}_{input_data.get('ayanamsa_mode')}"
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
        ayanamsa_mode=ayanamsa_mode,
        true_moon=True,
        true_node=True,
        planet_overrides=planet_overrides,
        override_moon_longitude=override_moon_longitude,
        override_ascendant_longitude=override_ascendant_longitude,
        birth_time_fold=birth_time_fold,
    )

    chart_facts: Dict[str, Any] = {
        "chart_id": report_id,
        "name": name,
        "lagna_sign": chart.lagna_sign_index + 1,  # 1-based (1-12)
        "lagna_degree": chart.lagna_degree,
        "rashi_sign": chart.rashi_sign_index + 1,
        "nakshatra": {
            "name": chart.nakshatra.name,
            "pada": chart.nakshatra.pada,
            "lord": chart.nakshatra.lord,
            "gana": chart.gana,
        },
        "planets": {},
        "dashas": [],
    }

    for p in chart.planets:
        chart_facts["planets"][p.name] = {
            "sign": p.sign_index + 1,  # 1-based
            "degree": p.degree_in_sign,
            "house": p.house,  # 1-based
            "retrograde": bool(p.is_retrograde and p.name not in ("Sun", "Moon", "Rahu", "Ketu")),
            "combust": bool(p.is_combust),
        }

    # Extract Vimshottari Mahadashas and Antardashas
    for md in chart.mahadasha_list:
        chart_facts["dashas"].append({
            "level": "MD",
            "lord": md.planet,
            "start": md.start_date.isoformat(),
            "end": md.end_date.isoformat(),
        })
        for ad in getattr(md, "antardashas", []):
            chart_facts["dashas"].append({
                "level": "AD",
                "lord": ad.planet,
                "start": ad.start_date.isoformat(),
                "end": ad.end_date.isoformat(),
            })

    hash_dict = {
        "dob": str(dob),
        "time": str(birth_time),
        "place": str(place),
        "latitude": loc.latitude,
        "longitude": loc.longitude,
        "ayanamsa_mode": ayanamsa_mode,
    }
    chart_hash = compute_chart_hash(hash_dict)

    return chart_facts, chart, chart_hash


def generate_prediction_report(
    report_id: str,
    payload: Any,
    use_ai: bool = False,
    topics: Optional[List[str]] = None,
    ref_date: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate a complete prediction report and persist it."""
    # Update AI config if user supplied specific overrides
    if provider or model:
        ai_service.update_runtime_ai_config(provider=provider, model=model)

    chart_facts, chart, chart_hash = prepare_chart_facts_from_input(payload)
    chart_facts["chart_id"] = report_id

    if not ref_date:
        ref_date = datetime.date.today().isoformat()

    # Run the 5-stage rulebook engine
    report = run_pipeline(
        chart_data=chart_facts,
        topics=topics,
        ref_date=ref_date,
        use_ai=use_ai,
    )

    report["report_id"] = report_id
    report["chart_hash"] = chart_hash
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

    # Record AI provider and model used
    ai_status = ai_service.get_ai_config()
    report["ai_meta"] = {
        "used_ai": use_ai and ai_status["is_configured"],
        "provider": ai_status["provider"] if (use_ai and ai_status["is_configured"]) else "none",
        "model": ai_status["model"] if (use_ai and ai_status["is_configured"]) else "rulebook_engine",
    }

    # Save to MongoDB
    save_prediction_record(report)

    return report


def get_prediction_by_id(report_id: str, current_hash: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve saved prediction and check whether it has become outdated."""
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
    """Regenerate a single topic section while strictly preserving all other sections and manual edits."""
    doc = get_prediction_record(report_id)
    if not doc and payload:
        # If not saved yet, generate full
        return generate_prediction_report(report_id, payload, use_ai=use_ai, topics=[topic], provider=provider, model=model)

    if not doc:
        raise ValueError(f"Prediction report '{report_id}' not found.")

    if provider or model:
        ai_service.update_runtime_ai_config(provider=provider, model=model)

    # Re-calculate chart facts
    if payload:
        chart_facts, _, _ = prepare_chart_facts_from_input(payload)
    else:
        # Re-derive from customer stored in doc if possible
        cust = doc.get("customer", {})
        chart_facts, _, _ = prepare_chart_facts_from_input({
            "name": cust.get("name", "Client"),
            "dob": cust.get("dob", "2000-01-01"),
            "time": cust.get("time", "12:00"),
            "place": cust.get("place", "Kolkata"),
            "report_id": report_id,
        })

    chart_facts["chart_id"] = report_id
    ref_date = doc.get("reference_date", datetime.date.today().isoformat())

    # Generate only the targeted topic
    sub_report = run_pipeline(
        chart_data=chart_facts,
        topics=[topic],
        ref_date=ref_date,
        use_ai=use_ai,
    )

    if not sub_report.get("sections"):
        raise RuntimeError(f"Engine failed to generate section '{topic}'")

    new_section = sub_report["sections"][0]

    # Replace section in doc
    sections = doc.get("sections", [])
    found = False
    for i, sec in enumerate(sections):
        if sec.get("topic") == topic:
            sections[i] = new_section
            found = True
            break

    if not found:
        sections.append(new_section)

    doc["sections"] = sections
    doc["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # Update DB
    save_prediction_record(doc)

    return doc


def save_manual_edit(report_id: str, topic: str, content: str) -> bool:
    """Save manual text edits made by the astrologer."""
    return update_prediction_section_record(report_id, topic, content, is_manual=True)
