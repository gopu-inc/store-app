# screens/browse.py
"""Parcourir les applications"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Static, Button, ListView, ListItem, Input
from textual.containers import Horizontal, Vertical, Container

class BrowseScreen(Screen):
    """Écran de parcours des applications"""
    
    CSS = """
    BrowseScreen {
        background: $surface;
    }
    
    #browse-header {
        height: 3;
        border-bottom: solid $primary;
        padding: 0 1;
        background: $panel;
    }
    
    #search-box {
        height: 3;
        margin: 1;
    }
    
    #search-box > Input {
        width: 1fr;
        margin: 0 1;
    }
    
    #search-box > Button {
        width: 15;
    }
    
    #browse-list {
        height: 1fr;
        margin: 1;
        border: solid $secondary;
    }
    
    #browse-list ListItem {
        padding: 1;
        border-bottom: solid $panel;
    }
    
    #browse-list ListItem:hover {
        background: $primary-darken-1;
    }
    
    #browse-actions {
        height: 3;
        padding: 0 1;
    }
    
    #browse-actions > Button {
        margin: 0 1;
        width: 15;
    }
    
    .status {
        color: $text-muted;
        text-align: right;
        padding: 0 1;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Horizontal(id="browse-header"):
            yield Label("🔍 Parcourir les applications")
            yield Label("", id="status", classes="status")
        
        with Horizontal(id="search-box"):
            yield Input(placeholder="🔎 Rechercher une application...", id="search-input")
            yield Button("🔍", id="search-btn", variant="primary")
        
        with Container(id="browse-list"):
            yield ListView(id="apps-list")
        
        with Horizontal(id="browse-actions"):
            yield Button("🔄 Rafraîchir", id="refresh-btn")
            yield Button("🏠 Accueil", id="home-btn", variant="primary")
    
    def on_mount(self) -> None:
        self.load_apps()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh-btn":
            self.load_apps()
        elif event.button.id == "search-btn":
            self.search_apps()
        elif event.button.id == "home-btn":
            self.app.push_screen("home")
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "search-input":
            self.search_apps()
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if hasattr(item, 'app_data'):
            bundle = item.app_data.get('bundle')
            self.app.current_app = bundle
            self.app.push_screen("detail")
    
    def load_apps(self) -> None:
        """Charge toutes les applications"""
        self.query_one("#apps-list").clear()
        self.query_one("#status").update("🔄 Chargement...")
        
        try:
            apps = self.app.api.get_apps(50)
            if apps:
                list_view = self.query_one("#apps-list")
                for app in apps:
                    item = self.create_app_item(app)
                    list_view.append(item)
                self.query_one("#status").update(f"✅ {len(apps)} applications")
            else:
                self.query_one("#status").update("📭 Aucune application")
        except Exception as e:
            self.query_one("#status").update(f"❌ Erreur: {e}")
    
    def search_apps(self) -> None:
        """Recherche des applications"""
        query = self.query_one("#search-input").value.strip()
        if not query or len(query) < 2:
            self.load_apps()
            return
        
        self.query_one("#apps-list").clear()
        self.query_one("#status").update(f"🔍 Recherche: {query}")
        
        try:
            results = self.app.api.search(query)
            if results:
                list_view = self.query_one("#apps-list")
                for app in results:
                    item = self.create_app_item(app)
                    list_view.append(item)
                self.query_one("#status").update(f"✅ {len(results)} résultats")
            else:
                self.query_one("#status").update("❌ Aucun résultat")
        except Exception as e:
            self.query_one("#status").update(f"❌ Erreur: {e}")
    
    def create_app_item(self, app_data):
        """Crée un élément de liste pour une application"""
        class AppListItem(ListItem):
            def __init__(self, data):
                super().__init__()
                self.app_data = data
            
            def render(self):
                name = self.app_data.get('name', 'Inconnu')
                version = self.app_data.get('version', '')
                author = self.app_data.get('author', '')
                rating = self.app_data.get('rating', 0)
                downloads = self.app_data.get('downloads', 0)
                stars = "⭐" * int(rating) + "☆" * (5 - int(rating))
                return f"📦 {name} v{version}\n  ✍️ {author}  {stars} {rating}  👥 {downloads}"
        
        return AppListItem(app_data)
