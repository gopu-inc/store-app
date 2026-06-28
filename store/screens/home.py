# screens/home.py
"""Écran d'accueil"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Static, Button, ListView, ListItem, LoadingIndicator
from textual.containers import Horizontal, Vertical, Grid, Container
from textual.reactive import reactive

class AppCard(ListItem):
    """Carte d'application dans la liste"""
    
    def __init__(self, app_data):
        super().__init__()
        self.app_data = app_data
    
    def render(self):
        name = self.app_data.get('name', 'Inconnu')
        version = self.app_data.get('version', '')
        author = self.app_data.get('author', '')
        rating = self.app_data.get('rating', 0)
        downloads = self.app_data.get('downloads', 0)
        stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
        
        return f"📦 {name} v{version}\n  ✍️ {author}  {stars} {rating}  👥 {downloads}"

class HomeScreen(Screen):
    """Écran d'accueil"""
    
    CSS = """
    HomeScreen {
        background: $surface;
    }
    
    #header {
        height: 3;
        border-bottom: solid $primary;
        padding: 0 1;
        background: $panel;
    }
    
    #featured-grid {
        grid-size: 3;
        grid-gutter: 1 1;
        margin: 1 1;
        height: 8;
    }
    
    #featured-grid > Static {
        border: solid $secondary;
        padding: 1;
        background: $panel;
        text-align: center;
    }
    
    #app-list {
        height: 1fr;
        margin: 1;
        border: solid $secondary;
    }
    
    #app-list ListItem {
        padding: 1;
        border-bottom: solid $panel;
    }
    
    #app-list ListItem:hover {
        background: $primary-darken-1;
    }
    
    #actions {
        height: 3;
        padding: 0 1;
    }
    
    #actions > Button {
        margin: 0 1;
        width: 20;
    }
    
    .status {
        color: $text-muted;
        text-align: right;
        padding: 0 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="header"):
            yield Label("📦 StoreApp.TUI")
            yield Label("", id="status", classes="status")
        
        yield Label("🔥 Applications en vedette", classes="subtitle")
        with Grid(id="featured-grid"):
            for i in range(3):
                yield Static(f"📦 App {i+1}\nChargement...", id=f"featured-{i}")
        
        yield Label("📋 Toutes les applications", classes="subtitle")
        with Container(id="app-list"):
            yield ListView(id="apps-list")
        
        with Horizontal(id="actions"):
            yield Button("🔍 Parcourir", id="browse-btn", variant="primary")
            yield Button("📤 Publier", id="publish-btn", variant="success")
            yield Button("🚪 Déconnexion", id="logout-btn", variant="warning")
    
    def on_mount(self) -> None:
        self.load_data()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "browse-btn":
            self.app.push_screen("browse")
        elif event.button.id == "publish-btn":
            self.app.push_screen("publish")
        elif event.button.id == "logout-btn":
            self.app.api.token = None
            self.app.api.username = None
            self.app.push_screen("login")
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if hasattr(item, 'app_data'):
            bundle = item.app_data.get('bundle')
            self.app.current_app = bundle
            self.app.push_screen("detail")
    
    def load_data(self) -> None:
        """Charge les données"""
        self.load_featured()
        self.load_apps()
    
    def load_featured(self) -> None:
        """Charge les applications en vedette"""
        try:
            featured = self.app.api.get_featured()
            for i, app in enumerate(featured[:3]):
                widget = self.query_one(f"#featured-{i}")
                name = app.get('name', 'App')
                rating = app.get('rating', 0)
                env = app.get('environnement', 'python')
                widget.update(f"📦 {name}\n⭐ {rating}  🐍 {env}")
       
        except:  
            pass
    
    def load_apps(self) -> None:
        """Charge la liste des applications"""
        self.query_one("#apps-list").clear()
        self.query_one("#status").update("🔄 Chargement...")
        
        try:
            apps = self.app.api.get_apps(50)
            if apps:
                list_view = self.query_one("#apps-list")
                for app in apps[:20]:
                    list_view.append(AppCard(app))
                self.query_one("#status").update(f"✅ {len(apps)} applications")
            else:
                self.query_one("#status").update("📭 Aucune application")
        except Exception as e:
            self.query_one("#status").update(f"❌ Erreur: {e}")
