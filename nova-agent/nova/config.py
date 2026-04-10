"""Configuration management for Nova Agent."""

import os
import yaml
from pathlib import Path

DEFAULT_CONFIG_DIR = Path.home() / ".nova"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.yaml"
DEFAULT_RULES_FILE = DEFAULT_CONFIG_DIR / "organize_rules.yaml"

DEFAULT_CONFIG = {
    "ai": {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 4096,
    },
    "organizer": {
        "default_target": str(Path.home()),
        "dry_run": False,
        "rules_file": str(DEFAULT_RULES_FILE),
    },
    "watch": {
        "directories": [str(Path.home() / "Downloads")],
        "interval_seconds": 5,
    },
    "theme": {
        "style": "dark",
    },
}

DEFAULT_ORGANIZE_RULES = {
    "categories": {
        "Documents": {
            "extensions": [".pdf", ".doc", ".docx", ".txt", ".odt", ".rtf", ".md", ".tex", ".epub"],
            "folder": "Documents",
        },
        "Images": {
            "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff", ".heic"],
            "folder": "Pictures",
        },
        "Videos": {
            "extensions": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
            "folder": "Videos",
        },
        "Audio": {
            "extensions": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus"],
            "folder": "Music",
        },
        "Archives": {
            "extensions": [".zip", ".tar", ".gz", ".bz2", ".rar", ".7z", ".xz", ".tar.gz"],
            "folder": "Archives",
        },
        "Code": {
            "extensions": [".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".c", ".cpp",
                          ".h", ".rb", ".php", ".swift", ".kt", ".scala", ".sh", ".bash"],
            "folder": "Code",
        },
        "Data": {
            "extensions": [".csv", ".json", ".xml", ".yaml", ".yml", ".sql", ".db", ".sqlite",
                          ".parquet", ".xlsx", ".xls"],
            "folder": "Data",
        },
        "Installers": {
            "extensions": [".exe", ".msi", ".dmg", ".deb", ".rpm", ".appimage", ".snap", ".flatpak"],
            "folder": "Installers",
        },
        "Fonts": {
            "extensions": [".ttf", ".otf", ".woff", ".woff2", ".eot"],
            "folder": "Fonts",
        },
        "Design": {
            "extensions": [".psd", ".ai", ".sketch", ".fig", ".xd", ".blend", ".obj", ".stl"],
            "folder": "Design",
        },
    }
}


def ensure_config_dir():
    """Create config directory if it doesn't exist."""
    DEFAULT_CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    """Load configuration from file, creating defaults if needed."""
    ensure_config_dir()

    if DEFAULT_CONFIG_FILE.exists():
        with open(DEFAULT_CONFIG_FILE) as f:
            user_config = yaml.safe_load(f) or {}
        # Merge with defaults
        config = _deep_merge(DEFAULT_CONFIG, user_config)
    else:
        config = DEFAULT_CONFIG.copy()
        save_config(config)

    return config


def save_config(config: dict):
    """Save configuration to file."""
    ensure_config_dir()
    with open(DEFAULT_CONFIG_FILE, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)


def load_organize_rules() -> dict:
    """Load file organization rules."""
    ensure_config_dir()

    if DEFAULT_RULES_FILE.exists():
        with open(DEFAULT_RULES_FILE) as f:
            return yaml.safe_load(f) or DEFAULT_ORGANIZE_RULES
    else:
        with open(DEFAULT_RULES_FILE, "w") as f:
            yaml.dump(DEFAULT_ORGANIZE_RULES, f, default_flow_style=False, sort_keys=False)
        return DEFAULT_ORGANIZE_RULES


def get_api_key() -> str | None:
    """Get Anthropic API key from environment or config."""
    return os.environ.get("ANTHROPIC_API_KEY")


def _deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
