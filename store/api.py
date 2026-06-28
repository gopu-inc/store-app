# api.py
"""Client API pour StoreApp.TUI"""

import requests
from typing import Optional, Dict, List, Any
from pathlib import Path

class StoreAPI:
    """Client pour l'API StoreApp.TUI"""
    
    def __init__(self, base_url: str = "https://storeapp-7mbo.onrender.com"):
        self.base_url = base_url
        self.token = None
        self.username = None
    
    def _headers(self) -> Dict[str, str]:
        """Retourne les headers d'authentification"""
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def signup(self, username: str, password: str, email: str = None) -> bool:
        """Inscription"""
        try:
            response = requests.post(
                f"{self.base_url}/signup",
                json={"username": username, "password": password, "email": email},
                timeout=10
            )
            return response.status_code == 200
        except:
            return False
    
    def login(self, username: str, password: str) -> bool:
        """Connexion"""
        try:
            response = requests.post(
                f"{self.base_url}/login",
                json={"username": username, "password": password},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.username = username
                return True
        except:
            pass
        return False
    
    def get_apps(self, limit: int = 50) -> List[Dict]:
        """Liste les applications"""
        try:
            response = requests.get(
                f"{self.base_url}/apps",
                params={"limit": limit},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return []
    
    def get_app(self, bundle: str) -> Optional[Dict]:
        """Récupère les détails d'une application"""
        try:
            response = requests.get(
                f"{self.base_url}/apps/{bundle}",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    def search(self, query: str) -> List[Dict]:
        """Recherche des applications"""
        try:
            response = requests.get(
                f"{self.base_url}/search",
                params={"q": query},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return []
    
    def get_featured(self) -> List[Dict]:
        """Récupère les applications en vedette"""
        try:
            response = requests.get(
                f"{self.base_url}/featured",
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return []
    
    def download(self, bundle: str, output_path: Path) -> bool:
        """Télécharge une application"""
        try:
            response = requests.get(
                f"{self.base_url}/download/{bundle}",
                stream=True,
                timeout=30
            )
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
        except:
            pass
        return False
    
    def publish(self, file_path: Path) -> bool:
        """Publie une application"""
        if not self.token:
            return False
        
        try:
            with open(file_path, 'rb') as f:
                files = {"file": (file_path.name, f, "application/octet-stream")}
                data = {"token": self.token}
                response = requests.post(
                    f"{self.base_url}/publish",
                    files=files,
                    data=data,
                    timeout=30
                )
                return response.status_code == 200
        except:
            pass
        return False

    def rate(self, bundle: str, rating: int, comment: str = None) -> bool:
        if not self.token:
            return False
            try:
                data = {
                    "token": self.token,
                    "rating": rating
                }
                if comment:
                    data["comment"] = comment
                    response = requests.post(
                        f"{self.base_url}/rate/{bundle}",
                        data=data,
                        timeout=10
                    )
                    return response.status_code == 200
            except Exception as e:
                print(f"❌ Rate error: {e}")
                return False

    def comment(self, bundle: str, content: str) -> bool:
        """Commente une application"""
        if not self.token:
            return False
        
        try:
            data = {"token": self.token, "content": content}
            response = requests.post(
                f"{self.base_url}/comment/{bundle}",
                data=data,
                timeout=10
            )
            return response.status_code == 200
        except:
            pass
        return False
