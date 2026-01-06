"""SQLite database for ski mountains."""

import math
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text
from sqlalchemy.orm import sessionmaker, declarative_base

Base = declarative_base()


class Mountain(Base):
    """Ski mountain model."""

    __tablename__ = "mountains"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    state = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    vertical_drop = Column(Integer)
    base_elevation = Column(Integer)
    summit_elevation = Column(Integer)
    num_trails = Column(Integer)
    num_lifts = Column(Integer)
    green_pct = Column(Integer)
    blue_pct = Column(Integer)
    black_pct = Column(Integer)
    double_black_pct = Column(Integer)
    terrain_parks = Column(Text)  # comma-separated: "easy,intermediate,hard,superpipe"
    glades = Column(Text)  # comma-separated: "easy,intermediate,hard"
    pass_types = Column(Text)  # comma-separated: "ikon,indy"
    allows_snowboarding = Column(Boolean, default=True)
    lift_types = Column(Text)  # comma-separated: "bubble,gondola,highspeed,fixed"
    has_night_skiing = Column(Boolean, default=False)
    avg_weekday_price = Column(Integer)
    avg_weekend_price = Column(Integer)
    website = Column(String)


def get_engine(db_path: Path | str = ":memory:"):
    """Create SQLAlchemy engine."""
    if db_path == ":memory:":
        return create_engine("sqlite:///:memory:")
    return create_engine(f"sqlite:///{db_path}")


def init_db(engine):
    """Create all tables."""
    Base.metadata.create_all(engine)


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two coordinates in km."""
    R = 6371
    lat1_rad, lat2_rad = math.radians(lat1), math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def query_mountains(
    session,
    lat: float,
    lon: float,
    max_distance_km: float = 300,
    pass_type: str | None = None,
    allows_snowboarding: bool | None = None,
) -> list[dict]:
    """
    Query mountains within radius matching filters.

    Returns list of dicts with mountain data + distance_km.
    """
    query = session.query(Mountain)

    if allows_snowboarding is not None:
        query = query.filter(Mountain.allows_snowboarding == allows_snowboarding)

    if pass_type:
        query = query.filter(Mountain.pass_types.contains(pass_type))

    results = []
    for m in query.all():
        dist = haversine_km(lat, lon, m.lat, m.lon)
        if dist <= max_distance_km:
            results.append({
                "id": m.id,
                "name": m.name,
                "state": m.state,
                "lat": m.lat,
                "lon": m.lon,
                "vertical_drop": m.vertical_drop,
                "num_trails": m.num_trails,
                "num_lifts": m.num_lifts,
                "green_pct": m.green_pct,
                "blue_pct": m.blue_pct,
                "black_pct": m.black_pct,
                "terrain_parks": m.terrain_parks,
                "glades": m.glades,
                "pass_types": m.pass_types,
                "allows_snowboarding": m.allows_snowboarding,
                "lift_types": m.lift_types,
                "avg_weekday_price": m.avg_weekday_price,
                "avg_weekend_price": m.avg_weekend_price,
                "distance_km": round(dist, 1),
            })

    return sorted(results, key=lambda x: x["distance_km"])
