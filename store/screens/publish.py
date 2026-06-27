# screens/publish.py
"""Publier une application"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Static, Button, Input
from textual.containers import Horizontal, Vertical, Container
from pathlib import Path

class PublishScreen(Screen):
    """Écran de publication d'application"""
    
    CSS = """
    PublishScreen {
        background: $surface;
    }
    
    #publish-header {
        height: 3;
        border-bottom: solid $primary;
        padding: 0 1;
        background: $panel;
    }
    
    #publish-content {
        height: 1fr;
        margin: 1;
        padding: 2;
        border: solid $secondary;
    }
    
    #publish-content > Label {
        padding: 1;
    }
    
    #publish-content > Input {
        margin: 1;
    }
    
    #publish-actions {
        height: 3;
        padding: 0 1;
    }
    
    #publish-actions > Button {
        margin: 0 1;
        width: 15;
    }
    
    .status {
        color: $text-muted;
        text-align: right;
        padding: 0 1;
    }
    
    #file-info {
        color: $success;
        padding: 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="publish-header"):
            yield Label("📤 Publier une application")
            yield Label("", id="status", classes="status")
        
        with Container(id="publish-content"):
            yield Label("📦 Chemin du package (.tpkg ou .tar.gz):")
            yield Input(placeholder="/chemin/vers/monapp.tpkg", id="package-path")
            yield Label("", id="file-info")
            yield Button("🚀 Publier", id="publish-btn", variant="primary")
        
        with Horizontal(id="publish-actions"):
            yield Button("🏠 Accueil", id="home-btn", variant="primary")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "publish-btn":
            self.publish_app()
        elif event.button.id == "home-btn":
            self.app.push_screen("home")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "package-path":
            self.publish_app()
    
    def publish_app(self) -> None:
        """Publie l'application"""
        path = self.query_one("#package-path").value.strip()
        if not path:
            self.query_one("#status").update("⚠️ Veuillez spécifier un chemin")
            return
        
        file_path = Path(path)
        if not file_path.exists():
            self.query_one("#status").update(f"❌ Fichier introuvable: {path}")
            return
        
        if not (file_path.suffix in ['.tpkg', '.gz'] or str(file_path).endswith('.tar.gz')):
            self.query_one("#status").update("❌ Format non supporté (.tpkg ou .tar.gz)")
            return
        
        self.query_one("#status").update("📤 Publication en cours...")
        
        try:
            if self.app.api.publish(file_path):
                self.query_one("#status").update("✅ Application publiée avec succès !")
                self.query_one("#package-path").value = ""
                self.query_one("#file-info").update(f"📦 {file_path.name} publié")
            else:
                self.query_one("#status").update("❌ Échec de la publication")
        except Exception as e:
            self.query_one("#status").update(f"❌ Erreur: {e}")
