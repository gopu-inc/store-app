# screens/publish.py
"""Écran de publication — form rich + validation"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Static, Button, Input
from textual.containers import Horizontal, Vertical, Container, ScrollableContainer
from textual import work
from pathlib import Path
from rich.text import Text

INSTRUCTIONS = """\
  📦  Format accepté : .tpkg  ou  .tar.gz

  Structure attendue dans le package :
    ├── manifest.txml     (obligatoire)
    ├── README.md         (recommandé)
    ├── icon.png          (optionnel, 200×200)
    └── screenshots/      (optionnel, max 5 PNG)

  Le manifest.txml doit contenir au minimum :
    <name>, <bundle>, <version>, <author>, <entrypoint>
"""


class PublishScreen(Screen):
    """Écran de publication d'une application"""

    BINDINGS = [("escape", "go_back", "Retour")]

    def compose(self) -> ComposeResult:
        with Horizontal(id="publish-topbar"):
            yield Static("📤  Publier une application", id="publish-topbar-title")

        with ScrollableContainer(id="publish-body"):
            yield Static(INSTRUCTIONS, id="publish-instructions")

            yield Static("  📁  Chemin du fichier package", classes="publish-label")
            with Horizontal(id="path-row"):
                yield Input(
                    placeholder="/chemin/vers/monapp.tpkg",
                    id="package-path",
                )

            yield Static("", id="publish-file-preview")
            yield Static("", id="publish-status")

        with Horizontal(id="publish-actions"):
            yield Button("🚀  Publier", id="publish-btn", variant="primary")
            yield Button("🏠  Accueil", id="home-btn", classes="ghost")

    def on_mount(self) -> None:
        self.query_one("#package-path").focus()

    # ── Events ────────────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "package-path":
            self._validate_path()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "package-path":
            self._validate_path(silent=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "publish-btn":
            self._publish()
        elif event.button.id == "home-btn":
            self.app.push_screen("home")

    def action_go_back(self) -> None:
        self.app.pop_screen()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _validate_path(self, silent: bool = False) -> bool:
        raw = self.query_one("#package-path", Input).value.strip()
        preview = self.query_one("#publish-file-preview", Static)

        if not raw:
            preview.display = False
            return False

        path = Path(raw).expanduser()
        if not path.exists():
            if not silent:
                self._set_status("✗  Fichier introuvable", error=True)
            preview.display = False
            return False

        if not (raw.endswith(".tpkg") or raw.endswith(".tar.gz") or raw.endswith(".gz")):
            if not silent:
                self._set_status("✗  Format non supporté (.tpkg ou .tar.gz)", error=True)
            preview.display = False
            return False

        size = path.stat().st_size
        t = Text()
        t.append(f"  ✓  {path.name}", style="bold #3fb950")
        t.append(f"   ({size / 1024:.1f} Ko)", style="#8b949e")
        preview.update(t)
        preview.display = True
        self._set_status("")
        return True

    def _publish(self) -> None:
        if not self.app.api.token:
            self._set_status("✗  Vous devez être connecté pour publier", error=True)
            return

        if not self._validate_path():
            return

        raw = self.query_one("#package-path", Input).value.strip()
        path = Path(raw).expanduser()
        self._set_status("⏳  Publication en cours…")
        self.query_one("#publish-btn", Button).disabled = True
        self._publish_worker(path)

    @work(thread=True)
    def _publish_worker(self, path: Path) -> None:
        ok, message = self.app.api.publish(path)

        def finish():
            self.query_one("#publish-btn", Button).disabled = False
            if ok:
                self._set_status(f"✓  {message}", error=False)
                self.query_one("#package-path", Input).clear()
                self.query_one("#publish-file-preview", Static).display = False
                self.app.notify(f"Application publiée !", severity="information")
            else:
                self._set_status(f"✗  {message}", error=True)
                self.app.notify(f"Échec : {message}", severity="error")

        self.app.call_from_thread(finish)

    def _set_status(self, msg: str, error: bool = False) -> None:
        s = self.query_one("#publish-status", Static)
        if not msg:
            s.update("")
            return
        t = Text(msg, style="#f85149" if error else "#3fb950")
        s.update(t)
