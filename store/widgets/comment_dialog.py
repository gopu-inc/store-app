# widgets/comment_dialog.py
"""Dialog pour écrire un commentaire"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Static, TextArea
from textual.containers import Container, Horizontal
from textual import work
from textual import events
from rich.text import Text


class CommentDialog(ModalScreen):
    """Modal pour écrire un commentaire"""

    CSS = """
    CommentDialog {
        align: center middle;
    }

    #comment-panel {
        width: 60;
        height: auto;
        background: #161b22;
        border: solid #58a6ff;
        padding: 2 3;
    }

    #comment-panel-title {
        color: #58a6ff;
        text-style: bold;
        text-align: center;
        padding: 0 0 1 0;
    }

    #comment-area {
        height: 5;
        margin: 0 0 1 0;
        background: #0d1117;
        border: solid #30363d;
        color: #e6edf3;
    }

    #comment-area:focus {
        border: solid #58a6ff;
    }

    #comment-error {
        color: #f85149;
        text-align: center;
        height: auto;
        padding: 0 0 1 0;
    }

    #comment-panel-actions {
        height: 3;
        align: center middle;
    }

    #comment-panel-actions Button {
        margin: 0 1;
        width: 18;
    }
    """

    BINDINGS = [("escape", "cancel", "Annuler")]

    def __init__(self, bundle: str):
        super().__init__()
        self.bundle = bundle

    def compose(self) -> ComposeResult:
        with Container(id="comment-panel"):
            yield Static("💬  Écrire un commentaire", id="comment-panel-title")
            yield Input(
                placeholder="Votre commentaire (max 500 caractères)…",
                id="comment-area",
                max_length=500,
            )
            yield Static("", id="comment-error")
            with Horizontal(id="comment-panel-actions"):
                yield Button("✓  Envoyer", id="submit-btn", variant="primary")
                yield Button("✗  Annuler", id="cancel-btn", classes="ghost")

    def on_mount(self) -> None:
        self.query_one("#comment-area").focus()

    def on_key(self, event: events.Key) -> None:
        if event.key == "enter":
            self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "submit-btn":
            self._submit()
        elif event.button.id == "cancel-btn":
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def _submit(self) -> None:
        text = self.query_one("#comment-area", Input).value.strip()
        if not text:
            self.query_one("#comment-error", Static).update(
                Text("⚠  Le commentaire ne peut pas être vide", style="#f85149")
            )
            return
        self.query_one("#comment-error", Static).update(
            Text("⏳  Envoi…", style="#8b949e")
        )
        self.query_one("#submit-btn", Button).disabled = True
        self._submit_worker(text)

    @work(thread=True)
    def _submit_worker(self, text: str) -> None:
        ok, msg = self.app.api.comment(self.bundle, text)

        def finish():
            self.query_one("#submit-btn", Button).disabled = False
            if ok:
                self.dismiss({"content": text})
            else:
                self.query_one("#comment-error", Static).update(
                    Text(f"✗  {msg}", style="#f85149")
                )

        self.app.call_from_thread(finish)
