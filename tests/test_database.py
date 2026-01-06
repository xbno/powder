"""Tests for mountain database."""

import pytest
from sqlalchemy.orm import sessionmaker

from powder.tools.database import (
    Mountain,
    get_engine,
    init_db,
    query_mountains,
    haversine_km,
)

# Boston coordinates for testing
BOSTON_LAT = 42.3601
BOSTON_LON = -71.0589


@pytest.fixture
def db_session():
    """Create in-memory database with 3 test mountains."""
    engine = get_engine(":memory:")
    init_db(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Real Northeast mountains
    mountains = [
        Mountain(
            name="Nashoba Valley",
            state="MA",
            lat=42.48,  # ~45km from Boston - closest
            lon=-71.49,
            vertical_drop=240,
            num_trails=17,
            num_lifts=7,
            green_pct=30,
            blue_pct=40,
            black_pct=30,
            double_black_pct=0,
            terrain_parks="easy,intermediate",
            glades=None,
            pass_types="indy",
            allows_snowboarding=True,
            lift_types="fixed",
            avg_weekday_price=50,
            avg_weekend_price=60,
        ),
        Mountain(
            name="Gunstock",
            state="NH",
            lat=43.53,  # ~140km from Boston
            lon=-71.37,
            vertical_drop=1340,
            num_trails=49,
            num_lifts=8,
            green_pct=12,
            blue_pct=61,
            black_pct=27,
            double_black_pct=0,
            terrain_parks="easy,intermediate",
            glades="intermediate",
            pass_types="indy",
            allows_snowboarding=True,
            lift_types="highspeed,fixed",  # no bubble
            avg_weekday_price=80,
            avg_weekend_price=100,
        ),
        Mountain(
            name="Waterville Valley",
            state="NH",
            lat=43.9592,  # ~185km from Boston
            lon=-71.5233,
            vertical_drop=2020,
            num_trails=62,
            num_lifts=11,
            green_pct=14,
            blue_pct=64,
            black_pct=18,
            double_black_pct=4,
            terrain_parks="easy,intermediate,hard",
            glades="easy,intermediate,hard",
            pass_types="indy",
            allows_snowboarding=True,
            lift_types="bubble,highspeed,fixed",
            avg_weekday_price=99,
            avg_weekend_price=120,
        ),
        Mountain(
            name="Okemo",
            state="VT",
            lat=43.41,  # ~175km from Boston
            lon=-72.72,
            vertical_drop=2200,
            num_trails=123,
            num_lifts=21,
            green_pct=32,
            blue_pct=36,
            black_pct=32,
            double_black_pct=0,
            terrain_parks="easy,intermediate,hard,superpipe",
            glades="easy,intermediate,hard",
            pass_types="epic",
            allows_snowboarding=True,
            lift_types="bubble,highspeed,fixed",
            avg_weekday_price=130,
            avg_weekend_price=160,
        ),
        Mountain(
            name="Stowe",
            state="VT",
            lat=44.5258,  # ~270km from Boston
            lon=-72.7858,
            vertical_drop=2360,
            num_trails=116,
            num_lifts=12,
            green_pct=16,
            blue_pct=59,
            black_pct=18,
            double_black_pct=7,
            terrain_parks="easy,intermediate,hard",
            glades="intermediate,hard",
            pass_types="epic",
            allows_snowboarding=True,
            lift_types="gondola,highspeed,fixed",
            avg_weekday_price=150,
            avg_weekend_price=180,
        ),
        Mountain(
            name="Jay Peak",
            state="VT",
            lat=44.97,  # ~320km from Boston - furthest
            lon=-72.47,
            vertical_drop=2153,
            num_trails=81,
            num_lifts=9,
            green_pct=20,
            blue_pct=40,
            black_pct=30,
            double_black_pct=10,
            terrain_parks="intermediate,hard",
            glades="easy,intermediate,hard",
            pass_types="ikon",
            allows_snowboarding=True,
            lift_types="tram,highspeed,fixed",
            avg_weekday_price=105,
            avg_weekend_price=130,
        ),
    ]
    session.add_all(mountains)
    session.commit()

    yield session

    session.close()


def test_haversine_km():
    """Test haversine distance calculation."""
    # Boston to NYC is ~306 km
    boston = (42.3601, -71.0589)
    nyc = (40.7128, -74.0060)
    dist = haversine_km(*boston, *nyc)
    assert 300 < dist < 320


def test_query_all_mountains(db_session):
    """Test querying all mountains within range."""
    results = query_mountains(db_session, BOSTON_LAT, BOSTON_LON, max_distance_km=500)
    assert len(results) == 6
    # Should be sorted by distance (Nashoba closest, Jay Peak furthest)
    assert results[0]["name"] == "Nashoba Valley"
    assert results[-1]["name"] == "Jay Peak"
    assert results[0]["distance_km"] <= results[1]["distance_km"]


def test_query_filter_by_distance(db_session):
    """Test filtering by max distance."""
    # Nashoba (~45km), Gunstock (~140km)
    results = query_mountains(db_session, BOSTON_LAT, BOSTON_LON, max_distance_km=150)
    assert len(results) == 2
    names = [r["name"] for r in results]
    assert "Nashoba Valley" in names
    assert "Gunstock" in names


def test_query_filter_by_pass_type(db_session):
    """Test filtering by pass type."""
    # Jay Peak is on Ikon
    results = query_mountains(
        db_session, BOSTON_LAT, BOSTON_LON, max_distance_km=500, pass_type="ikon"
    )
    assert len(results) == 1
    assert results[0]["name"] == "Jay Peak"

    # Okemo and Stowe are on Epic
    results = query_mountains(
        db_session, BOSTON_LAT, BOSTON_LON, max_distance_km=500, pass_type="epic"
    )
    assert len(results) == 2
    names = [r["name"] for r in results]
    assert "Okemo" in names
    assert "Stowe" in names


def test_lift_types_returned(db_session):
    """Test that lift_types info is returned."""
    results = query_mountains(db_session, BOSTON_LAT, BOSTON_LON, max_distance_km=500)
    # Waterville and Okemo have bubble lifts
    bubble_mountains = [r for r in results if "bubble" in (r["lift_types"] or "")]
    assert len(bubble_mountains) == 2
    # Stowe has a gondola
    gondola_mountains = [r for r in results if "gondola" in (r["lift_types"] or "")]
    assert len(gondola_mountains) == 1
    assert gondola_mountains[0]["name"] == "Stowe"


def test_query_returns_distance(db_session):
    """Test that results include distance_km."""
    results = query_mountains(db_session, BOSTON_LAT, BOSTON_LON, max_distance_km=500)
    for r in results:
        assert "distance_km" in r
        assert r["distance_km"] > 0
