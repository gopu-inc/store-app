# screens/detail.py
"""Détail d'une application"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Static, Button, Input
from textual.containers import Horizontal, Vertical, Container
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
    
    #detail-actions {
        height: 3;
        padding: 0 1;
    }
    
    #detail-actions > Button {
        margin: 0 1;
        width: 15;
    }
    
    #detail-actions > Input {
        width: 10;
        margin: 0 1;
    }
    
    .status {
        color: $text-muted;
        text-align: right;
        padding: 0 1;
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
            yield Label("", id="app-description")
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
                self.query_one("#app-name").update(f"📦 {metadata.get('name', 'Inconnu')}")
                self.query_one("#app-version").update(f"Version: {metadata.get('version', '')}")
                self.query_one("#app-author").update(f"Auteur: {metadata.get('author', '')}")
                
                rating = metadata.get('rating', 0)
                rating_count = metadata.get('rating_count', 0)
                stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
                self.query_one("#app-rating").update(f"{stars} {rating} ({rating_count} notes)")
                
                self.query_one("#app-downloads").update(f"👥 {metadata.get('downloads', 0)} téléchargements")
                self.query_one("#app-description").update(f"📝 {metadata.get('description', '')}")
                
                # Afficher la note de l'utilisateur si connecté
                user_rating = self.get_user_rating(data.get('ratings', []))
                if user_rating:
                    self.query_one("#user-rating").update(f"✅ Vous avez noté: {'⭐' * user_rating}")
                
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
                self.load_detail()  # Recharger les détails
            else:
                self.query_one("#status").update("❌ Notation annulée")
        
        self.app.push_screen(RatingDialog(bundle, app_name), on_rating_dismissed)
