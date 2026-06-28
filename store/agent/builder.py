# agent/builder.py
"""Système de build des packages"""

import os
import json
import tarfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import shutil


class Builder:
    """Système de build StoreApp.TUI"""
    
    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.build_dir = project_path / "build"
        self.dist_dir = project_path / "dist"
        self.temp_dir = tempfile.mkdtemp(prefix="store_build_")
        
        self._ensure_dirs()
    
    def _ensure_dirs(self):
        """Crée les dossiers nécessaires"""
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
    
    def build(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Build le package"""
        try:
            # Vérifier les fichiers requis
            required = ["manifest.txml", "README.md"]
            for req in required:
                if not (self.project_path / req).exists():
                    return {"success": False, "error": f"Fichier manquant: {req}"}
            
            # Nom du package
            bundle = metadata.get("bundle", "com.example.app")
            version = metadata.get("version", "1.0.0")
            package_name = f"{bundle}-{version}.tpkg"
            output_path = self.dist_dir / package_name
            
            # Créer le package
            with tarfile.open(output_path, "w:gz") as tar:
                # Ajouter manifest.txml
                tar.add(self.project_path / "manifest.txml", arcname="manifest.txml")
                
                # Ajouter README.md
                tar.add(self.project_path / "README.md", arcname="README.md")
                
                # Ajouter postinstall.bundle si existe
                if (self.project_path / "postinstall.bundle").exists():
                    tar.add(self.project_path / "postinstall.bundle", arcname="postinstall.bundle")
                
                # Ajouter le code source
                src_dir = self.project_path / "src"
                if src_dir.exists():
                    tar.add(src_dir, arcname="src")
                
                # Ajouter les fichiers de l'agent si présents
                for item in ["agent", "screens", "widgets", "styles"]:
                    src = self.project_path / item
                    if src.exists():
                        tar.add(src, arcname=item)
            
            # Générer le SHA256
            import hashlib
            with open(output_path, "rb") as f:
                sha = hashlib.sha256(f.read()).hexdigest()
            
            # Sauvegarder la signature
            signature_path = self.dist_dir / f"{package_name}.sha256"
            with open(signature_path, "w") as f:
                f.write(sha)
            
            return {
                "success": True,
                "output_path": str(output_path),
                "signature": sha,
                "size": output_path.stat().st_size
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_package_path(self) -> Optional[Path]:
        """Récupère le chemin du dernier package build"""
        packages = list(self.dist_dir.glob("*.tpkg"))
        if packages:
            return max(packages, key=lambda p: p.stat().st_mtime)
        return None
    
    def clean(self):
        """Nettoie les fichiers de build"""
        shutil.rmtree(self.build_dir, ignore_errors=True)
        shutil.rmtree(self.dist_dir, ignore_errors=True)
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        self._ensure_dirs()
