# screens/home.py
"""Écran d'accueil — DataTable + Featured cards"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Static, Button, DataTable
from textual.containers import Horizontal, Vertical, Container
from textual import work
from rich.text import Text


def _stars(rating: float) -> str:
    full = int(round(rating))
    return "★" * full + "☆" * (5 - full)


def _env_icon(env: str) -> str:
    icons = {
        "python": "🐍", "nodejs": "⬡", "node": "⬡",
        "go": "🐹", "rust": "🦀", "ruby": "💎",
        "java": "☕", "deno": "🦕", "bash": "🖥",
        "sh": "🖥", "php": "🐘", "lua": "🌙",
    }
    return icons.get(env.lower(), "📦")


class FeaturedCard(Static):
    def __init__(self, app_data: dict, idx: int):
        super().__init__(id=f"featured-{idx}")
        self._data = app_data

    def on_mount(self) -> None:
        d = self._data
        name = d.get("name", "???")
        env = d.get("environnement", "python")
        rating = d.get("rating", 0)
        downloads = d.get("downloads", 0)
        icon = _env_icon(env)
        t = Text()
        t.append(f"  {icon}  {name}\n", style="bold #58a6ff")
        t.append(f"  {_stars(rating)} {rating:.1f}", style="#d29922")
        t.append(f"   ↓ {downloads}", style="#8b949e")
        self.update(t)


class EmptyFeaturedCard(Static):
    def __init__(self, idx: int):
        super().__init__(id=f"featured-{idx}", classes="featured-card")

    def on_mount(self) -> None:
        t = Text()
        t.append("  ─────────────────\n", style="#30363d")
        t.append("  Aucune vedette", style="#30363d")
        self.update(t)


class HomeScreen(Screen):
    """Écran d'accueil"""

    COMPONENT_CLASSES = {"featured-card"}

    def compose(self) -> ComposeResult:
        # Top bar
        with Horizontal(id="home-topbar"):
            yield Static("  StoreApp.TUI", id="home-topbar-logo")
            yield Static("", id="home-topbar-user")

        # Featured section
        yield Static(" 🔥  Applications en vedette", id="featured-label")
        with Horizontal(id="featured-row"):
            for i in range(3):
                c = Static(f"  ─────────────────\n  Chargement…", id=f"featured-{i}", classes="featured-card")
                yield c

        # App list
        yield Static(" 📋  Toutes les applications", id="all-apps-label")
        yield DataTable(id="app-table", cursor_type="row")

        # Bottom actions
        with Horizontal(id="home-actions"):
            yield Button("🔍  Parcourir", id="browse-btn", variant="primary")
            yield Button("📤  Publier", id="publish-btn", classes="ghost")
            yield Button("🚪  Déconnexion", id="logout-btn", classes="ghost")
            yield Static("", id="home-status", classes="muted")

    def on_mount(self) -> None:
        table = self.query_one("#app-table", DataTable)
        table.add_column("  Application", key="name")
        table.add_column("Version", key="version")
        table.add_column("Auteur", key="author")
        table.add_column("Env", key="env")
        table.add_column("Note", key="rating")
        table.add_column("  Téléchargements", key="downloads")

        # Mettre à jour la barre utilisateur
        user = self.app.api.username
        if user:
            self.query_one("#home-topbar-user").update(f"👤  {user}  ")

        self._load_featured()
        self._load_apps()

    # ── Events ────────────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "browse-btn":
            self.app.push_screen("browse")
        elif event.button.id == "publish-btn":
            self.app.action_go_publish()
        elif event.button.id == "logout-btn":
            self.app.api.logout()
            self.app.push_screen("login")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one("#app-table", DataTable)
        row = table.get_row(event.row_key)
        # bundle stored as last meta item in row_key
        bundle = event.row_key.value  # type: ignore[attr-defined]
        if bundle:
            self.app.open_detail(bundle)

    # ── Workers ───────────────────────────────────────────────────────────────

    @work(thread=True)
    def _load_featured(self) -> None:
        try:
            featured = self.app.api.get_featured()
        except Exception:
            featured = []

        def update():
            for i in range(3):
                container = self.query_one(f"#featured-{i}", Static)
                if i < len(featured):
                    d = featured[i]
                    name = d.get("name", "???")
                    env = d.get("environnement", "python")
                    rating = d.get("rating", 0)
                    downloads = d.get("downloads", 0)
                    icon = _env_icon(env)
                    t = Text()
                    t.append(f"  {icon}  {name}\n", style="bold #58a6ff")
                    t.append(f"  {_stars(rating)} {rating:.1f}", style="#d29922")
                    t.append(f"   ↓ {downloads}", style="#8b949e")
                    container.update(t)
                else:
                    container.update(Text("  — vide —", style="#30363d"))

        self.app.call_from_thread(update)

    @work(thread=True)
    def _load_apps(self) -> None:
        self.app.call_from_thread(
            lambda: self.query_one("#home-status", Static).update("⏳  Chargement…")
        )
        try:
            apps = self.app.api.get_apps(50)
        except Exception as e:
            err = str(e)
            self.app.call_from_thread(
                lambda: self.query_one("#home-status", Static).update(f"✗  Erreur: {err}")
            )
            return

        def populate():
            table = self.query_one("#app-table", DataTable)
            table.clear()
            for a in apps:
                name = a.get("name", "—")
                version = a.get("version", "—")
                author = a.get("author", "—")
                env = a.get("environnement", "python")
                rating = a.get("rating", 0)
                downloads = a.get("downloads", 0)
                bundle = a.get("bundle", "")
                icon = _env_icon(env)

                name_text = Text()
                name_text.append("  ")
                name_text.append(name, style="bold #e6edf3")

                stars_text = Text()
                stars_text.append(_stars(rating), style="#d29922")
                stars_text.append(f" {rating:.1f}", style="#8b949e")

                dl_text = Text()
                dl_text.append(f"  ↓ {downloads}", style="#8b949e")

                env_text = Text()
                env_text.append(f"{icon} {env}", style="#58a6ff")

                table.add_row(
                    name_text,
                    Text(version, style="#3fb950"),
                    Text(author, style="#bc8cff"),
                    env_text,
                    stars_text,
                    dl_text,
                    key=bundle,
                )

            status = self.query_one("#home-status", Static)
            if apps:
                status.update(f"✓  {len(apps)} application(s)")
            else:
                status.update("📭  Aucune application")

        self.app.call_from_thread(populate)
