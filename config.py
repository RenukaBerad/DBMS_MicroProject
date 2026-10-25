"""
Configuration Module for Internal Marks Management System
Loads and manages PostgreSQL database credentials and application settings.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Optional

try:
    from dotenv import load_dotenv
    # Load .env file from the current directory if present
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    # python-dotenv not installed, proceed with system environment variables
    pass


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "internal_marks_db"
    user: str = "postgres"
    password: str = ""

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Instantiate configuration directly from environment variables."""
        port_raw = os.getenv("DB_PORT", "5432")
        try:
            port = int(port_raw)
        except ValueError:
            port = 5432

        return cls(
            host=os.getenv("DB_HOST", "localhost").strip(),
            port=port,
            database=os.getenv("DB_NAME", "internal_marks_db").strip(),
            user=os.getenv("DB_USER", "postgres").strip(),
            password=os.getenv("DB_PASSWORD", "").strip()
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary suitable for psycopg/psycopg2."""
        return {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "user": self.user,
            "password": self.password,
            "connect_timeout": 5  # Quick timeout to prevent GUI freezes
        }

    def is_placeholder_password(self) -> bool:
        """Check if password is empty or still set to the example placeholder."""
        if not self.password:
            return True
        placeholders = [
            "replace_with_your_local_password",
            "your_password",
            "password",
            "changeme"
        ]
        return self.password.lower() in placeholders

    @property
    def display_target(self) -> str:
        """Human-readable target summary for status bars (password masked)."""
        return f"{self.user}@{self.host}:{self.port}/{self.database}"


# Global application configuration instance
CURRENT_CONFIG = DatabaseConfig.from_env()


def get_current_config() -> DatabaseConfig:
    """Return the active database configuration."""
    global CURRENT_CONFIG
    return CURRENT_CONFIG


def update_config(host: str, port: int, database: str, user: str, password: str, persist_to_env: bool = False) -> DatabaseConfig:
    """Update runtime configuration and optionally persist to local .env file."""
    global CURRENT_CONFIG
    CURRENT_CONFIG = DatabaseConfig(
        host=host.strip(),
        port=port,
        database=database.strip(),
        user=user.strip(),
        password=password.strip()
    )

    if persist_to_env:
        env_path = Path(__file__).resolve().parent / ".env"
        lines = [
            "# Auto-updated by Internal Marks Management System\n",
            f"DB_HOST={CURRENT_CONFIG.host}\n",
            f"DB_PORT={CURRENT_CONFIG.port}\n",
            f"DB_NAME={CURRENT_CONFIG.database}\n",
            f"DB_USER={CURRENT_CONFIG.user}\n",
            f"DB_PASSWORD={CURRENT_CONFIG.password}\n"
        ]
        try:
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(lines)
        except Exception:
            pass

    return CURRENT_CONFIG
