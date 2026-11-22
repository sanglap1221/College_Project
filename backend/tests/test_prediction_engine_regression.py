"""Regression Test Suite for Jyotish Prediction Engine.
Validates:
1. Lord mapping on test fixture (Lagna Dhanu).
2. Natural friendship labels (with pending_astrologer_review status).
3. Header lords match topic-relevant lords.
4. Evidence group capping (no group in > 2 topics).
5. No empty sections.
6. No raw lists (`[]`, `[8]`) in narratives.
7. EN and BN evidence levels and counts identical (single source of truth).
8. Forbidden-claims scan (no lifespan, no "আয়ু বিচার", no 100% certainty).
9. Timeline contains no unsupported event labels or age buckets.
"""

import pytest
import re
from typing import Any, Dict

from app.predictions.engine.chart import Chart
from app.predictions.engine.rules import RuleBook
from app.predictions.engine.pipeline import run_pipeline
from app.predictions.engine.reference import (
    TOPIC_PRIMARY_HOUSE,
    get_natural_friendship,
    SIGNS,
)

FIXTURE_CHART_FACTS = {
    "chart_id": "regression_fixture_dhanu",
    "lagna_sign": 9,  # Sagittarius / Dhanu
    "planets": {
        "Sun": {"sign": 4, "house": 8, "degree": 15.0},      # Cancer (8th)
        "Moon": {"sign": 3, "house": 7, "degree": 12.0},     # Gemini (7th)
        "Mars": {"sign": 5, "house": 9, "degree": 10.0},     # Leo (9th)
        "Mercury": {"sign": 5, "house": 9, "degree": 14.0},  # Leo (9th)
        "Jupiter": {"sign": 5, "house": 9, "degree": 18.0},  # Leo (9th)
        "Venus": {"sign": 3, "house": 7, "degree": 20.0},    # Gemini (7th)
        "Saturn": {"sign": 3, "house": 7, "degree": 25.0},   # Gemini (7th)
        "Rahu": {"sign": 1, "house": 5, "degree": 5.0},      # Aries (5th)
        "Ketu": {"sign": 7, "house": 11, "degree": 5.0},     # Libra (11th)
    },
    "dashas": [
        {"level": "mahadasha", "lord": "Saturn", "start": "2015-01-01", "end": "2034-01-01"},
        {"level": "antardasha", "lord": "Rahu", "start": "2024-01-01", "end": "2026-11-01"},
        {"level": "antardasha", "lord": "Jupiter", "start": "2026-11-01", "end": "2029-05-01"},
        {"level": "antardasha", "lord": "Saturn", "start": "2029-05-01", "end": "2032-05-01"},
    ],
    "dob": "1995-08-01",
}


@pytest.fixture
def test_chart() -> Chart:
    rb = RuleBook()
    return Chart(FIXTURE_CHART_FACTS, rb.cfg)


def test_1_lord_mapping_on_test_fixture(test_chart: Chart):
    """Test 1: Verify exact house lord mapping for Dhanu Lagna fixture."""
    assert test_chart.lagna == 9
    assert test_chart.lorded("Jupiter") == [1, 4]
    assert test_chart.lorded("Saturn") == [2, 3]
    assert test_chart.lorded("Mars") == [5, 12]
    assert test_chart.lorded("Venus") == [6, 11]
    assert test_chart.lorded("Mercury") == [7, 10]
    assert test_chart.lorded("Moon") == [8]
    assert test_chart.lorded("Sun") == [9]
    assert test_chart.lorded("Rahu") == []
    assert test_chart.lorded("Ketu") == []


def test_2_natural_friendship_labels():
    """Test 2: Natural friendship labels and pending_astrologer_review status."""
    rel = get_natural_friendship("Saturn", "Mercury")
    assert rel["relationship"] == "friend"
    assert rel["status"] == "pending_astrologer_review"

    rel2 = get_natural_friendship("Sun", "Saturn")
    assert rel2["relationship"] == "enemy"
    assert rel2["status"] == "pending_astrologer_review"

    rel3 = get_natural_friendship("Jupiter", "Saturn")
    assert rel3["relationship"] == "neutral"
    assert rel3["status"] == "pending_astrologer_review"


def test_3_header_lords_match_topic_relevant_lords(test_chart: Chart):
    """Test 3: Topic headers must use topic-relevant lord."""
    rep = run_pipeline(FIXTURE_CHART_FACTS, language="en")
    for sec in rep["sections"]:
        topic = sec["topic"]
        h_pri = TOPIC_PRIMARY_HOUSE.get(topic)
        if not h_pri:
            continue
        expected_lord = test_chart.house_lord(h_pri)
        hdr = sec.get("header_lord", {})
        assert hdr.get("lord") == expected_lord, f"Topic {topic} lord {hdr.get('lord')} != {expected_lord}"
        assert hdr.get("house") == h_pri


def test_4_evidence_group_capping(test_chart: Chart):
    """Test 4: Evidence group capping - no group appears in > 2 topics."""
    rep = run_pipeline(FIXTURE_CHART_FACTS, language="en")
    group_topics: Dict[str, set] = {}
    for sec in rep["sections"]:
        topic = sec["topic"]
        for sf in sec.get("supporting_factors", []) + sec.get("challenging_factors", []):
            grp = sf.get("factor")
            if grp:
                group_topics.setdefault(grp, set()).add(topic)

    # Across all topics, one evidence group may appear in at most 2 topics
    for grp, topics in group_topics.items():
        assert len(topics) <= 2, f"Group '{grp}' appeared in {len(topics)} topics (> 2 topics): {topics}"


def test_5_no_empty_sections():
    """Test 5: No empty sections emitted in report."""
    rep = run_pipeline(FIXTURE_CHART_FACTS, language="en")
    assert len(rep["sections"]) > 0
    for sec in rep["sections"]:
        counts = sec.get("counts", {})
        n = counts.get("independent_groups", 0)
        assert n > 0, f"Section {sec.get('topic')} has 0 independent groups"
        assert len(sec.get("basis_ids", [])) > 0, f"Section {sec.get('topic')} has empty basis_ids"


def test_6_no_raw_lists_in_narratives():
    """Test 6: No raw Python lists like `[]` or `[8]` appear in narratives."""
    for lang in ("en", "bn", "hi"):
        rep = run_pipeline(FIXTURE_CHART_FACTS, language=lang)
        for sec in rep["sections"]:
            text_to_scan = (
                sec.get("overview", "")
                + " " + sec.get("summary", "")
                + " " + " ".join(sec.get("themes", []))
                + " " + " ".join(sec.get("challenges", []))
            )
            raw_list_pattern = re.compile(r"\[\s*\d*(?:,\s*\d+)*\s*\]")
            # Filter out evidence rule citations like [HL-H10-IN-H09]
            matches = [m for m in raw_list_pattern.findall(text_to_scan) if not any(tag in m for tag in ("HL", "PH", "DG", "YOGA", "FACT", "NATAL"))]
            assert not matches, f"Raw list found in {sec.get('topic')} ({lang}): {matches}"

            if sec.get("career_analysis"):
                ca = sec["career_analysis"]
                ca_text = str(ca.get("timeline", [])) + str(ca.get("placement_cards", []))
                # Check that timeline explanations don't contain raw `ruling []` or `অধিপতি: []`
                assert "ruling []" not in ca_text
                assert "অধিপতি: []" not in ca_text


def test_7_en_and_bn_evidence_levels_and_counts_identical():
    """Test 7: Single source of truth - EN and BN evidence levels, counts, and basis IDs must match 100%."""
    rep_en = run_pipeline(FIXTURE_CHART_FACTS, language="en")
    rep_bn = run_pipeline(FIXTURE_CHART_FACTS, language="bn")

    sec_en = {s["topic"]: s for s in rep_en["sections"]}
    sec_bn = {s["topic"]: s for s in rep_bn["sections"]}

    assert set(sec_en.keys()) == set(sec_bn.keys()), "Topic set mismatch between EN and BN"

    for topic in sec_en:
        en_item = sec_en[topic]
        bn_item = sec_bn[topic]

        assert en_item["evidence_level"] == bn_item["evidence_level"], (
            f"Evidence level mismatch for {topic}: EN={en_item['evidence_level']}, BN={bn_item['evidence_level']}"
        )
        assert en_item["counts"] == bn_item["counts"], (
            f"Counts mismatch for {topic}: EN={en_item['counts']}, BN={bn_item['counts']}"
        )
        assert en_item["basis_ids"] == bn_item["basis_ids"], (
            f"Basis IDs mismatch for {topic}: EN={en_item['basis_ids']}, BN={bn_item['basis_ids']}"
        )


def test_8_forbidden_claims_scan():
    """Test 8: Strict compliance scan - no lifespan prediction, no 'আয়ু বিচার', no 100% certainty."""
    for lang in ("en", "bn", "hi"):
        rep = run_pipeline(FIXTURE_CHART_FACTS, language=lang)
        full_dump = str(rep)

        assert "আয়ু বিচার" not in full_dump, "Found forbidden phrase 'আয়ু বিচার'"
        assert "lifespan" not in full_dump.lower(), "Found forbidden word 'lifespan'"
        assert "100% certainty" not in full_dump.lower()
        assert "guaranteed outcome" not in full_dump.lower()


def test_9_timeline_unsupported_labels():
    """Test 9: Timeline contains no speculative event labels or age buckets."""
    rep = run_pipeline(FIXTURE_CHART_FACTS, language="en")
    career_sec = next((s for s in rep["sections"] if s.get("topic") == "career"), None)
    assert career_sec is not None
    assert "career_analysis" in career_sec

    timeline = career_sec["career_analysis"].get("timeline", [])
    assert len(timeline) <= 4, "Timeline should only have past + current + next 2 changes"

    forbidden_labels = [
        "First Job",
        "Promotion",
        "Business Start",
        "Major Career Milestone",
        "Career Entry & Foundation Building",
        "Job Transition",
    ]

    for item in timeline:
        event_str = str(item.get("event", {}))
        for fl in forbidden_labels:
            assert fl.lower() not in event_str.lower(), f"Speculative label '{fl}' found in timeline: {event_str}"
        assert "age_range" not in item, "Age bucket found in timeline item"
        assert "md_houses_ruled" in item or item.get("period_type") == "past"
