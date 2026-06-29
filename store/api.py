# api.py
"""Client API pour StoreApp.TUI — httpx + gestion d'erreurs robuste"""

import httpx
from typing import Optional, Dict, List
from pathlib import Path
from config import Config


class StoreAPI:
    """Client pour l'API StoreApp.TUI"""

    def __init__(self, base_url: str = None):
        self.base_url = (base_url or Config.API_BASE_URL).rstrip("/")
        self.token: Optional[str] = None
        self.username: Optional[str] = None
        self._load_session()

    # ── Session ──────────────────────────────────────────────────────────────

    def _load_session(self):
        session = Config.load_session()
        if session:
            self.token = session.get("token")
            self.username = session.get("username")

    def _headers(self) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    # ── Auth ─────────────────────────────────────────────────────────────────

    def signup(self, username: str, password: str, email: str = None) -> bool:
        try:
            r = httpx.post(
                f"{self.base_url}/signup",
                json={"username": username, "password": password, "email": email},
                timeout=15,
            )
            return r.status_code == 200
        except Exception:
            return False

    def login(self, username: str, password: str) -> bool:
        try:
            r = httpx.post(
                f"{self.base_url}/login",
                json={"username": username, "password": password},
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                self.token = data.get("access_token")
                self.username = username
                Config.save_session(username, self.token)
                return True
        except Exception:
            pass
        return False

    def logout(self):
        self.token = None
        self.username = None
        Config.clear_session()

    # ── Apps ─────────────────────────────────────────────────────────────────

    def get_apps(self, limit: int = 50) -> List[Dict]:
        try:
            r = httpx.get(
                f"{self.base_url}/apps",
                params={"limit": limit},
                timeout=20,
            )
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return []

    def get_app(self, bundle: str) -> Optional[Dict]:
        try:
            r = httpx.get(f"{self.base_url}/apps/{bundle}", timeout=20)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return None

    def get_featured(self) -> List[Dict]:
        try:
            r = httpx.get(f"{self.base_url}/featured", timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return []

    def search(self, query: str) -> List[Dict]:
        try:
            r = httpx.get(
                f"{self.base_url}/search",
                params={"q": query},
                timeout=15,
            )
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return []

    # ── Download / Publish ────────────────────────────────────────────────────

    def download(self, bundle: str, output_path: Path) -> bool:
        try:
            with httpx.stream(
                "GET", f"{self.base_url}/download/{bundle}", timeout=60
            ) as r:
                if r.status_code == 200:
                    with open(output_path, "wb") as f:
                        for chunk in r.iter_bytes(chunk_size=8192):
                            f.write(chunk)
                    return True
        except Exception:
            pass
        return False

    def publish(self, file_path: Path) -> tuple[bool, str]:
        """Publie une application. Retourne (success, message)."""
        if not self.token:
            return False, "Non authentifié"
        try:
            with open(file_path, "rb") as f:
                r = httpx.post(
                    f"{self.base_url}/publish",
                    files={"file": (file_path.name, f, "application/octet-stream")},
                    data={"token": self.token},
                    timeout=60,
                )
            if r.status_code == 200:
                data = r.json()
                return True, data.get("message", "Publié avec succès")
            try:
                detail = r.json().get("detail", r.text[:200])
            except Exception:
                detail = r.text[:200]
            return False, detail
        except Exception as e:
            return False, str(e)

    # ── Social ────────────────────────────────────────────────────────────────

    def rate(self, bundle: str, rating: int, comment: str = None) -> tuple[bool, str]:
        """Note une application. Retourne (success, message)."""
        if not self.token:
            return False, "Non authentifié"
        try:
            data = {"token": self.token, "rating": rating}
            if comment:
                data["comment"] = comment
            r = httpx.post(
                f"{self.base_url}/rate/{bundle}",
                data=data,
                timeout=15,
            )
            if r.status_code == 200:
                return True, "Note envoyée !"
            try:
                detail = r.json().get("detail", r.text[:200])
            except Exception:
                detail = r.text[:200]
            return False, detail
        except Exception as e:
            return False, str(e)

    def comment(self, bundle: str, content: str) -> tuple[bool, str]:
        if not self.token:
            return False, "Non authentifié"
        try:
            r = httpx.post(
                f"{self.base_url}/comment/{bundle}",
                json={"content": content},
                headers=self._headers(),
                timeout=15,
            )
            if r.status_code == 200:
                return True, "Commentaire ajouté"
            try:
                detail = r.json().get("detail", r.text[:200])
            except Exception:
                detail = r.text[:200]
            return False, detail
        except Exception as e:
            return False, str(e)

    def get_updates(self) -> List[Dict]:
        try:
            r = httpx.get(f"{self.base_url}/updates", timeout=15)
            if r.status_code == 200:
                return r.json()
        except Exception:
            pass
        return []

    # ── Status ────────────────────────────────────────────────────────────────

    def ping(self) -> bool:
        try:
            r = httpx.get(f"{self.base_url}/", timeout=5)
            return r.status_code == 200
        except Exception:
            return False
