# widgets/rating_dialog.py
"""Widget de notation"""

from textual.app import ComposeResult
from textual.widgets import Label, Button, Input, Static
from textual.containers import Horizontal, Vertical, Container
from textual.screen import ModalScreen
from textual import events

class RatingDialog(ModalScreen):
    """Boîte de dialogue pour noter une application"""
    
    CSS = """
    RatingDialog {
        align: center middle;
        background: $surface 80%;
    }
    
    #rating-box {
        width: 50;
        height: auto;
        border: solid $primary;
        padding: 2 3;
        background: $surface;
    }
    
    #rating-box > Label {
        text-align: center;
        padding: 1;
    }
    
    #stars {
        height: 3;
        padding: 1;
        text-align: center;
    }
    
    #stars > Button {
        width: 5;
        margin: 0 1;
        padding: 0;
    }
    
    #stars > Button:hover {
        background: $primary-darken-1;
    }
    
    #stars > Button.selected {
        background: $primary;
    }
    
    #comment-input {
        margin: 1 0;
    }
    
    #rating-actions {
        height: 3;
        padding: 0 1;
    }
    
    #rating-actions > Button {
        margin: 0 1;
        width: 15;
    }
    
    #error {
        color: $error;
        text-align: center;
        height: 3;
    }
    """
    
    def __init__(self, bundle: str, app_name: str):
        super().__init__()
        self.bundle = bundle
        self.app_name = app_name
        self.selected_rating = 0
    
    def compose(self) -> ComposeResult:
        with Container(id="rating-box"):
            yield Label(f"⭐ Noter {self.app_name}", classes="title")
            yield Label("Sélectionnez une note:", classes="subtitle")
            
            with Horizontal(id="stars"):
                for i in range(1, 6):
                    yield Button("☆", id=f"star-{i}", variant="default")
            
            yield Input(placeholder="✏️ Votre commentaire (optionnel)", id="comment-input")
            
            with Horizontal(id="rating-actions"):
                yield Button("✅ Valider", id="submit-rating", variant="primary")
                yield Button("❌ Annuler", id="cancel-rating", variant="default")
            
            yield Static("", id="error")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel-rating":
            self.dismiss(None)
        elif event.button.id == "submit-rating":
            self.submit_rating()
        elif event.button.id.startswith("star-"):
            self.select_star(int(event.button.id.split("-")[1]))
    
    def on_key(self, event: events.Key) -> None:
        if event.key == "escape":
            self.dismiss(None)
        elif event.key in ["1", "2", "3", "4", "5"]:
            self.select_star(int(event.key))
        elif event.key == "enter":
            self.submit_rating()
    
    def select_star(self, rating: int) -> None:
        """Sélectionne une note"""
        self.selected_rating = rating
        
        for i in range(1, 6):
            button = self.query_one(f"#star-{i}")
            if i <= rating:
                button.label = "★"
                button.variant = "primary"
            else:
                button.label = "☆"
                button.variant = "default"
        
        self.query_one("#error").update("")
    
    def submit_rating(self) -> None:
        """Soumet la note"""
        if self.selected_rating == 0:
            self.query_one("#error").update("⚠️ Veuillez sélectionner une note")
            return
        
        comment = self.query_one("#comment-input").value.strip()
        
        self.query_one("#error").update("🔄 Envoi...")
        
        # Soumettre la note
        try:
            success = self.app.api.rate(self.bundle, self.selected_rating, comment)
            if success:
                self.query_one("#error").update("✅ Note envoyée !")
                self.dismiss({
                    "rating": self.selected_rating,
                    "comment": comment
                })
            else:
                self.query_one("#error").update("❌ Erreur lors de l'envoi")
        except Exception as e:
            self.query_one("#error").update(f"❌ Erreur: {e}")
