# config.py
"""Configuration StoreApp.TUI"""

import os
import json
from pathlib import Path


class Config:
    """Configuration de l'application"""

    APP_NAME = "StoreApp.TUI"
    VERSION = "2.0.0"

    # API
    API_BASE_URL = os.getenv("STOREAPP_API_URL", "https://storeapp-7mbo.onrender.com")

    # Stockage local
    STORE_DIR = Path.home() / ".storeapp"
    DOWNLOAD_DIR = STORE_DIR / "downloads"
    INSTALL_DIR = STORE_DIR / "apps"
    TOKEN_FILE = STORE_DIR / "session.json"

    @classmethod
    def init_dirs(cls):
        """Crée les dossiers nécessaires"""
        cls.STORE_DIR.mkdir(exist_ok=True)
        cls.DOWNLOAD_DIR.mkdir(exist_ok=True)
        cls.INSTALL_DIR.mkdir(exist_ok=True)

    @classmethod
    def save_session(cls, username: str, token: str):
        """Sauvegarde la session en cache"""
        cls.TOKEN_FILE.write_text(
            json.dumps({"username": username, "token": token})
        )

    @classmethod
    def load_session(cls) -> dict:
        """Charge la session depuis le cache"""
        try:
            if cls.TOKEN_FILE.exists():
                return json.loads(cls.TOKEN_FILE.read_text())
        except Exception:
            pass
        return {}

    @classmethod
    def clear_session(cls):
        """Supprime la session en cache"""
        try:
            cls.TOKEN_FILE.unlink(missing_ok=True)
        except Exception:
            pass


# Initialiser les dossiers
Config.init_dirs()
