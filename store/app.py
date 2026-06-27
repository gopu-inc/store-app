# app.py
"""Application Textual StoreApp.TUI"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.containers import Container

from screens.login import LoginScreen
from screens.home import HomeScreen
from screens.browse import BrowseScreen
from screens.detail import DetailScreen
from screens.publish import PublishScreen

from api import StoreAPI
from config import Config

class StoreApp(App):
    """Application StoreApp.TUI"""
    
    CSS_PATH = "styles/app.tcss"
    TITLE = "StoreApp.TUI"
    
    BINDINGS = [
        ("ctrl+q", "quit", "Quitter"),
        ("ctrl+h", "home", "Accueil"),
        ("ctrl+b", "browse", "Parcourir"),
        ("ctrl+p", "publish", "Publier"),
    ]
    
    SCREENS = {
        "login": LoginScreen,
        "home": HomeScreen,
        "browse": BrowseScreen,
        "detail": DetailScreen,
        "publish": PublishScreen,
    }
    
    def __init__(self):
        super().__init__()
        self.api = StoreAPI(Config.API_BASE_URL)
        self.current_app = None
    
    def on_mount(self) -> None:
        """Montage de l'application"""
        # Vérifier si déjà connecté (token en cache)
        if self.api.token:
            self.push_screen("home")
        else:
            self.push_screen("login")
    
    def compose(self) -> ComposeResult:
        """Composition de l'application"""
        yield Header(show_clock=True)
        yield Container(id="main-container")
        yield Footer()
    
    def action_home(self) -> None:
        """Action: Accueil"""
        self.push_screen("home")
    
    def action_browse(self) -> None:
        """Action: Parcourir"""
        self.push_screen("browse")
    
    def action_publish(self) -> None:
        """Action: Publier"""
        self.push_screen("publish")
