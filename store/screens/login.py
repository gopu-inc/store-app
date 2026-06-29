# screens/login.py
"""Écran de connexion — ASCII art + animation"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Input, Button, Static
from textual.containers import Container, Vertical, Horizontal
from textual import work
from textual import events

BANNER = (
    " _____ ___  ___  ____  _____   _   ____  ____\n"
    r"/ ____|  _||   ||  _ \|  ___| / \ |  _ \|  _ \\" "\n"
    r"\___ \ | |_|   || |_) |  _|  / _ \| |_) | |_) |" "\n"
    r" ___) ||  _|   ||  _ <| |___/ ___ \  __/|  __/" "\n"
    r"|____/ |_| \___||_| \_\|____/_/   \_\_|  |_|"
)

TAGLINE = "✦  Le Play Store du Terminal  ✦"


class LoginScreen(Screen):
    """Écran de connexion StoreApp.TUI"""

    BINDINGS = [
        ("tab", "focus_next", ""),
        ("shift+tab", "focus_previous", ""),
    ]

    def compose(self) -> ComposeResult:
        with Container(id="login-panel"):
            yield Static(BANNER.strip(), id="login-banner")
            yield Static(TAGLINE, id="login-tagline")
            yield Static("─" * 50, id="login-sep")
            yield Static("", id="login-error")
            yield Static("", id="login-status")
            yield Input(placeholder="👤  Nom d'utilisateur", id="username")
            yield Input(placeholder="🔒  Mot de passe", id="password", password=True)
            with Horizontal(id="login-btns"):
                yield Button("  Connexion", id="login-btn", variant="primary")
                yield Button("  Inscription", id="signup-btn", classes="ghost")
            yield Static(
                f"v{__import__('config').Config.VERSION}  •  Powered by GitHub Storage",
                id="login-version",
            )

    def on_mount(self) -> None:
        self.query_one("#username").focus()

    # ── Events ────────────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "username":
            self.query_one("#password").focus()
        elif event.input.id == "password":
            self._do_login()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-btn":
            self._do_login()
        elif event.button.id == "signup-btn":
            self._do_signup()

    # ── Auth workers ──────────────────────────────────────────────────────────

    def _do_login(self) -> None:
        username = self.query_one("#username").value.strip()
        password = self.query_one("#password").value
        if not username or not password:
            self._set_error("⚠  Veuillez remplir tous les champs")
            return
        self._set_status("⏳  Connexion en cours…")
        self._login_worker(username, password)

    def _do_signup(self) -> None:
        username = self.query_one("#username").value.strip()
        password = self.query_one("#password").value
        if not username or not password:
            self._set_error("⚠  Veuillez remplir tous les champs")
            return
        if len(password) < 6:
            self._set_error("⚠  Mot de passe trop court (min 6 caractères)")
            return
        self._set_status("⏳  Inscription en cours…")
        self._signup_worker(username, password)

    @work(thread=True)
    def _login_worker(self, username: str, password: str) -> None:
        ok = self.app.api.login(username, password)
        if ok:
            self.app.call_from_thread(self._on_login_success)
        else:
            self.app.call_from_thread(
                self._set_error, "✗  Identifiants incorrects"
            )

    @work(thread=True)
    def _signup_worker(self, username: str, password: str) -> None:
        ok = self.app.api.signup(username, password)
        if ok:
            self.app.call_from_thread(
                self._set_status,
                "✓  Compte créé ! Vous pouvez maintenant vous connecter.",
            )
            self.app.call_from_thread(lambda: self.query_one("#password", Input).clear())
        else:
            self.app.call_from_thread(
                self._set_error, "✗  Nom d'utilisateur déjà pris ou erreur serveur"
            )

    def _on_login_success(self) -> None:
        self._set_status(f"✓  Bienvenue {self.app.api.username} !")
        self.app.push_screen("home")

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _set_error(self, msg: str) -> None:
        self.query_one("#login-error").update(msg)
        self.query_one("#login-status").update("")

    def _set_status(self, msg: str) -> None:
        self.query_one("#login-status").update(msg)
        self.query_one("#login-error").update("")
