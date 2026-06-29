# server.py
"""StoreApp.TUI Backend — copie de référence locale (déployé sur Render)
   Source : https://storeapp-7mbo.onrender.com
   Pour lancer localement :
       pip install fastapi uvicorn python-jose[cryptography] pillow httpx python-multipart
       python server.py
"""

import os
import json
import hashlib
import hmac
import base64
import tarfile
import io
import uuid
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pathlib import Path
from PIL import Image

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel, Field
import httpx
from jose import JWTError, jwt
import uvicorn


# ==================== CONFIGURATION ====================

class Config:
    APP_NAME = "StoreApp.TUI"
    VERSION = "2.0.0"

    # GitHub
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    GITHUB_REPO = os.getenv("GITHUB_REPO", "gopu-inc/Storage")
    GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")
    GITHUB_API_URL = "https://api.github.com"

    # JWT
    SECRET_KEY = os.getenv("SECRET_KEY", "storeapp_secret_key_change_me")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 jours

    # Upload
    MAX_PACKAGE_SIZE = 50 * 1024 * 1024  # 50 MB
    ALLOWED_EXTENSIONS = [".tpkg", ".tar.gz", ".gz"]

    # Images
    MAX_ICON_SIZE = 1024 * 1024        # 1 MB
    MAX_SCREENSHOT_SIZE = 5 * 1024 * 1024  # 5 MB
    ICON_SIZE = (200, 200)
    SCREENSHOT_SIZE = (800, 400)

    @classmethod
    def validate(cls):
        if not cls.GITHUB_TOKEN:
            print("⚠️  GITHUB_TOKEN non configuré")
        if cls.SECRET_KEY == "storeapp_secret_key_change_me":
            print("⚠️  SECRET_KEY par défaut — changez-la en production")


Config.validate()


# ==================== MODÈLES ====================

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class RatingCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)


# ==================== SÉCURITÉ ====================

class SecurityUtils:
    @staticmethod
    def hash_password(password: str) -> str:
        salt = os.urandom(32)
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
        return base64.b64encode(salt + hashed).decode()

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        try:
            data = base64.b64decode(hashed)
            salt = data[:32]
            stored = data[32:]
            computed = hashlib.pbkdf2_hmac("sha256", plain.encode(), salt, 100000)
            return hmac.compare_digest(stored, computed)
        except Exception:
            return False

    @staticmethod
    def create_token(username: str) -> str:
        payload = {
            "sub": username,
            "exp": datetime.utcnow() + timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        return jwt.encode(payload, Config.SECRET_KEY, algorithm=Config.ALGORITHM)

    @staticmethod
    def decode_token(token: str) -> dict:
        try:
            return jwt.decode(token, Config.SECRET_KEY, algorithms=[Config.ALGORITHM])
        except JWTError:
            raise HTTPException(status_code=401, detail="Token invalide")


# ==================== STOCKAGE GITHUB ====================

class GitHubStorage:
    def __init__(self):
        self.headers = {
            "Authorization": f"token {Config.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        self.base_url = f"{Config.GITHUB_API_URL}/repos/{Config.GITHUB_REPO}/contents"

    async def _request(self, method: str, path: str, data: Dict = None) -> Dict:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = self.headers.copy()
        if data:
            headers["Content-Type"] = "application/json"
        async with httpx.AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "PUT":
                response = await client.put(url, json=data, headers=headers)
            elif method == "DELETE":
                response = await client.delete(url, headers=headers)
            else:
                raise ValueError(f"Méthode non supportée: {method}")
            if response.status_code in [200, 201]:
                return response.json()
            elif response.status_code == 404:
                return None
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"GitHub API error: {response.text[:200]}",
                )

    async def _create_file(self, path: str, content: bytes, message: str) -> Dict:
        existing = await self._request("GET", path)
        data = {
            "message": message,
            "content": base64.b64encode(content).decode(),
            "branch": Config.GITHUB_BRANCH,
        }
        if existing and "sha" in existing:
            data["sha"] = existing["sha"]
        return await self._request("PUT", path, data)

    async def _get_file(self, path: str) -> Optional[bytes]:
        result = await self._request("GET", path)
        if result and "content" in result:
            return base64.b64decode(result["content"])
        return None

    async def _get_json(self, path: str) -> Optional[Dict]:
        content = await self._get_file(path)
        if content:
            try:
                return json.loads(content)
            except Exception:
                return None
        return None

    async def save_user(self, username: str, password_hash: str, email: str = None) -> Dict:
        user_data = {
            "username": username,
            "password": password_hash,
            "email": email,
            "created_at": datetime.utcnow().isoformat(),
            "apps_published": [],
            "apps_installed": [],
        }
        await self._create_file(
            f"users/{username}.json",
            json.dumps(user_data, indent=2).encode(),
            f"Create user {username}",
        )
        return user_data

    async def get_user(self, username: str) -> Optional[Dict]:
        return await self._get_json(f"users/{username}.json")

    async def save_app(self, app_data: Dict, package_bytes: bytes,
                       icon_bytes: bytes = None, screenshots: List[bytes] = None) -> Dict:
        bundle = app_data.get("bundle")
        if not bundle:
            raise HTTPException(status_code=400, detail="Bundle requis")
        app_path = f"apps/{bundle}"
        files = {
            f"{app_path}/package.tpkg": package_bytes,
            f"{app_path}/manifest.txml": app_data.get("manifest_xml", "").encode(),
            f"{app_path}/README.md": app_data.get("readme", "# Application").encode(),
        }
        if icon_bytes:
            files[f"{app_path}/icon.png"] = icon_bytes
        if screenshots:
            for i, screenshot in enumerate(screenshots[:5]):
                files[f"{app_path}/screenshots/screenshot_{i+1}.png"] = screenshot
        metadata = {
            "bundle": bundle,
            "name": app_data.get("name", ""),
            "version": app_data.get("version", "1.0.0"),
            "author": app_data.get("author", ""),
            "description": app_data.get("description", ""),
            "entrypoint": app_data.get("entrypoint", ""),
            "license": app_data.get("license", ""),
            "homepage": app_data.get("homepage", ""),
            "environnement": app_data.get("environnement", "python"),
            "gestionnaire": app_data.get("gestionnaire", "pip install"),
            "app_path": app_data.get("app_path", "~/"),
            "lock_cache_path": app_data.get("lock_cache_path", "./cache/"),
            "permissions": app_data.get("permissions", []),
            "dependencies": app_data.get("dependencies", []),
            "has_icon": bool(icon_bytes),
            "has_screenshots": bool(screenshots),
            "screenshot_count": len(screenshots) if screenshots else 0,
            "downloads": 0,
            "rating": 0.0,
            "rating_count": 0,
            "size": len(package_bytes),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
        files[f"{app_path}/metadata.json"] = json.dumps(metadata, indent=2).encode()
        for file_path, content in files.items():
            await self._create_file(
                file_path, content,
                f"Upload {bundle} v{app_data.get('version', '1.0.0')}",
            )
        user = await self.get_user(app_data.get("author", ""))
        if user:
            if "apps_published" not in user:
                user["apps_published"] = []
            if bundle not in user["apps_published"]:
                user["apps_published"].append(bundle)
            await self._create_file(
                f"users/{app_data.get('author', '')}.json",
                json.dumps(user, indent=2).encode(),
                f"Update user apps for {bundle}",
            )
        await self.update_app_index()
        return metadata

    async def update_app_index(self):
        apps_list = await self._request("GET", "apps")
        bundles = []
        if apps_list:
            for item in apps_list:
                if item.get("type") == "dir":
                    bundles.append(item.get("name"))
        index_data = {
            "apps": bundles,
            "updated_at": datetime.utcnow().isoformat(),
            "total": len(bundles),
        }
        await self._create_file(
            "index.json",
            json.dumps(index_data, indent=2).encode(),
            "Update app index",
        )

    async def get_app(self, bundle: str) -> Optional[Dict]:
        return await self._get_json(f"apps/{bundle}/metadata.json")

    async def get_app_package(self, bundle: str) -> Optional[bytes]:
        return await self._get_file(f"apps/{bundle}/package.tpkg")

    async def get_app_readme(self, bundle: str) -> Optional[str]:
        content = await self._get_file(f"apps/{bundle}/README.md")
        if content:
            return content.decode("utf-8", errors="ignore")
        return None

    async def get_app_icon(self, bundle: str) -> Optional[bytes]:
        return await self._get_file(f"apps/{bundle}/icon.png")

    async def get_app_screenshots(self, bundle: str) -> List[bytes]:
        screenshots = []
        for i in range(1, 6):
            content = await self._get_file(f"apps/{bundle}/screenshots/screenshot_{i}.png")
            if content:
                screenshots.append(content)
        return screenshots

    async def get_app_manifest(self, bundle: str) -> Optional[str]:
        content = await self._get_file(f"apps/{bundle}/manifest.txml")
        if content:
            return content.decode("utf-8", errors="ignore")
        return None

    async def list_apps(self, limit: int = 50) -> List[Dict]:
        apps = []
        try:
            index = await self._get_json("index.json")
            if index and "apps" in index:
                bundles = index["apps"]
            else:
                contents = await self._request("GET", "apps")
                if contents:
                    bundles = [item.get("name") for item in contents if item.get("type") == "dir"]
                else:
                    return []
            for bundle in bundles[:limit]:
                metadata = await self.get_app(bundle)
                if metadata:
                    apps.append(metadata)
        except Exception as e:
            print(f"Erreur list_apps: {e}")
        return apps

    async def search_apps(self, query: str) -> List[Dict]:
        all_apps = await self.list_apps(100)
        results = []
        query_lower = query.lower()
        for app in all_apps:
            name = app.get("name", "").lower()
            bundle = app.get("bundle", "").lower()
            author = app.get("author", "").lower()
            description = app.get("description", "").lower()
            if (query_lower in name or query_lower in bundle or
                    query_lower in author or query_lower in description):
                results.append(app)
        return results

    async def update_download_count(self, bundle: str) -> None:
        metadata = await self.get_app(bundle)
        if metadata:
            metadata["downloads"] = metadata.get("downloads", 0) + 1
            metadata["updated_at"] = datetime.utcnow().isoformat()
            await self._create_file(
                f"apps/{bundle}/metadata.json",
                json.dumps(metadata, indent=2).encode(),
                f"Update download count for {bundle}",
            )

    async def add_rating(self, bundle: str, rating: int, username: str,
                         comment: str = None) -> Dict:
        metadata = await self.get_app(bundle)
        if not metadata:
            raise HTTPException(status_code=404, detail="Application non trouvée")
        ratings_data = await self._get_json(f"ratings/{bundle}.json") or {"ratings": []}
        ratings_data["ratings"].append({
            "username": username,
            "rating": rating,
            "comment": comment,
            "created_at": datetime.utcnow().isoformat(),
        })
        await self._create_file(
            f"ratings/{bundle}.json",
            json.dumps(ratings_data, indent=2).encode(),
            f"Add rating for {bundle}",
        )
        total = sum(r["rating"] for r in ratings_data["ratings"])
        count = len(ratings_data["ratings"])
        avg = total / count if count > 0 else 0
        metadata["rating"] = round(avg, 1)
        metadata["rating_count"] = count
        metadata["updated_at"] = datetime.utcnow().isoformat()
        await self._create_file(
            f"apps/{bundle}/metadata.json",
            json.dumps(metadata, indent=2).encode(),
            f"Update rating for {bundle}",
        )
        return {"rating": avg, "count": count}

    async def get_ratings(self, bundle: str) -> List[Dict]:
        data = await self._get_json(f"ratings/{bundle}.json")
        return data.get("ratings", []) if data else []

    async def add_comment(self, bundle: str, username: str, content: str) -> Dict:
        comments_data = await self._get_json(f"comments/{bundle}.json") or {"comments": []}
        comments_data["comments"].append({
            "username": username,
            "content": content,
            "created_at": datetime.utcnow().isoformat(),
        })
        await self._create_file(
            f"comments/{bundle}.json",
            json.dumps(comments_data, indent=2).encode(),
            f"Add comment for {bundle}",
        )
        return {"status": "success"}

    async def get_comments(self, bundle: str) -> List[Dict]:
        data = await self._get_json(f"comments/{bundle}.json")
        return data.get("comments", []) if data else []


# ==================== TRAITEMENT D'IMAGES ====================

class ImageProcessor:
    @staticmethod
    def resize_image(image_bytes: bytes, size: tuple) -> bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.thumbnail(size, Image.Resampling.LANCZOS)
            if img.mode in ("RGBA", "LA", "P"):
                img = img.convert("RGB")
            output = io.BytesIO()
            img.save(output, format="PNG", optimize=True)
            return output.getvalue()
        except Exception as e:
            print(f"Erreur de redimensionnement: {e}")
            return image_bytes

    @staticmethod
    def is_valid_image(image_bytes: bytes) -> bool:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()
            return True
        except Exception:
            return False


# ==================== APPLICATION ====================

app = FastAPI(
    title="StoreApp.TUI",
    version="2.0.0",
    description="Store d'applications Terminal — Gestion complète des métadonnées",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage = GitHubStorage()


# ==================== ROUTES ====================

@app.get("/")
async def root():
    return {
        "name": Config.APP_NAME,
        "version": Config.VERSION,
        "status": "online",
        "storage": "GitHub",
        "features": ["icônes", "captures d'écran", "notes et commentaires",
                     "multi-environnements", "cache.lock"],
        "endpoints": [
            "/signup", "/login",
            "/apps", "/apps/{bundle}",
            "/search", "/download/{bundle}",
            "/rate/{bundle}", "/comment/{bundle}",
            "/publish", "/featured", "/updates",
            "/apps/{bundle}/icon", "/apps/{bundle}/screenshots",
        ],
    }


@app.post("/signup")
async def signup(user: UserCreate):
    existing = await storage.get_user(user.username)
    if existing:
        raise HTTPException(status_code=400, detail="Utilisateur déjà existant")
    password_hash = SecurityUtils.hash_password(user.password)
    await storage.save_user(user.username, password_hash, user.email)
    return {"status": "success", "message": "Utilisateur créé", "username": user.username}


@app.post("/login")
async def login(user: UserLogin):
    stored = await storage.get_user(user.username)
    if not stored:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    if not SecurityUtils.verify_password(user.password, stored["password"]):
        raise HTTPException(status_code=401, detail="Identifiants incorrects")
    token = SecurityUtils.create_token(user.username)
    return {"access_token": token, "token_type": "bearer", "username": user.username}


def parse_manifest(content: str) -> Dict:
    result = {"permissions": [], "dependencies": []}
    try:
        root = ET.fromstring(content)
        for child in root:
            tag = child.tag
            text = child.text.strip() if child.text else ""
            if tag == "permissions":
                result["permissions"] = [p.text.strip() for p in child if p.text]
            elif tag == "dependencies":
                result["dependencies"] = [d.text.strip() for d in child if d.text]
            elif tag == "compiler":
                compiler_data = {}
                for comp in child:
                    compiler_data[comp.tag] = comp.text.strip() if comp.text else ""
                result["compiler"] = compiler_data
            else:
                result[tag.replace("-", "_")] = text
    except Exception:
        patterns = {
            "name": r"<name>([^<]+)</name>",
            "version": r"<version>([^<]+)</version>",
            "author": r"<author>([^<]+)</author>",
            "bundle": r"<bundle>([^<]+)</bundle>",
            "description": r"<description>([^<]+)</description>",
            "entrypoint": r"<entrypoint>([^<]+)</entrypoint>",
            "license": r"<license>([^<]+)</license>",
            "homepage": r"<homepage>([^<]+)</homepage>",
            "environnement": r"<environnement>([^<]+)</environnement>",
            "gestionnaire": r"<gestionnaire>([^<]+)</gestionnaire>",
            "app_path": r"<app-path>([^<]+)</app-path>",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                result[key] = match.group(1)
        perm_matches = re.findall(r"<permission>([^<]+)</permission>", content)
        if perm_matches:
            result["permissions"] = perm_matches
        dep_matches = re.findall(r"<dependency>([^<]+)</dependency>", content)
        if dep_matches:
            result["dependencies"] = dep_matches
    return result


@app.post("/publish")
async def publish_app(file: UploadFile = File(...), token: str = Form(...)):
    try:
        payload = SecurityUtils.decode_token(token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token invalide")
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalide")

    if not (file.filename.endswith(".tpkg") or
            file.filename.endswith(".tar.gz") or
            file.filename.endswith(".gz")):
        raise HTTPException(status_code=400, detail="Format non supporté")

    contents = await file.read()
    if len(contents) > Config.MAX_PACKAGE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"Package trop volumineux. Maximum: {Config.MAX_PACKAGE_SIZE // (1024*1024)} MB",
        )

    app_data = {"author": username}
    readme_content = ""
    manifest_xml = ""
    icon_bytes = None
    screenshots = []

    try:
        with tarfile.open(fileobj=io.BytesIO(contents), mode="r:gz") as tar:
            if "manifest.txml" in tar.getnames():
                manifest_file = tar.extractfile("manifest.txml")
                if manifest_file:
                    manifest_content = manifest_file.read().decode("utf-8")
                    manifest_xml = manifest_content
                    app_data.update(parse_manifest(manifest_content))
            else:
                raise HTTPException(status_code=400, detail="manifest.txml introuvable")

            if "README.md" in tar.getnames():
                readme_file = tar.extractfile("README.md")
                if readme_file:
                    readme_content = readme_file.read().decode("utf-8", errors="ignore")

            if "icon.png" in tar.getnames():
                icon_file = tar.extractfile("icon.png")
                if icon_file:
                    icon_bytes = icon_file.read()
                    if ImageProcessor.is_valid_image(icon_bytes):
                        icon_bytes = ImageProcessor.resize_image(icon_bytes, Config.ICON_SIZE)

            screenshot_files = sorted([
                name for name in tar.getnames()
                if name.startswith("screenshots/") and
                name.endswith((".png", ".jpg", ".jpeg"))
            ])
            for s_name in screenshot_files[:5]:
                s_file = tar.extractfile(s_name)
                if s_file:
                    s_bytes = s_file.read()
                    if ImageProcessor.is_valid_image(s_bytes):
                        s_bytes = ImageProcessor.resize_image(s_bytes, Config.SCREENSHOT_SIZE)
                        screenshots.append(s_bytes)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Package invalide: {str(e)}")

    if not app_data.get("bundle"):
        raise HTTPException(status_code=400, detail="Bundle manquant dans manifest.txml")
    if not app_data.get("name"):
        raise HTTPException(status_code=400, detail="Nom manquant dans manifest.txml")

    app_data["manifest_xml"] = manifest_xml
    app_data["readme"] = readme_content
    metadata = await storage.save_app(app_data, contents, icon_bytes, screenshots)

    return {
        "status": "success",
        "message": f"Application {app_data.get('name')} publiée",
        "bundle": app_data.get("bundle"),
        "has_icon": bool(icon_bytes),
        "screenshot_count": len(screenshots),
    }


@app.get("/apps")
async def list_apps(limit: int = Query(50, ge=1, le=100)):
    return await storage.list_apps(limit)


@app.get("/apps/{bundle}")
async def get_app(bundle: str):
    metadata = await storage.get_app(bundle)
    if not metadata:
        raise HTTPException(status_code=404, detail="Application non trouvée")
    manifest_raw = await storage.get_app_manifest(bundle)
    manifest = parse_manifest(manifest_raw) if manifest_raw else {}
    readme = await storage.get_app_readme(bundle)
    ratings = await storage.get_ratings(bundle)
    comments = await storage.get_comments(bundle)
    icon = await storage.get_app_icon(bundle)
    screenshots = await storage.get_app_screenshots(bundle)
    return {
        "metadata": metadata,
        "manifest": manifest,
        "readme": readme,
        "ratings": ratings[-20:],
        "comments": comments[-20:],
        "has_icon": bool(icon),
        "screenshot_count": len(screenshots),
    }


@app.get("/apps/{bundle}/icon")
async def get_app_icon(bundle: str):
    icon = await storage.get_app_icon(bundle)
    if not icon:
        raise HTTPException(status_code=404, detail="Icône non trouvée")
    return StreamingResponse(
        io.BytesIO(icon),
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@app.get("/apps/{bundle}/screenshots")
async def get_app_screenshots(bundle: str):
    screenshots = await storage.get_app_screenshots(bundle)
    if not screenshots:
        raise HTTPException(status_code=404, detail="Aucune capture d'écran")
    return {"count": len(screenshots), "bundle": bundle}


@app.get("/apps/{bundle}/manifest")
async def get_app_manifest(bundle: str):
    raw = await storage.get_app_manifest(bundle)
    if not raw:
        raise HTTPException(status_code=404, detail="Manifest non trouvé")
    return parse_manifest(raw)


@app.get("/search")
async def search_apps(q: str = Query(..., min_length=1)):
    return await storage.search_apps(q)


@app.get("/download/{bundle}")
async def download_app(bundle: str):
    package = await storage.get_app_package(bundle)
    if not package:
        raise HTTPException(status_code=404, detail="Package non trouvé")
    await storage.update_download_count(bundle)
    return StreamingResponse(
        io.BytesIO(package),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={bundle}.tpkg"},
    )


@app.post("/rate/{bundle}")
async def rate_app(
    bundle: str,
    token: str = Form(...),
    rating: int = Form(...),
    comment: Optional[str] = Form(None),
):
    try:
        payload = SecurityUtils.decode_token(token)
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Token invalide")
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalide")
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="Note entre 1 et 5")
    result = await storage.add_rating(bundle, rating, username, comment)
    return {"status": "success", **result}


@app.post("/comment/{bundle}")
async def comment_app(bundle: str, body: CommentCreate,
                      authorization: Optional[str] = None):
    # Accept token from header
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Token requis")
    try:
        payload = SecurityUtils.decode_token(token)
        username = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalide")
    result = await storage.add_comment(bundle, username, body.content)
    return result


@app.get("/featured")
async def get_featured():
    apps = await storage.list_apps(20)
    apps.sort(key=lambda a: (a.get("downloads", 0), a.get("rating", 0)), reverse=True)
    return apps[:6]


@app.get("/updates")
async def get_updates():
    apps = await storage.list_apps(50)
    apps.sort(key=lambda a: a.get("updated_at", ""), reverse=True)
    return apps[:10]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
