# screens/browse.py
"""Écran de recherche — DataTable + recherche live"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Static, Button, DataTable, Input
from textual.containers import Horizontal, Vertical
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


class BrowseScreen(Screen):
    """Écran de parcours / recherche"""

    BINDINGS = [("escape", "go_back", "Retour")]

    def compose(self) -> ComposeResult:
        with Horizontal(id="browse-topbar"):
            yield Static("🔍  Parcourir les applications", id="browse-topbar-title")

        with Horizontal(id="search-bar"):
            yield Input(
                placeholder="Tapez pour rechercher — nom, auteur, description…",
                id="search-input",
            )
            yield Button("Chercher", id="search-btn", variant="primary")

        yield Static("", id="browse-stats")
        yield DataTable(id="browse-table", cursor_type="row")

        with Horizontal(id="browse-actions"):
            yield Button("🔄  Tout afficher", id="refresh-btn", classes="ghost")
            yield Button("🏠  Accueil", id="home-btn", variant="primary")

    def on_mount(self) -> None:
        table = self.query_one("#browse-table", DataTable)
        table.add_column("  Application", key="name")
        table.add_column("Version", key="version")
        table.add_column("Auteur", key="author")
        table.add_column("Env", key="env")
        table.add_column("Note", key="rating")
        table.add_column("  Description", key="desc")
        self._load_all()

    # ── Events ────────────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "search-btn":
            self._do_search()
        elif event.button.id == "refresh-btn":
            self.query_one("#search-input", Input).clear()
            self._load_all()
        elif event.button.id == "home-btn":
            self.app.push_screen("home")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._do_search()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        bundle = event.row_key.value  # type: ignore[attr-defined]
        if bundle:
            self.app.open_detail(bundle)

    def action_go_back(self) -> None:
        self.app.pop_screen()

    # ── Workers ───────────────────────────────────────────────────────────────

    def _do_search(self) -> None:
        query = self.query_one("#search-input", Input).value.strip()
        if len(query) < 2:
            self._load_all()
            return
        self.query_one("#browse-stats", Static).update("⏳  Recherche en cours…")
        self._search_worker(query)

    @work(thread=True)
    def _load_all(self) -> None:
        self.app.call_from_thread(
            lambda: self.query_one("#browse-stats", Static).update("⏳  Chargement…")
        )
        try:
            apps = self.app.api.get_apps(100)
        except Exception as e:
            err = str(e)
            self.app.call_from_thread(
                lambda: self.query_one("#browse-stats", Static).update(f"✗  {err}")
            )
            return
        self.app.call_from_thread(self._populate, apps, "")

    @work(thread=True)
    def _search_worker(self, query: str) -> None:
        try:
            apps = self.app.api.search(query)
        except Exception as e:
            err = str(e)
            self.app.call_from_thread(
                lambda: self.query_one("#browse-stats", Static).update(f"✗  {err}")
            )
            return
        self.app.call_from_thread(self._populate, apps, query)

    def _populate(self, apps: list, query: str) -> None:
        table = self.query_one("#browse-table", DataTable)
        table.clear()
        for a in apps:
            name = a.get("name", "—")
            version = a.get("version", "—")
            author = a.get("author", "—")
            env = a.get("environnement", "python")
            rating = a.get("rating", 0)
            desc = (a.get("description", "") or "")[:55]
            bundle = a.get("bundle", "")
            icon = _env_icon(env)

            name_text = Text()
            name_text.append("  ")
            if query and query.lower() in name.lower():
                # Highlight match
                lo = name.lower().find(query.lower())
                name_text.append(name[:lo], style="#e6edf3 bold")
                name_text.append(name[lo:lo+len(query)], style="bold #58a6ff on #1f6feb")
                name_text.append(name[lo+len(query):], style="#e6edf3 bold")
            else:
                name_text.append(name, style="bold #e6edf3")

            stars_text = Text()
            stars_text.append(_stars(rating), style="#d29922")
            stars_text.append(f" {rating:.1f}", style="#8b949e")

            env_text = Text(f"{icon} {env}", style="#58a6ff")

            desc_text = Text(desc + ("…" if len(a.get("description","") or "") > 55 else ""),
                             style="#8b949e")

            table.add_row(
                name_text,
                Text(version, style="#3fb950"),
                Text(author, style="#bc8cff"),
                env_text,
                stars_text,
                desc_text,
                key=bundle,
            )

        stats = self.query_one("#browse-stats", Static)
        if query:
            stats.update(f'✓  {len(apps)} résultat(s) pour "{query}"')
        elif apps:
            stats.update(f"✓  {len(apps)} application(s) disponible(s)")
        else:
            stats.update("📭  Aucune application")
