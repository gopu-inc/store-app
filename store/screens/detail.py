# screens/detail.py
"""Détail d'une application avec métadonnées complètes"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Static, Button, Input
from textual.containers import Horizontal, Vertical, Container, Grid
from textual import events
from pathlib import Path

from store.widgets.rating_dialog import RatingDialog


class DetailScreen(Screen):
    """Écran de détail d'une application"""
    
    CSS = """
    DetailScreen {
        background: $surface;
    }
    
    #detail-header {
        height: 3;
        border-bottom: solid $primary;
        padding: 0 1;
        background: $panel;
    }
    
    #detail-content {
        height: 1fr;
        margin: 1;
        padding: 1;
        border: solid $secondary;
        overflow-y: auto;
    }
    
    #detail-content > Label {
        padding: 1;
    }
    
    #metadata-grid {
        grid-size: 2;
        grid-gutter: 1 1;
        margin: 1 0;
        border: solid $panel;
        padding: 1;
    }
    
    #metadata-grid > Label {
        padding: 1;
    }
    
    #detail-actions {
        height: 3;
        padding: 0 1;
    }
    
    #detail-actions > Button {
        margin: 0 1;
        width: 15;
    }
    
    .status {
        color: $text-muted;
        text-align: right;
        padding: 0 1;
    }
    
    .env-badge {
        background: $primary-darken-1;
        padding: 0 2;
        border: solid $primary;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="detail-header"):
            yield Label("📦 Détail de l'application")
            yield Label("", id="status", classes="status")
        
        with Container(id="detail-content"):
            yield Label("", id="app-name")
            yield Label("", id="app-version")
            yield Label("", id="app-author")
            yield Label("", id="app-rating")
            yield Label("", id="app-downloads")
            yield Label("", id="app-env", classes="env-badge")
            
            with Grid(id="metadata-grid"):
                yield Label("📋 Métadonnées", classes="subtitle")
                yield Label("")
                yield Label("📦 Bundle:")
                yield Label("", id="app-bundle")
                yield Label("📝 Description:")
                yield Label("", id="app-description")
                yield Label("📂 App Path:")
                yield Label("", id="app-path")
                yield Label("🔒 Lock Cache:")
                yield Label("", id="app-lock")
                yield Label("📦 Dépendances:")
                yield Label("", id="app-deps")
                yield Label("🔧 Permissions:")
                yield Label("", id="app-perms")
            
            yield Label("---", id="readme-sep")
            yield Static("", id="app-readme")
            yield Label("", id="user-rating")
        
        with Horizontal(id="detail-actions"):
            yield Button("⬇️ Télécharger", id="download-btn", variant="primary")
            yield Button("⭐ Noter", id="rate-btn", variant="success")
            yield Button("🔙 Retour", id="back-btn", variant="warning")
    
    def on_mount(self) -> None:
        self.load_detail()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.app.pop_screen()
        elif event.button.id == "download-btn":
            self.download_app()
        elif event.button.id == "rate-btn":
            self.show_rating_dialog()
    
    def load_detail(self) -> None:
        """Charge les détails de l'application"""
        bundle = self.app.current_app
        if not bundle:
            return
        
        self.query_one("#status").update("🔄 Chargement...")
        
        try:
            data = self.app.api.get_app(bundle)
            if data:
                metadata = data.get('metadata', {})
                manifest = data.get('manifest', {})
                
                # Informations principales
                self.query_one("#app-name").update(f"📦 {metadata.get('name', 'Inconnu')}")
                self.query_one("#app-version").update(f"Version: {metadata.get('version', '')}")
                self.query_one("#app-author").update(f"Auteur: {metadata.get('author', '')}")
                
                # Note
                rating = metadata.get('rating', 0)
                rating_count = metadata.get('rating_count', 0)
                stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
                self.query_one("#app-rating").update(f"{stars} {rating} ({rating_count} notes)")
                
                # Téléchargements
                self.query_one("#app-downloads").update(f"👥 {metadata.get('downloads', 0)} téléchargements")
                
                # Environnement
                env = manifest.get('environnement', 'python')
                self.query_one("#app-env").update(f"🐍 {env}")
                
                # Métadonnées détaillées
                self.query_one("#app-bundle").update(metadata.get('bundle', ''))
                self.query_one("#app-description").update(metadata.get('description', '')[:100])
                self.query_one("#app-path").update(manifest.get('app-path', '~/'))
                self.query_one("#app-lock").update(manifest.get('lock-cash-path', './cache/'))
                
                # Dépendances
                deps = manifest.get('dependencies', [])
                self.query_one("#app-deps").update(', '.join(deps[:3]) + ('...' if len(deps) > 3 else ''))
                
                # Permissions
                perms = manifest.get('permissions', [])
                self.query_one("#app-perms").update(', '.join(perms[:3]) + ('...' if len(perms) > 3 else ''))
                
                # Afficher la note de l'utilisateur si connecté
                user_rating = self.get_user_rating(data.get('ratings', []))
                if user_rating:
                    self.query_one("#user-rating").update(f"✅ Vous avez noté: {'⭐' * user_rating}")
                
                # README
                readme = data.get('readme', '')
                if readme:
                    self.query_one("#app-readme").update(readme[:500] + "..." if len(readme) > 500 else readme)
                else:
                    self.query_one("#app-readme").update("Aucun README disponible")
                
                self.query_one("#status").update("✅ Chargé")
            else:
                self.query_one("#status").update("❌ Application non trouvée")
        except Exception as e:
            self.query_one("#status").update(f"❌ Erreur: {e}")
    
    def get_user_rating(self, ratings: list) -> int:
        """Récupère la note de l'utilisateur connecté"""
        if not self.app.api.token:
            return 0
        
        username = self.app.api.username
        for r in ratings:
            if r.get('username') == username:
                return r.get('rating', 0)
        return 0
    
    def download_app(self) -> None:
        """Télécharge l'application"""
        bundle = self.app.current_app
        if not bundle:
            return
        
        self.query_one("#status").update("⬇️ Téléchargement...")
        
        try:
            output_path = Path.home() / "Downloads" / f"{bundle}.tpkg"
            output_path.parent.mkdir(exist_ok=True)
            
            if self.app.api.download(bundle, output_path):
                self.query_one("#status").update(f"✅ Téléchargé: {output_path}")
            else:
                self.query_one("#status").update("❌ Échec du téléchargement")
        except Exception as e:
            self.query_one("#status").update(f"❌ Erreur: {e}")
    
    def show_rating_dialog(self) -> None:
        """Affiche la boîte de dialogue de notation"""
        if not self.app.api.token:
            self.query_one("#status").update("⚠️ Connectez-vous pour noter")
            return
        
        bundle = self.app.current_app
        if not bundle:
            return
        
        metadata = self.app.api.get_app(bundle)
        if not metadata:
            return
        
        app_name = metadata.get('metadata', {}).get('name', 'Application')
        
        def on_rating_dismissed(result):
            if result:
                self.query_one("#status").update(f"✅ Note envoyée !")
                self.load_detail()
            else:
                self.query_one("#status").update("❌ Notation annulée")
        
        self.app.push_screen(RatingDialog(bundle, app_name), on_rating_dismissed)
