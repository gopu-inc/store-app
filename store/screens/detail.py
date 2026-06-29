# screens/detail.py
"""Détail d'une application — TabbedContent : Info | README | Avis"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import (
    Label, Static, Button, Markdown,
    TabbedContent, TabPane, ProgressBar,
)
from textual.containers import Horizontal, Vertical, Container, ScrollableContainer
from textual import work
from textual import events
from pathlib import Path
from rich.text import Text

from widgets.rating_dialog import RatingDialog
from widgets.comment_dialog import CommentDialog


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
    return icons.get((env or "").lower(), "📦")


class DetailScreen(Screen):
    """Détail complet d'une application avec onglets"""

    BINDINGS = [("escape", "go_back", "Retour")]

    def __init__(self):
        super().__init__()
        self._data: dict = {}

    def compose(self) -> ComposeResult:
        # Top bar
        with Horizontal(id="detail-topbar"):
            yield Static("📦  Détail de l'application", id="detail-topbar-title")
            yield Static("⏳  Chargement…", id="detail-status")

        # Hero section
        with Vertical(id="detail-hero"):
            yield Static("", id="hero-name")
            yield Static("", id="hero-bundle")
            with Horizontal(id="hero-meta-row"):
                yield Static("", id="hero-version")
                yield Static("", id="hero-author")
                yield Static("", id="hero-stars")
                yield Static("", id="hero-downloads")
                yield Static("", id="hero-env-badge")

        # Download progress (hidden by default)
        yield ProgressBar(id="download-progress", total=100, show_eta=False)

        # Tabbed content
        with TabbedContent(id="detail-content"):
            with TabPane("📋  Informations", id="tab-info"):
                yield ScrollableContainer(
                    Static("", id="info-desc"),
                    Vertical(id="info-grid"),
                    id="info-scroll",
                )

            with TabPane("📖  README", id="tab-readme"):
                with ScrollableContainer(id="readme-scroll"):
                    yield Markdown("*Chargement du README…*", id="readme-md")

            with TabPane("⭐  Avis", id="tab-reviews"):
                with ScrollableContainer(id="reviews-list"):
                    yield Static("", id="reviews-content")

        # Bottom actions
        with Horizontal(id="detail-actions"):
            yield Button("⬇  Télécharger", id="download-btn", variant="primary")
            yield Button("⭐  Noter", id="rate-btn", variant="success")
            yield Button("💬  Commenter", id="comment-btn", classes="ghost")
            yield Button("🔙  Retour", id="back-btn", classes="ghost")

    def on_mount(self) -> None:
        # Hide progress bar
        self.query_one("#download-progress").display = False
        self._load_detail()

    # ── Events ────────────────────────────────────────────────────────────────

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back-btn":
            self.app.pop_screen()
        elif event.button.id == "download-btn":
            self._download()
        elif event.button.id == "rate-btn":
            self._show_rating()
        elif event.button.id == "comment-btn":
            self._show_comment()

    def action_go_back(self) -> None:
        self.app.pop_screen()

    # ── Loader ────────────────────────────────────────────────────────────────

    @work(thread=True)
    def _load_detail(self) -> None:
        bundle = self.app.current_app
        if not bundle:
            return
        try:
            data = self.app.api.get_app(bundle)
        except Exception as e:
            self.app.call_from_thread(
                self.query_one("#detail-status", Static).update, f"✗  {e}"
            )
            return

        if not data:
            self.app.call_from_thread(
                self.query_one("#detail-status", Static).update,
                "✗  Application introuvable",
            )
            return

        self._data = data
        self.app.call_from_thread(self._render_data, data)

    def _render_data(self, data: dict) -> None:
        meta = data.get("metadata", {}) or {}
        manifest = data.get("manifest", {}) or {}
        ratings = data.get("ratings", []) or []
        comments = data.get("comments", []) or []
        readme = data.get("readme", "") or ""

        name = meta.get("name", "—")
        bundle = meta.get("bundle", "—")
        version = meta.get("version", "—")
        author = meta.get("author", "—")
        env = meta.get("environnement", manifest.get("environnement", "python")) or "python"
        rating = meta.get("rating", 0)
        rating_count = meta.get("rating_count", 0)
        downloads = meta.get("downloads", 0)
        description = meta.get("description", "") or ""
        deps = meta.get("dependencies", manifest.get("dependencies", [])) or []
        perms = meta.get("permissions", manifest.get("permissions", [])) or []
        homepage = meta.get("homepage", "") or ""
        license_ = meta.get("license", "") or ""
        app_path = meta.get("app_path", manifest.get("app_path", "~/")) or "~/"
        gestionnaire = meta.get("gestionnaire", manifest.get("gestionnaire", "")) or ""
        size = meta.get("size", 0)

        icon = _env_icon(env)

        # ── Hero ──────────────────────────────────────────────────────────────
        name_t = Text()
        name_t.append(f"  {name}", style="bold #e6edf3")
        self.query_one("#hero-name", Static).update(name_t)
        self.query_one("#hero-bundle", Static).update(
            Text(f"  {bundle}", style="#8b949e")
        )
        self.query_one("#hero-version", Static).update(
            Text(f"v{version}", style="#3fb950")
        )
        self.query_one("#hero-author", Static).update(
            Text(f"by {author}", style="#bc8cff")
        )
        stars_t = Text()
        stars_t.append(_stars(rating), style="#d29922")
        stars_t.append(f"  {rating:.1f}  ({rating_count} avis)", style="#8b949e")
        self.query_one("#hero-stars", Static).update(stars_t)
        self.query_one("#hero-downloads", Static).update(
            Text(f"↓ {downloads} téléchargements", style="#8b949e")
        )
        self.query_one("#hero-env-badge", Static).update(
            Text(f" {icon} {env} ", style="#58a6ff")
        )

        # ── Info tab ───────────────────────────────────────────────────────────
        desc_t = Text()
        desc_t.append("\n  " + description + "\n\n", style="#e6edf3")
        self.query_one("#info-desc", Static).update(desc_t)

        grid = self.query_one("#info-grid", Vertical)
        grid.remove_children()

        def row(key: str, val: str):
            with grid:
                h = Horizontal(classes="info-row")
                h.mount(Static(key, classes="info-key"))
                h.mount(Static(val, classes="info-val"))

        def add_field(key: str, val: str):
            h = Horizontal(classes="info-row")
            k = Static(key, classes="info-key")
            v = Static(val, classes="info-val")
            grid.mount(h)
            h.mount(k)
            h.mount(v)

        add_field("📦  Bundle", bundle)
        add_field("🔖  Version", version)
        add_field("✍  Auteur", author)
        add_field("⚖  Licence", license_ or "—")
        add_field("🌐  Homepage", homepage or "—")
        add_field("📂  App path", app_path)
        add_field("⚙  Gestionnaire", gestionnaire or "—")
        add_field("💾  Taille", f"{size / 1024:.1f} Ko" if size else "—")
        add_field("📦  Dépendances", ", ".join(deps) if deps else "—")
        add_field("🔧  Permissions", ", ".join(perms) if perms else "—")

        # ── README tab ─────────────────────────────────────────────────────────
        if readme.strip():
            self.query_one("#readme-md", Markdown).update(readme)
        else:
            self.query_one("#readme-md", Markdown).update(
                "*Aucun README disponible pour cette application.*"
            )

        # ── Reviews tab ────────────────────────────────────────────────────────
        self._render_reviews(ratings, comments)

        # ── Status ─────────────────────────────────────────────────────────────
        self.query_one("#detail-status", Static).update("✓  Chargé")

    def _render_reviews(self, ratings: list, comments: list) -> None:
        content = self.query_one("#reviews-content", Static)
        if not ratings and not comments:
            content.update(Text("\n  Aucun avis pour cette application.", style="#8b949e"))
            return

        t = Text()
        if ratings:
            t.append(f"\n  {len(ratings)} note(s)\n", style="bold #58a6ff")
            t.append("  " + "─" * 44 + "\n", style="#30363d")
            for r in reversed(ratings[-20:]):
                user = r.get("username", "?")
                stars = r.get("rating", 0)
                comment = r.get("comment", "") or ""
                date = (r.get("created_at", "") or "")[:10]
                t.append(f"  {user}", style="bold #bc8cff")
                t.append(f"  {_stars(stars)}", style="#d29922")
                t.append(f"  {date}\n", style="#30363d")
                if comment:
                    t.append(f"  {comment}\n", style="#e6edf3")
                t.append("\n")

        if comments:
            t.append(f"  {len(comments)} commentaire(s)\n", style="bold #58a6ff")
            t.append("  " + "─" * 44 + "\n", style="#30363d")
            for c in reversed(comments[-20:]):
                user = c.get("username", "?")
                text = c.get("content", "") or ""
                date = (c.get("created_at", "") or "")[:10]
                t.append(f"  {user}", style="bold #bc8cff")
                t.append(f"  {date}\n", style="#30363d")
                t.append(f"  {text}\n\n", style="#e6edf3")

        content.update(t)

    # ── Download ──────────────────────────────────────────────────────────────

    def _download(self) -> None:
        bundle = self.app.current_app
        if not bundle:
            return
        pb = self.query_one("#download-progress", ProgressBar)
        pb.display = True
        pb.update(progress=0)
        self.query_one("#detail-status", Static).update("⬇  Téléchargement…")
        self._download_worker(bundle)

    @work(thread=True)
    def _download_worker(self, bundle: str) -> None:
        from config import Config
        output = Config.DOWNLOAD_DIR / f"{bundle}.tpkg"
        ok = self.app.api.download(bundle, output)

        def finish():
            pb = self.query_one("#download-progress", ProgressBar)
            pb.update(progress=100)
            if ok:
                self.query_one("#detail-status", Static).update(f"✓  Sauvegardé : {output}")
                self.app.notify(f"Téléchargé : {bundle}", severity="information")
                pb.display = False
            else:
                self.query_one("#detail-status", Static).update("✗  Échec du téléchargement")
                self.app.notify("Téléchargement échoué", severity="error")
                pb.display = False

        self.app.call_from_thread(finish)

    # ── Rating / Comment ──────────────────────────────────────────────────────

    def _show_rating(self) -> None:
        if not self.app.api.token:
            self.app.notify("Connectez-vous pour noter", severity="warning")
            return
        bundle = self.app.current_app
        meta = self._data.get("metadata", {}) or {}
        app_name = meta.get("name", bundle)

        def on_result(result):
            if result:
                self.app.notify(
                    f"Note {result['rating']}/5 envoyée !", severity="information"
                )
                self._load_detail()

        self.app.push_screen(RatingDialog(bundle, app_name), on_result)

    def _show_comment(self) -> None:
        if not self.app.api.token:
            self.app.notify("Connectez-vous pour commenter", severity="warning")
            return
        bundle = self.app.current_app

        def on_result(result):
            if result:
                self.app.notify("Commentaire ajouté !", severity="information")
                self._load_detail()

        self.app.push_screen(CommentDialog(bundle), on_result)
