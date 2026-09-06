#!/usr/bin/env python
"""
Weather Forecast Database Manager

Manages user's default city for weather queries.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

DB_DIR = Path(os.environ.get("WEATHER_DATA_DIR", os.environ.get("CODEX_DATA_DIR", Path.cwd() / "codex-data"))) / "weather_forecast"
CONFIG_FILE = DB_DIR / "config.json"


def ensure_db_files() -> None:
    """Ensure database file exists."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    
    if not CONFIG_FILE.exists():
        default_config = {
            "initialized": False,
            "created_at": datetime.now().isoformat(),
            "default_city": None,
            "unit": "metric",  # metric or uscs
            "format": "compact"  # compact or full
        }
        CONFIG_FILE.write_text(json.dumps(default_config, indent=2))


def load_config() -> Dict[str, Any]:
    """Load config from file."""
    ensure_db_files()
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}


def save_config(config: Dict[str, Any]) -> None:
    """Save config to file."""
    ensure_db_files()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)


# ============================================================================
# CITY MANAGEMENT
# ============================================================================

def has_default_city() -> bool:
    """Check if user has set a default city."""
    config = load_config()
    return config.get("initialized", False) and config.get("default_city") is not None


def get_default_city() -> Optional[str]:
    """Get user's default city."""
    config = load_config()
    return config.get("default_city")


def set_default_city(city: str) -> None:
    """Set user's default city."""
    config = load_config()
    config["default_city"] = city
    config["initialized"] = True
    config["updated_at"] = datetime.now().isoformat()
    save_config(config)


def get_weather_config() -> Dict[str, Any]:
    """Get full weather config."""
    return load_config()


def update_config(key: str, value: Any) -> None:
    """Update a specific config key."""
    config = load_config()
    config[key] = value
    config["updated_at"] = datetime.now().isoformat()
    save_config(config)


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Weather Forecast Database Manager")
        print("\nUsage:")
        print("  python weather_db.py has_city")
        print("  python weather_db.py get_city")
        print("  python weather_db.py set_city <city_name>")
        print("  python weather_db.py get_config")
        sys.exit(1)

    command = sys.argv[1]

    if command == "has_city":
        print("true" if has_default_city() else "false")
    elif command == "get_city":
        city = get_default_city()
        print(city if city else "")
    elif command == "set_city":
        if len(sys.argv) < 3:
            print("Error: city_name required")
            sys.exit(1)
        city = sys.argv[2]
        set_default_city(city)
        print(f"✓ Default city set to: {city}")
    elif command == "get_config":
        print(json.dumps(get_weather_config(), indent=2))
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
