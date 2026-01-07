"""Seed the mountains database from JSONL file."""

import json
from pathlib import Path
from sqlalchemy.orm import sessionmaker

from powder.tools.database import Mountain, get_engine, init_db


DATA_DIR = Path(__file__).parent
MOUNTAINS_JSONL = DATA_DIR / "mountains.jsonl"


def load_mountains() -> list[dict]:
    """Load mountains from JSONL file."""
    mountains = []
    with open(MOUNTAINS_JSONL) as f:
        for line in f:
            line = line.strip()
            if line:
                mountains.append(json.loads(line))
    return mountains


def seed_database(db_path: Path | str = None):
    """Create and populate the mountains database from JSONL."""
    if db_path is None:
        db_path = DATA_DIR / "mountains.db"

    mountains = load_mountains()

    engine = get_engine(db_path)
    init_db(engine)

    Session = sessionmaker(bind=engine)
    session = Session()

    # Clear existing data
    session.query(Mountain).delete()

    # Add mountains
    for m in mountains:
        session.add(Mountain(**m))

    session.commit()
    session.close()

    print(f"Seeded {len(mountains)} mountains to {db_path}")


if __name__ == "__main__":
    seed_database()
