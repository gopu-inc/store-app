# agent/metadata.py
"""Gestion des métadonnées avec support multi-environnements"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, Optional, Any, List
from datetime import datetime
import hashlib


class MetadataManager:
    """Gestionnaire de métadonnées avec cache et lock"""
    
    # Environnements supportés
    SUPPORTED_ENVIRONMENTS = {
        "python": {"gestionnaire": "pip install", "extension": "py", "runner": "python"},
        "nodejs": {"gestionnaire": "npm install", "extension": "js", "runner": "node"},
        "go": {"gestionnaire": "go mod download", "extension": "go", "runner": "go run"},
        "rust": {"gestionnaire": "cargo build", "extension": "rs", "runner": "cargo run"},
        "perl": {"gestionnaire": "cpan install", "extension": "pl", "runner": "perl"},
        "java": {"gestionnaire": "mvn install", "extension": "java", "runner": "java"},
        "kotlin": {"gestionnaire": "gradle build", "extension": "kt", "runner": "kotlin"},
        "gcc": {"gestionnaire": "make", "extension": "c", "runner": "./"},
        "javascript": {"gestionnaire": "npm install", "extension": "js", "runner": "node"},
        "typescript": {"gestionnaire": "npm install", "extension": "ts", "runner": "ts-node"},
        "ruby": {"gestionnaire": "gem install", "extension": "rb", "runner": "ruby"},
        "php": {"gestionnaire": "composer install", "extension": "php", "runner": "php"},
        "swift": {"gestionnaire": "swift build", "extension": "swift", "runner": "swift"},
        "scala": {"gestionnaire": "sbt compile", "extension": "scala", "runner": "scala"},
        "elixir": {"gestionnaire": "mix deps.get", "extension": "ex", "runner": "elixir"},
    }
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.manifest_path = project_path / "manifest.txml"
        self.cache_path = project_path / "cache"
        self.lock_path = project_path / "cache.lock.txml"
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Crée les dossiers nécessaires"""
        self.cache_path.mkdir(exist_ok=True)
    
    def exists(self) -> bool:
        """Vérifie si les métadonnées existent"""
        return self.manifest_path.exists()
    
    def load(self) -> Optional[Dict[str, Any]]:
        """Charge les métadonnées depuis manifest.txml"""
        if not self.manifest_path.exists():
            return None
        
        try:
            tree = ET.parse(self.manifest_path)
            root = tree.getroot()
            
            metadata = {
                "environnement": "python",  # Par défaut
                "gestionnaire": "pip install",
                "app_path": "",
                "lock_cache_path": "./cache/",
                "compiler": {},
                "dependencies": [],
                "permissions": [],
                "run_command": ""
            }
            
            for child in root:
                tag = child.tag
                text = child.text.strip() if child.text else ""
                
                if tag == "permissions":
                    metadata["permissions"] = [p.text.strip() for p in child if p.text]
                elif tag == "dependencies":
                    metadata["dependencies"] = [d.text.strip() for d in child if d.text]
                elif tag == "compiler":
                    compiler_data = {}
                    for comp in child:
                        compiler_data[comp.tag] = comp.text.strip() if comp.text else ""
                    metadata["compiler"] = compiler_data
                elif tag == "environnement":
                    metadata["environnement"] = text
                    # Définir le gestionnaire par défaut
                    if text in self.SUPPORTED_ENVIRONMENTS:
                        metadata["gestionnaire"] = self.SUPPORTED_ENVIRONMENTS[text]["gestionnaire"]
                elif tag == "gestionnaire":
                    metadata["gestionnaire"] = text
                elif tag == "app-path":
                    metadata["app_path"] = text
                elif tag == "lock-cash-path":
                    metadata["lock_cache_path"] = text
                elif tag == "app-run":
                    metadata["run_command"] = text
                else:
                    metadata[tag] = text
            
            return metadata
        except Exception as e:
            print(f"❌ Erreur de chargement des métadonnées: {e}")
            return None
    
    def create(self, name: str, author: str, bundle: str, environnement: str = "python") -> bool:
        """Crée un nouveau manifest.txml avec support multi-environnements"""
        
        env_config = self.SUPPORTED_ENVIRONMENTS.get(environnement, self.SUPPORTED_ENVIRONMENTS["python"])
        
        manifest = f"""<?xml version="1.0" encoding="UTF-8"?>
<app>
    <name>{name}</name>
    <version>1.0.0</version>
    <author>{author}</author>
    <bundle>{bundle}</bundle>
    <description>Application créée avec StoreApp.TUI</description>
    <entrypoint>app.main:App</entrypoint>
    <license>MIT</license>
    <app-path>~/</app-path>
    
    <!-- Environnement d'exécution -->
    <environnement>{environnement}</environnement>
    <gestionnaire>{env_config['gestionnaire']}</gestionnaire>
    
    <!-- Dépendances -->
    <dependencies>
        <dependency>textual>=0.50.0</dependency>
        <dependency>rich>=13.0.0</dependency>
    </dependencies>
    
    <!-- Commande d'exécution -->
    <app-run>cd @{{app-path}} && {{gestionnaire}} -e .</app-run>
    
    <!-- Cache et lock -->
    <lock-cash-path>./cache/</lock-cash-path>
    
    <permissions>
        <permission>notifications</permission>
    </permissions>
</app>
"""
        try:
            self.manifest_path.write_text(manifest)
            print(f"✅ manifest.txml créé: {self.manifest_path}")
            
            # Créer le cache.lock.txml
            self.create_lock_file()
            
            # Créer le dossier src
            src_dir = self.project_path / "src"
            src_dir.mkdir(exist_ok=True)
            print(f"✅ src/ créé: {src_dir}")
            
            return True
        except Exception as e:
            print(f"❌ Erreur de création: {e}")
            return False
    
    def create_lock_file(self) -> bool:
        """Crée le fichier cache.lock.txml"""
        try:
            # Lire le manifest pour générer le cache
            metadata = self.load()
            if not metadata:
                return False
            
            # Générer un checksum du manifest
            manifest_content = self.manifest_path.read_text()
            checksum = hashlib.sha256(manifest_content.encode()).hexdigest()
            
            lock_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<lock>
    <version>1.0.0</version>
    <timestamp>{datetime.now().isoformat()}</timestamp>
    <app>
        <name>{metadata.get('name', '')}</name>
        <bundle>{metadata.get('bundle', '')}</bundle>
        <version>{metadata.get('version', '1.0.0')}</version>
    </app>
    <checksum>
        <manifest>{checksum}</manifest>
        <dependencies>
            {''.join(f'<dep>{d}</dep>' for d in metadata.get('dependencies', []))}
        </dependencies>
    </checksum>
    <cache>
        <path>{metadata.get('lock_cache_path', './cache/')}</path>
        <size>0</size>
        <files>0</files>
        <last_update>{datetime.now().isoformat()}</last_update>
    </cache>
    <environment>
        <type>{metadata.get('environnement', 'python')}</type>
        <gestionnaire>{metadata.get('gestionnaire', 'pip install')}</gestionnaire>
    </environment>
</lock>
"""
            self.lock_path.write_text(lock_content)
            print(f"✅ cache.lock.txml créé: {self.lock_path}")
            return True
        except Exception as e:
            print(f"❌ Erreur création lock: {e}")
            return False
    
    def update_lock(self, metadata: Dict[str, Any]) -> bool:
        """Met à jour le fichier cache.lock.txml"""
        try:
            manifest_content = self.manifest_path.read_text()
            checksum = hashlib.sha256(manifest_content.encode()).hexdigest()
            
            lock_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<lock>
    <version>1.0.0</version>
    <timestamp>{datetime.now().isoformat()}</timestamp>
    <app>
        <name>{metadata.get('name', '')}</name>
        <bundle>{metadata.get('bundle', '')}</bundle>
        <version>{metadata.get('version', '1.0.0')}</version>
    </app>
    <checksum>
        <manifest>{checksum}</manifest>
        <dependencies>
            {''.join(f'<dep>{d}</dep>' for d in metadata.get('dependencies', []))}
        </dependencies>
    </checksum>
    <cache>
        <path>{metadata.get('lock_cache_path', './cache/')}</path>
        <size>0</size>
        <files>0</files>
        <last_update>{datetime.now().isoformat()}</last_update>
    </cache>
    <environment>
        <type>{metadata.get('environnement', 'python')}</type>
        <gestionnaire>{metadata.get('gestionnaire', 'pip install')}</gestionnaire>
    </environment>
</lock>
"""
            self.lock_path.write_text(lock_content)
            return True
        except Exception as e:
            print(f"❌ Erreur mise à jour lock: {e}")
            return False
    
    def get_lock_data(self) -> Optional[Dict[str, Any]]:
        """Récupère les données du fichier lock"""
        if not self.lock_path.exists():
            return None
        
        try:
            tree = ET.parse(self.lock_path)
            root = tree.getroot()
            
            data = {}
            for child in root:
                if child.tag == "checksum":
                    data["checksum"] = {}
                    for sub in child:
                        data["checksum"][sub.tag] = sub.text.strip() if sub.text else ""
                elif child.tag == "cache":
                    data["cache"] = {}
                    for sub in child:
                        data["cache"][sub.tag] = sub.text.strip() if sub.text else ""
                elif child.tag == "environment":
                    data["environment"] = {}
                    for sub in child:
                        data["environment"][sub.tag] = sub.text.strip() if sub.text else ""
                else:
                    data[child.tag] = child.text.strip() if child.text else ""
            
            return data
        except Exception as e:
            print(f"❌ Erreur lecture lock: {e}")
            return None
    
    def get_supported_environments(self) -> List[str]:
        """Retourne la liste des environnements supportés"""
        return list(self.SUPPORTED_ENVIRONMENTS.keys())
