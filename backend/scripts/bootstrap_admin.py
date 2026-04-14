from pathlib import Path
import sys


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.bootstrap_service import bootstrap_default_data


def main() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        bootstrap_default_data(db)
    print("Default infrastructure data initialized successfully.")


if __name__ == "__main__":
    main()
