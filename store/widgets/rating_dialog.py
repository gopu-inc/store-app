# widgets/rating_dialog.py
"""Dialog de notation — clavier + souris"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static
from textual.containers import Horizontal, Container, Vertical
from textual import work
from textual import events
from rich.text import Text


STAR_LABELS = ["Médiocre", "Passable", "Correct", "Bien", "Excellent"]


class RatingDialog(ModalScreen):
    """Modal de notation (1–5 étoiles + commentaire)"""

    BINDINGS = [("escape", "cancel", "Annuler")]

    def __init__(self, bundle: str, app_name: str):
        super().__init__()
        self.bundle = bundle
        self.app_name = app_name
        self._rating = 0

    def compose(self) -> ComposeResult:
        with Container(id="rating-panel"):
            yield Static(f"⭐  Noter  {self.app_name}", id="rating-title")
            with Horizontal(id="stars-row"):
                for i in range(1, 6):
                    yield Button("☆", id=f"star-{i}", classes="star-btn")
            yield Static("Appuyez sur 1–5 ou cliquez", id="rating-hint")
            yield Input(placeholder="💬  Votre avis (optionnel)…", id="comment-input")
            yield Static("", id="rating-error")
            with Horizontal(id="rating-actions"):
                yield Button("✓  Valider", id="submit-btn", variant="primary")
                yield Button("✗  Annuler", id="cancel-btn", classes="ghost")

    # ── Events ────────────────────────────────────────────────────────────────

    def on_key(self, event: events.Key) -> None:
        if event.key in ("1", "2", "3", "4", "5"):
            self._select(int(event.key))
        elif event.key == "enter":
            self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid and bid.startswith("star-"):
            self._select(int(bid.split("-")[1]))
        elif bid == "submit-btn":
            self._submit()
        elif bid == "cancel-btn":
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    # ── Logic ─────────────────────────────────────────────────────────────────

    def _select(self, n: int) -> None:
        self._rating = n
        for i in range(1, 6):
            btn = self.query_one(f"#star-{i}", Button)
            if i <= n:
                btn.label = "★"
                btn.add_class("selected")
            else:
                btn.label = "☆"
                btn.remove_class("selected")
        label = STAR_LABELS[n - 1]
        hint = self.query_one("#rating-hint", Static)
        t = Text()
        t.append(f"  {n}/5 — {label}", style="#d29922")
        hint.update(t)
        self.query_one("#rating-error", Static).update("")

    def _submit(self) -> None:
        if self._rating == 0:
            self.query_one("#rating-error", Static).update(
                Text("⚠  Sélectionnez une note", style="#f85149")
            )
            return
        comment = self.query_one("#comment-input", Input).value.strip()
        self.query_one("#rating-error", Static).update(
            Text("⏳  Envoi…", style="#8b949e")
        )
        self.query_one("#submit-btn", Button).disabled = True
        self._submit_worker(self._rating, comment)

    @work(thread=True)
    def _submit_worker(self, rating: int, comment: str) -> None:
        ok, msg = self.app.api.rate(self.bundle, rating, comment or None)

        def finish():
            self.query_one("#submit-btn", Button).disabled = False
            if ok:
                self.dismiss({"rating": rating, "comment": comment})
            else:
                self.query_one("#rating-error", Static).update(
                    Text(f"✗  {msg}", style="#f85149")
                )

        self.app.call_from_thread(finish)
