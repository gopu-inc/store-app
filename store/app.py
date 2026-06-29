# app.py
"""StoreApp.TUI — Application principale Textual v2.0"""

from textual.app import App, ComposeResult
from textual.widgets import Header, Footer
from textual.binding import Binding

from screens.login import LoginScreen
from screens.home import HomeScreen
from screens.browse import BrowseScreen
from screens.detail import DetailScreen
from screens.publish import PublishScreen

from api import StoreAPI
from config import Config


class StoreApp(App):
    """StoreApp.TUI — Le Play Store du Terminal"""

    CSS_PATH = "styles/app.tcss"
    TITLE = "StoreApp.TUI"
    SUB_TITLE = "Le Play Store du Terminal"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quitter", show=True),
        Binding("ctrl+h", "go_home", "Accueil", show=True),
        Binding("ctrl+b", "go_browse", "Parcourir", show=True),
        Binding("ctrl+p", "go_publish", "Publier", show=True),
        Binding("ctrl+l", "go_login", "Compte", show=False),
        Binding("escape", "pop_screen", "Retour", show=False),
        Binding("f5", "refresh", "Rafraîchir", show=False),
    ]

    SCREENS = {
        "login": LoginScreen,
        "home": HomeScreen,
        "browse": BrowseScreen,
        "publish": PublishScreen,
    }

    def __init__(self):
        super().__init__()
        self.api = StoreAPI(Config.API_BASE_URL)
        self.current_app: str | None = None  # bundle courant pour DetailScreen

    def on_mount(self) -> None:
        if self.api.token:
            self.push_screen("home")
        else:
            self.push_screen("login")

    # ── Actions ───────────────────────────────────────────────────────────────

    def action_go_home(self) -> None:
        self.push_screen("home")

    def action_go_browse(self) -> None:
        self.push_screen("browse")

    def action_go_publish(self) -> None:
        if not self.api.token:
            self.notify("Connectez-vous pour publier", severity="warning")
            return
        self.push_screen("publish")

    def action_go_login(self) -> None:
        self.push_screen("login")

    def action_pop_screen(self) -> None:
        if len(self.screen_stack) > 1:
            self.pop_screen()

    def action_refresh(self) -> None:
        try:
            self.screen.on_mount()  # type: ignore
        except Exception:
            pass

    def open_detail(self, bundle: str) -> None:
        """Ouvre le détail d'une application."""
        self.current_app = bundle
        self.push_screen(DetailScreen())
