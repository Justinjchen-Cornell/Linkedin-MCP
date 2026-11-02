import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    db_path: Path = Path(os.getenv("LINKEDIN_WORKBENCH_DB", "data/app.db"))
    host: str = "127.0.0.1"
    port: int = 8765


settings = Settings()
