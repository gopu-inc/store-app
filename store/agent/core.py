# agent/core.py
"""Agent principal de build"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .builder import Builder
from .metadata import MetadataManager
from .commands import CommandManager
from .supervisor import Supervisor


class Agent:
    """Agent de build StoreApp.TUI"""
    
    VERSION = "1.0.0"
    NAME = "store-agent"
    
    def __init__(self, project_path: Optional[str] = None):
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.builder = Builder(self.project_path)
        self.metadata = MetadataManager(self.project_path)
        self.commands = CommandManager()
        self.supervisor = Supervisor()
        
        # État de l'agent
        self.state = {
            "initialized": False,
            "project_loaded": False,
            "last_build": None,
            "current_version": "1.0.0"
        }
        
        self._init_agent()
    
    def _init_agent(self):
        """Initialise l'agent"""
        print(f"🤖 Agent {self.NAME} v{self.VERSION}")
        print(f"📁 Projet: {self.project_path}")
        
        # Vérifier si le projet est initialisé
        if self.metadata.exists():
            self.state["project_loaded"] = True
            print("✅ Projet chargé")
        else:
            print("ℹ️ Nouveau projet - exécutez 'agent init'")
        
        self.state["initialized"] = True
    
    def init_project(self, name: str, author: str, bundle: str) -> bool:
        """Initialise un nouveau projet"""
        return self.metadata.create(name, author, bundle)
    
    def build(self, output_dir: Optional[str] = None) -> Dict[str, Any]:
        """Build le package"""
        print("🔨 Build en cours...")
        
        # Vérifier les métadonnées
        metadata = self.metadata.load()
        if not metadata:
            print("❌ Métadonnées manquantes - exécutez 'agent init'")
            return {"success": False, "error": "Métadonnées manquantes"}
        
        # Build
        result = self.builder.build(metadata)
        
        if result.get("success"):
            self.state["last_build"] = datetime.now().isoformat()
            print(f"✅ Build réussi: {result.get('output_path')}")
        else:
            print(f"❌ Build échoué: {result.get('error')}")
        
        return result
    def list_environments(self) -> List[str]:
    """Liste les environnements supportés"""
    return self.metadata.get_supported_environments()
    def set_environment(self, env: str) -> bool:
        """Définit l'environnement du projet"""
        if env not in self.metadata.SUPPORTED_ENVIRONMENTS:
            print(f"❌ Environnement non supporté: {env}")
            print(f"📋 Supportés: {', '.join(self.metadata.get_supported_environments())}")
            return False
            metadata = self.metadata.load()
            if not metadata:
                print("❌ Métadonnées non trouvées")
                return False
                metadata["environnement"] = env
                metadata["gestionnaire"] = self.metadata.SUPPORTED_ENVIRONMENTS[env]["gestionnaire"]
                print(f"✅ Environnement défini sur: {env}")
                return True
    def publish(self, token: str) -> Dict[str, Any]:
        """Publie le package sur StoreApp.TUI"""
        print("📤 Publication en cours...")
        
        # Vérifier le build
        if not self.state.get("last_build"):
            print("❌ Aucun build trouvé - exécutez 'agent build'")
            return {"success": False, "error": "Aucun build"}
        
        # Récupérer le package
        package_path = self.builder.get_package_path()
        if not package_path:
            return {"success": False, "error": "Package introuvable"}
        
        # Publier via l'API
        try:
            import requests
            files = {"file": (package_path.name, open(package_path, "rb"))}
            data = {"token": token}
            
            response = requests.post(
                "https://storeapp-7mbo.onrender.com/publish",
                files=files,
                data=data,
                timeout=30
            )
            
            if response.status_code == 200:
                print("✅ Publié avec succès")
                return {"success": True, "response": response.json()}
            else:
                print(f"❌ Échec: {response.status_code}")
                return {"success": False, "error": response.text}
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return {"success": False, "error": str(e)}
    
    def status(self) -> Dict[str, Any]:
        """Retourne le statut de l'agent"""
        metadata = self.metadata.load()
        return {
            "agent": {
                "name": self.NAME,
                "version": self.VERSION,
                "state": self.state
            },
            "project": {
                "initialized": self.metadata.exists(),
                "metadata": metadata
            }
        }
    
    def run_command(self, cmd: str, args: List[str]) -> bool:
        """Exécute une commande de l'agent"""
        return self.commands.execute(cmd, args, self)
