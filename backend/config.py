# ==============================================================================
# KRIYA Authentication Backend — Configuration Loader
# ==============================================================================
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
env_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path=env_path)

AUTH_HOST = os.getenv("AUTH_HOST", "0.0.0.0")
AUTH_PORT = int(os.getenv("AUTH_PORT", "5000"))

# Company PostgreSQL Database on Raspberry Pi 5 (READ-ONLY)
COMPANY_DB_URL = os.getenv(
    "COMPANY_DB_URL",
    "postgresql://Lemniscus_Trigeminalis:vicky2201@100.98.154.51:5432/company_db"
)

# JWT Signing Secret (must match agent/api/session.py)
JWT_SECRET = os.getenv("JWT_SECRET", "kriya_sovereign_airgap_secret_2026_mrpl")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_SECONDS = 86400  # 24 hours

# Local Auth SQLite storage directory
DATA_DIR = Path(os.getenv("DATA_DIR", str(ROOT_DIR / "backend" / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
AUTH_DB_PATH = DATA_DIR / "kriya_auth.db"
