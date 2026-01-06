"""Seed the mountains database with Northeast US ski resorts."""

from pathlib import Path
from sqlalchemy.orm import sessionmaker

from powder.tools.database import Mountain, get_engine, init_db


MOUNTAINS = [
    {
        "name": "Nashoba Valley",
        "state": "MA",
        "lat": 42.48,
        "lon": -71.49,
        "vertical_drop": 240,
        "num_trails": 17,
        "num_lifts": 7,
        "green_pct": 30,
        "blue_pct": 40,
        "black_pct": 30,
        "double_black_pct": 0,
        "terrain_parks": "easy,intermediate",
        "glades": None,
        "pass_types": "indy",
        "allows_snowboarding": True,
        "lift_types": "fixed",
        "has_night_skiing": True,
        "avg_weekday_price": 50,
        "avg_weekend_price": 60,
        "snowmaking_pct": 100,
        "has_magic_carpet": True,
        "has_ski_school": True,
        "learning_area_quality": "good",
    },
    {
        "name": "Gunstock",
        "state": "NH",
        "lat": 43.53,
        "lon": -71.37,
        "vertical_drop": 1340,
        "num_trails": 49,
        "num_lifts": 8,
        "green_pct": 12,
        "blue_pct": 61,
        "black_pct": 27,
        "double_black_pct": 0,
        "terrain_parks": "easy,intermediate",
        "glades": "intermediate",
        "pass_types": "indy",
        "allows_snowboarding": True,
        "lift_types": "highspeed,fixed",
        "has_night_skiing": True,
        "avg_weekday_price": 80,
        "avg_weekend_price": 100,
        "snowmaking_pct": 90,
        "has_magic_carpet": True,
        "has_ski_school": True,
        "learning_area_quality": "good",
    },
    {
        "name": "Waterville Valley",
        "state": "NH",
        "lat": 43.9592,
        "lon": -71.5233,
        "vertical_drop": 2020,
        "num_trails": 62,
        "num_lifts": 11,
        "green_pct": 14,
        "blue_pct": 64,
        "black_pct": 18,
        "double_black_pct": 4,
        "terrain_parks": "easy,intermediate,hard",
        "glades": "easy,intermediate,hard",
        "pass_types": "indy",
        "allows_snowboarding": True,
        "lift_types": "bubble,highspeed,fixed",
        "has_night_skiing": False,
        "avg_weekday_price": 99,
        "avg_weekend_price": 120,
        "snowmaking_pct": 100,
        "has_magic_carpet": True,
        "has_ski_school": True,
        "learning_area_quality": "excellent",
    },
    {
        "name": "Okemo",
        "state": "VT",
        "lat": 43.41,
        "lon": -72.72,
        "vertical_drop": 2200,
        "num_trails": 123,
        "num_lifts": 21,
        "green_pct": 32,
        "blue_pct": 36,
        "black_pct": 32,
        "double_black_pct": 0,
        "terrain_parks": "easy,intermediate,hard,superpipe",
        "glades": "easy,intermediate,hard",
        "pass_types": "epic",
        "allows_snowboarding": True,
        "lift_types": "bubble,highspeed,fixed",
        "has_night_skiing": False,
        "avg_weekday_price": 130,
        "avg_weekend_price": 160,
        "snowmaking_pct": 95,
        "has_magic_carpet": True,
        "has_ski_school": True,
        "learning_area_quality": "excellent",
    },
    {
        "name": "Stowe",
        "state": "VT",
        "lat": 44.5258,
        "lon": -72.7858,
        "vertical_drop": 2360,
        "num_trails": 116,
        "num_lifts": 12,
        "green_pct": 16,
        "blue_pct": 59,
        "black_pct": 18,
        "double_black_pct": 7,
        "terrain_parks": "easy,intermediate,hard",
        "glades": "intermediate,hard",
        "pass_types": "epic",
        "allows_snowboarding": True,
        "lift_types": "gondola,highspeed,fixed",
        "has_night_skiing": False,
        "avg_weekday_price": 150,
        "avg_weekend_price": 180,
        "snowmaking_pct": 83,
        "has_magic_carpet": True,
        "has_ski_school": True,
        "learning_area_quality": "good",
    },
    {
        "name": "Jay Peak",
        "state": "VT",
        "lat": 44.97,
        "lon": -72.47,
        "vertical_drop": 2153,
        "num_trails": 81,
        "num_lifts": 9,
        "green_pct": 20,
        "blue_pct": 40,
        "black_pct": 30,
        "double_black_pct": 10,
        "terrain_parks": "intermediate,hard",
        "glades": "easy,intermediate,hard",
        "pass_types": "ikon",
        "allows_snowboarding": True,
        "lift_types": "tram,highspeed,fixed",
        "has_night_skiing": False,
        "avg_weekday_price": 105,
        "avg_weekend_price": 130,
        "snowmaking_pct": 80,
        "has_magic_carpet": True,
        "has_ski_school": True,
        "learning_area_quality": "good",
    },
]


def seed_database(db_path: Path | str = None):
    """Create and populate the mountains database."""
    if db_path is None:
        db_path = Path(__file__).parent / "mountains.db"

    engine = get_engine(db_path)
    init_db(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Clear existing data
    session.query(Mountain).delete()

    # Add mountains
    for m in MOUNTAINS:
        session.add(Mountain(**m))

    session.commit()
    session.close()

    print(f"Seeded {len(MOUNTAINS)} mountains to {db_path}")


if __name__ == "__main__":
    seed_database()
