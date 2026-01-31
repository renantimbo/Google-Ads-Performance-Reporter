from dataclasses import dataclass
from pathlib import Path
import os

@dataclass(frozen=True)
class Settings:
    repo_root: Path = Path(__file__).resolve().parents[1]
    db_path: Path = repo_root / "data.sqlite"
    ads_config_path: Path = repo_root / "google-ads.yaml"
    reports_dir: Path = repo_root / "reports"
    fetch_days: int = int(os.getenv("FETCH_DAYS", "30"))
    analysis_window_days: int = int(os.getenv("ANALYSIS_WINDOW_DAYS", "7"))

settings = Settings()
