# config.py
"""Configuration StoreApp.TUI"""

import os
from pathlib import Path

class Config:
    """Configuration de l'application"""
    
    APP_NAME = "StoreApp.TUI"
    VERSION = "1.0.0"
    
    # API
    API_BASE_URL = os.getenv("STOREAPP_API_URL", "https://storeapp-7mbo.onrender.com")
    
    # Stockage local
    STORE_DIR = Path.home() / ".storeapp"
    DOWNLOAD_DIR = STORE_DIR / "downloads"
    INSTALL_DIR = STORE_DIR / "apps"
    
    @classmethod
    def init_dirs(cls):
        """Crée les dossiers nécessaires"""
        cls.STORE_DIR.mkdir(exist_ok=True)
        cls.DOWNLOAD_DIR.mkdir(exist_ok=True)
        cls.INSTALL_DIR.mkdir(exist_ok=True)

# Initialiser les dossiers
Config.init_dirs()
