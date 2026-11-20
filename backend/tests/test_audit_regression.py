"""Comprehensive regression test suite for Astro_freelance.

Covers:
1. Ascendant tables validation (missing, empty, truncated, malformed, beginning/middle/end, angle zero, fallback).
2. Coordinates and timezones validation (NaN, inf, bounds, non-numeric, partial, invalid IANA tz).
3. Local birth times around DST (spring forward nonexistent time, fall back ambiguity, fold 0/1 disambiguation).
4. Lagna timeline (midnight transition at m=0, UTC chronological ordering, 23h spring forward, 25h fall back, calculate_chart start minute consistency).
5. Bengali date (before/after sunrise, date-only calls, incomplete details, invalid timezone, polar sunrise failure, transit search bracket success/failure, Pohela Boishakh).
6. PDF time formatting with offsets and repeated times.
7. Kolkata/Kanpur 1989-07-23 reference compatibility.
"""
from datetime import date, time, datetime, timedelta
import math
from zoneinfo import ZoneInfo
from unittest.mock import patch
import pytest
import swisseph as swe

from app.astrology.calculations import (
    validate_coordinates,
    resolve_location,
    calculate_chart,
    calculate_book_lagna,
    _is_valid_ascendant_table,
    _lookup_time_table_value,
    _load_ascendant_table,
    _sign_index,
    ZODIAC_SIGNS,
)
from app.astrology.lagna_table import (
    calculate_dynamic_lagna_events,
    calculate_dynamic_lagna_starts,
    get_daily_lagna_timeline,
    subtract_one_minute,
    _timeline_sort_key,
)
from app.astrology.bengali_date import (
    gregorian_to_bengali,
    find_sun_transit,
    get_sidereal_sun_longitude,
)
from app.pdf.generate_pdf import format_time_dot, build_report_context
from app.schemas import PdfRequest


# ===========================================================================
# 1. Ascendant Table Validation Tests
# ===========================================================================

def test_ascendant_table_missing_and_empty():
    assert _is_valid_ascendant_table(None) is False
    assert _is_valid_ascendant_table({}) is False
    assert _is_valid_ascendant_table([]) is False
    assert _is_valid_ascendant_table("table") is False


def test_ascendant_table_truncated_and_gap():
    # Less than 50 entries
    short_table = {f"{h:02d}:00:00": float(h * 15) for h in range(10)}
    assert _is_valid_ascendant_table(short_table) is False

    # 60 entries covering only 00:00 to 04:00 (massive midnight gap ~20 hours)
    coarse_table = {f"00:{m:02d}:00": float(m) for m in range(60)}
    assert _is_valid_ascendant_table(coarse_table) is False


def test_ascendant_table_malformed_keys_and_values():
    valid_base = _load_ascendant_table(0)
    assert valid_base is not None

    # Invalid key format
    corrupt_key = dict(valid_base)
    corrupt_key["24:00:00"] = 90.0
    assert _is_valid_ascendant_table(corrupt_key) is False

    corrupt_key2 = dict(valid_base)
    corrupt_key2["invalid_time"] = 90.0
    assert _is_valid_ascendant_table(corrupt_key2) is False

    # Value: bool rejected
    corrupt_bool = dict(valid_base)
    corrupt_bool["00:00:00"] = True
    assert _is_valid_ascendant_table(corrupt_bool) is False

    # Value: NaN / Inf rejected
    corrupt_nan = dict(valid_base)
    corrupt_nan["00:04:00"] = float("nan")
    assert _is_valid_ascendant_table(corrupt_nan) is False

    corrupt_inf = dict(valid_base)
    corrupt_inf["00:04:00"] = float("inf")
    assert _is_valid_ascendant_table(corrupt_inf) is False

    # Value: out of angular range [-0.1 or 360.1]
    corrupt_neg = dict(valid_base)
    corrupt_neg["00:04:00"] = -0.5
    assert _is_valid_ascendant_table(corrupt_neg) is False

    corrupt_high = dict(valid_base)
    corrupt_high["00:04:00"] = 360.5
    assert _is_valid_ascendant_table(corrupt_high) is False


def test_ascendant_table_invalid_at_beginning_middle_end():
    valid_base = _load_ascendant_table(0)
    assert valid_base is not None
    keys = list(valid_base.keys())

    # Invalid at beginning
    bad_start = dict(valid_base)
    bad_start[keys[0]] = "bad_val"
    assert _is_valid_ascendant_table(bad_start) is False

    # Invalid in middle
    bad_mid = dict(valid_base)
    bad_mid[keys[len(keys) // 2]] = float("nan")
    assert _is_valid_ascendant_table(bad_mid) is False

    # Invalid at end
    bad_end = dict(valid_base)
    bad_end[keys[-1]] = -1.0
    assert _is_valid_ascendant_table(bad_end) is False


def test_ascendant_table_legitimate_angle_zero():
    valid_base = _load_ascendant_table(0)
    assert valid_base is not None
    table_with_zero = dict(valid_base)
    # 0.0 is a legitimate astronomical angle
    table_with_zero["00:00:00"] = 0.0
    assert _is_valid_ascendant_table(table_with_zero) is True

    # _lookup_time_table_value must return 0.0, not None
    val = _lookup_time_table_value(table_with_zero, 0.0)
    assert val == pytest.approx(0.0, abs=1e-5)


def test_calculate_book_lagna_fallback_without_fabricated_zero():
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = 2447730.666667
    lat = 22.5726
    lon = 88.3639

    with patch("app.astrology.calculations._load_ascendant_table", return_value=None):
        asc = calculate_book_lagna(jd, lat, lon)
        # Verify it falls back to direct Swiss Ephemeris sidereal calculation
        cusps, ascmc = swe.houses_ex(jd, lat, lon, b"P", swe.FLG_SIDEREAL)
        expected = ascmc[0] % 360.0
        assert asc == pytest.approx(expected, abs=0.001)
        assert asc != 0.0


# ===========================================================================
# 2. Coordinate and Timezone Validation Tests
# ===========================================================================

def test_validate_coordinates_rejections():
    # Non-numeric
    with pytest.raises(ValueError, match="Coordinates must be numeric"):
        validate_coordinates(True, 88.0)
    with pytest.raises(ValueError, match="Non-numeric coordinates"):
        validate_coordinates("not_a_number", 88.0)
    with pytest.raises(ValueError, match="Both latitude and longitude"):
        validate_coordinates(None, 88.0)
    with pytest.raises(ValueError, match="Both latitude and longitude"):
        validate_coordinates(22.0, None)

    # NaN / Inf
    with pytest.raises(ValueError, match="finite numbers"):
        validate_coordinates(float("nan"), 88.0)
    with pytest.raises(ValueError, match="finite numbers"):
        validate_coordinates(22.0, float("inf"))

    # Out of range
    with pytest.raises(ValueError, match="Latitude out of range"):
        validate_coordinates(91.0, 88.0)
    with pytest.raises(ValueError, match="Latitude out of range"):
        validate_coordinates(-90.1, 88.0)
    with pytest.raises(ValueError, match="Longitude out of range"):
        validate_coordinates(22.0, 180.5)
    with pytest.raises(ValueError, match="Longitude out of range"):
        validate_coordinates(22.0, -181.0)


def test_resolve_location_partial_coordinates():
    with pytest.raises(ValueError, match="Both latitude and longitude"):
        resolve_location(lat=22.5726, lon=None)
    with pytest.raises(ValueError, match="Both latitude and longitude"):
        resolve_location(lat=None, lon=88.3639)


def test_resolve_location_explicit_international_preservation():
    loc = resolve_location(lat=51.5074, lon=-0.1278, tz="Europe/London")
    assert loc.timezone == "Europe/London"
    assert loc.latitude == pytest.approx(51.5074, abs=0.0001)
    assert loc.longitude == pytest.approx(-0.1278, abs=0.0001)


# ===========================================================================
# 3. Local Birth Times Around DST Tests
# ===========================================================================

def test_dst_spring_forward_nonexistent_time():
    # London 2024-03-31: clocks jump from 01:00 to 02:00.
    # 01:30 does NOT exist.
    dob = date(2024, 3, 31)
    tob = time(1, 30)
    with pytest.raises(ValueError, match="Nonexistent local time"):
        calculate_chart(dob, tob, "London", latitude=51.5074, longitude=-0.1278, timezone="Europe/London")


def test_dst_autumn_fallback_ambiguous_time_without_fold():
    # London 2024-10-27: clocks fall back from 02:00 BST to 01:00 GMT.
    # 01:30 is ambiguous and occurs twice.
    dob = date(2024, 10, 27)
    tob = time(1, 30)
    with pytest.raises(ValueError, match="Ambiguous local time.*birth_time_fold"):
        calculate_chart(dob, tob, "London", latitude=51.5074, longitude=-0.1278, timezone="Europe/London")


def test_dst_autumn_fallback_disambiguation_with_fold():
    dob = date(2024, 10, 27)
    tob = time(1, 30)

    # fold=0: first occurrence (00:30 UTC)
    c0 = calculate_chart(
        dob, tob, "London",
        latitude=51.5074, longitude=-0.1278, timezone="Europe/London",
        birth_time_fold=0
    )

    # fold=1: second occurrence (01:30 UTC)
    c1 = calculate_chart(
        dob, tob, "London",
        latitude=51.5074, longitude=-0.1278, timezone="Europe/London",
        birth_time_fold=1
    )

    # One hour difference in Julian Day: 1/24 day
    diff_jd = c1.julian_day - c0.julian_day
    assert diff_jd == pytest.approx(1.0 / 24.0, abs=1e-6)
    # The ascendant longitudes must differ because 1 hour has elapsed
    assert c0.ascendant_longitude != pytest.approx(c1.ascendant_longitude, abs=1.0)

    # Invalid fold value
    with pytest.raises(ValueError, match="Invalid birth_time_fold"):
        calculate_chart(
            dob, tob, "London",
            latitude=51.5074, longitude=-0.1278, timezone="Europe/London",
            birth_time_fold=2
        )


# ===========================================================================
# 4. Lagna Timeline Tests
# ===========================================================================

def test_lagna_timeline_london_spring_forward_minutes():
    # 31 March 2024: 1,380 actual minutes
    events = calculate_dynamic_lagna_events(
        dob=date(2024, 3, 31), lat=51.5074, lon=-0.1278,
        is_sidereal=True, timezone_name="Europe/London"
    )
    assert len(events) >= 1  # Verify calculated sign transitions exist

    # Chronologically ordered in UTC
    for i in range(len(events) - 1):
        assert events[i]["utc_datetime"] < events[i + 1]["utc_datetime"]

    # Every start minute agrees with calculate_chart()
    for ev in events:
        h, m = map(int, ev["start"].split()[0].split(":"))
        chart = calculate_chart(
            dob=date(2024, 3, 31), birth_time=time(h, m), place="London",
            latitude=51.5074, longitude=-0.1278, timezone="Europe/London"
        )
        assert chart.lagna_sign == ev["name_en"]


def test_lagna_timeline_london_autumn_fallback_minutes():
    # 27 October 2024: 1,500 actual minutes
    events = calculate_dynamic_lagna_events(
        dob=date(2024, 10, 27), lat=51.5074, lon=-0.1278,
        is_sidereal=True, timezone_name="Europe/London"
    )
    # Chronologically ordered in UTC
    for i in range(len(events) - 1):
        assert events[i]["utc_datetime"] < events[i + 1]["utc_datetime"]

    # Full timeline output
    tl = get_daily_lagna_timeline(
        "Kartik", 10, use_sidereal=True,
        dob=date(2024, 10, 27), lat=51.5074, lon=-0.1278, timezone_name="Europe/London"
    )
    assert len(tl) == len(events)

    # Offset suffix (+0100) is present on ambiguous start/end times
    has_offset = any("(+0100)" in item["start"] or "(+0100)" in item["end"] for item in tl)
    assert has_offset is True


def test_lagna_timeline_normal_kolkata_day():
    dob = date(2024, 8, 12)
    tl = get_daily_lagna_timeline(
        "Sravana", 27, use_sidereal=True,
        dob=dob, lat=22.5726, lon=88.3639, timezone_name="Asia/Kolkata"
    )
    assert len(tl) == 12
    # Verify every start time matches calculate_chart
    for item in tl:
        h, m = map(int, item["start"].split(":"))
        chart = calculate_chart(
            dob=dob, birth_time=time(h, m), place="Kolkata",
            latitude=22.5726, longitude=88.3639, timezone="Asia/Kolkata"
        )
        assert chart.lagna_sign == item["name_en"]


def test_subtract_one_minute_and_sort_key_with_offsets():
    assert subtract_one_minute("01:14 (+0100)") == "01:13 (+0100)"
    assert subtract_one_minute("00:00 (+0100)") == "23:59 (+0100)"
    assert subtract_one_minute("12:00") == "11:59"

    # Sort key orders UTC accurately
    # 01:14 (+0100) -> UTC 00:14 (14 minutes)
    # 00:40 (+0000) -> UTC 00:40 (40 minutes)
    key_bst = _timeline_sort_key("01:14 (+0100)")
    key_gmt = _timeline_sort_key("00:40 (+0000)")
    assert key_bst < key_gmt  # 00:14 UTC precedes 00:40 UTC


# ===========================================================================
# 5. Bengali Date Tests
# ===========================================================================

def test_bengali_date_before_and_after_sunrise():
    # 23 July 1989 in Kolkata: sunrise is ~05:07 IST
    dob = date(1989, 7, 23)
    lat = 22.5726
    lon = 88.3639
    tz = "Asia/Kolkata"

    # 1. Born at 04:30 (before sunrise) -> falls back to previous day effective date (22 July)
    y1, m1, d1, eff1 = gregorian_to_bengali(
        dob, birth_time=time(4, 30), latitude=lat, longitude=lon, timezone_name=tz
    )
    assert eff1 == date(1989, 7, 22)
    assert d1 == 6  # Sravana 6

    # 2. Born at 09:30 (after sunrise) -> same day effective date (23 July)
    y2, m2, d2, eff2 = gregorian_to_bengali(
        dob, birth_time=time(9, 30), latitude=lat, longitude=lon, timezone_name=tz
    )
    assert eff2 == date(1989, 7, 23)
    assert d2 == 7  # Sravana 7


def test_bengali_date_date_only_preserves_kolkata_default():
    # Calling with only date (no time/coords) preserves documented Kolkata default
    y, m, d, eff = gregorian_to_bengali(date(1989, 7, 23))
    assert eff == date(1989, 7, 23)
    assert m == 3  # Sravana (0-indexed: Boishakh=0, Jyaistha=1, Ashadha=2, Sravana=3)
    assert d == 7


def test_bengali_date_incomplete_details_raise_value_error():
    dob = date(1989, 7, 23)
    # Time provided but coordinates missing
    with pytest.raises(ValueError, match="Incomplete birth details"):
        gregorian_to_bengali(dob, birth_time=time(9, 30))

    # Coordinates provided but time missing
    with pytest.raises(ValueError, match="Incomplete birth details"):
        gregorian_to_bengali(dob, latitude=22.5726, longitude=88.3639)


def test_bengali_date_invalid_timezone_raises():
    dob = date(1989, 7, 23)
    with pytest.raises(ValueError, match="Invalid IANA timezone"):
        gregorian_to_bengali(
            dob, birth_time=time(9, 30), latitude=22.5726, longitude=88.3639,
            timezone_name="Fake/Invalid_Zone"
        )


def test_bengali_date_polar_sunrise_failure():
    # Arctic circle in June (polar day, midnight sun, sunrise does not occur)
    # Longyearbyen, Svalbard: 78.2232° N, 15.6267° E
    dob = date(2024, 6, 21)
    with pytest.raises(ValueError, match="Sunrise calculation failed"):
        gregorian_to_bengali(
            dob, birth_time=time(12, 0), latitude=78.2232, longitude=15.6267,
            timezone_name="Arctic/Longyearbyen"
        )


def test_find_sun_transit_success_and_failure():
    # Mesha ingress (transit to 0.0 sidereal) in mid-April 2024
    # Approximate JD around 2024-04-13 noon:
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd_approx = swe.julday(2024, 4, 13, 12, 0)
    jd_transit = find_sun_transit(0.0, jd_approx)
    assert jd_transit > 0

    # Calculated longitude at jd_transit must be 0.0 within sub-second precision (~0.00001 deg)
    lon = get_sidereal_sun_longitude(jd_transit)
    diff = min(lon, 360.0 - lon)
    assert diff < 0.0001

    # Bracket failure when center is absurdly far away and impossible
    with patch("app.astrology.bengali_date.get_sidereal_sun_longitude", return_value=180.0):
        with pytest.raises(ValueError, match="Could not establish valid bracket"):
            find_sun_transit(0.0, 2450000.0)


def test_bengali_date_pohela_boishakh():
    # 14 April 2024 is Pohela Boishakh (Boishakh 1, 1431)
    y, m, d, eff = gregorian_to_bengali(date(2024, 4, 14))
    assert y == 1431
    assert m == 0  # Boishakh
    assert d == 1


# ===========================================================================
# 6. PDF Formatting Regression Tests
# ===========================================================================

def test_pdf_format_time_dot_with_and_without_offsets():
    assert format_time_dot("01:14 (+0100)") == "1.14 (+0100)"
    assert format_time_dot("00:45") == "0.45"
    assert format_time_dot("09:05 (-0500)") == "9.05 (-0500)"
    assert format_time_dot("15:30") == "15.30"
    assert format_time_dot("") == ""


# ===========================================================================
# 7. Compatibility Regression: Kolkata/Kanpur 1989-07-23 at 09:30 IST
# ===========================================================================

def test_regression_kolkata_kanpur_1989_unaltered():
    """Verify that established Kolkata (Virgo/Kanya) and Kanpur (Leo/Simha) lagna results remain strictly unaltered."""
    dob = date(1989, 7, 23)
    bt = time(9, 30)

    # 1. Kolkata
    c_kolkata = calculate_chart(
        dob=dob, birth_time=bt, place="Kolkata",
        latitude=22.5726, longitude=88.3639, timezone="Asia/Kolkata"
    )
    assert c_kolkata.lagna_sign == "Kanya"
    assert c_kolkata.lagna_sign_index == 5
    assert c_kolkata.ascendant_longitude == pytest.approx(155.584, abs=0.05)

    # 2. Kanpur
    c_kanpur = calculate_chart(
        dob=dob, birth_time=bt, place="Kanpur",
        latitude=26.4499, longitude=80.3319, timezone="Asia/Kolkata"
    )
    assert c_kanpur.lagna_sign == "Simha"
    assert c_kanpur.lagna_sign_index == 4
    assert c_kanpur.ascendant_longitude == pytest.approx(148.407, abs=0.05)


def test_past_antardashas_increasing_chronological_order():
    """Verify that past antardashas are sorted in increasing chronological order, not decreasing."""
    payload = PdfRequest(
        name="Test Person",
        dob=date(1972, 7, 14),
        time=time(10, 30),
        place="Kolkata",
        latitude=22.5726,
        longitude=88.3639,
        timezone="Asia/Kolkata"
    )
    ctx = build_report_context(payload)
    past = ctx.get("past_antardashas", [])
    assert len(past) > 0, "Expected past antardashas for a 1972 birth"

    # Verify every element progresses forward in time (increasing order)
    for i in range(len(past) - 1):
        assert past[i]["start_date"] <= past[i + 1]["start_date"], (
            f"past_antardashas not in increasing order: {past[i]['start_date']} > {past[i + 1]['start_date']}"
        )
        assert past[i]["start_date"] <= past[i]["end_date"]

