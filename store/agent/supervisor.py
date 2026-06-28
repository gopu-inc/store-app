# agent/supervisor.py
"""Supervisor secure self"""

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class Supervisor:
    """Supervisor sécurisé pour l'agent"""
    
    def __init__(self):
        self.secure_file = Path.home() / ".storeapp" / "supervisor.json"
        self.secure_file.parent.mkdir(exist_ok=True)
        self._load_secure_data()
    
    def _load_secure_data(self):
        """Charge les données sécurisées"""
        if self.secure_file.exists():
            try:
                self.secure_data = json.loads(self.secure_file.read_text())
            except:
                self.secure_data = {}
        else:
            self.secure_data = {}
    
    def _save_secure_data(self):
        """Sauvegarde les données sécurisées"""
        self.secure_file.write_text(json.dumps(self.secure_data, indent=2))
    
    def verify(self, data: Dict[str, Any]) -> bool:
        """Vérifie l'intégrité des données"""
        checksum = data.get("_checksum")
        if not checksum:
            return False
        
        # Recalculer le checksum
        data_copy = data.copy()
        data_copy.pop("_checksum", None)
        computed = hashlib.sha256(json.dumps(data_copy, sort_keys=True).encode()).hexdigest()
        
        return computed == checksum
    
    def secure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sécurise les données avec un checksum"""
        data_copy = data.copy()
        data_copy["_checksum"] = hashlib.sha256(
            json.dumps(data_copy, sort_keys=True).encode()
        ).hexdigest()
        data_copy["_secured_at"] = datetime.now().isoformat()
        return data_copy
    
    def store(self, key: str, data: Dict[str, Any]):
        """Stocke des données sécurisées"""
        self.secure_data[key] = self.secure(data)
        self._save_secure_data()
    
    def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Récupère des données sécurisées"""
        data = self.secure_data.get(key)
        if data and self.verify(data):
            return data
        return None
    
    def self_verify(self) -> bool:
        """Vérifie l'intégrité de toutes les données stockées"""
        for key, data in self.secure_data.items():
            if not self.verify(data):
                return False
        return True
