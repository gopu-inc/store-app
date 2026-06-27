# screens/login.py
"""Écran de connexion"""

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Label, Input, Button, Static
from textual.containers import Container
from textual import events

class LoginScreen(Screen):
    """Écran de connexion StoreApp.TUI"""
    
    CSS = """
    LoginScreen {
        align: center middle;
    }
    
    #login-box {
        width: 50;
        height: auto;
        border: solid $primary;
        padding: 2 3;
        background: $surface;
    }
    
    #login-box > Label {
        text-align: center;
        padding: 1 0;
    }
    
    #login-box > Input {
        margin: 1 0;
    }
    
    #login-box > Button {
        margin: 1 0;
    }
    
    #error {
        color: $error;
        text-align: center;
        height: 3;
    }
    
    #status {
        color: $success;
        text-align: center;
        height: 3;
    }
    """
    
    def compose(self) -> ComposeResult:
        with Container(id="login-box"):
            yield Label("📦 StoreApp.TUI", classes="title")
            yield Label("Le Play Store du Terminal", classes="subtitle")
            yield Input(placeholder="👤 Nom d'utilisateur", id="username")
            yield Input(placeholder="🔒 Mot de passe", id="password", password=True)
            yield Button("🚀 Se connecter", id="login-btn", variant="primary")
            yield Button("📝 S'inscrire", id="signup-btn", variant="default")
            yield Static("", id="error")
            yield Static("", id="status")
    
    def on_mount(self) -> None:
        self.query_one("#username").focus()
    
    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "username":
            self.query_one("#password").focus()
        elif event.input.id == "password":
            self.do_login()
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-btn":
            self.do_login()
        elif event.button.id == "signup-btn":
            self.do_signup()
    
    def do_login(self) -> None:
        username = self.query_one("#username").value
        password = self.query_one("#password").value
        
        if not username or not password:
            self.query_one("#error").update("⚠️ Veuillez remplir tous les champs")
            return
        
        self.query_one("#error").update("")
        self.query_one("#status").update("🔄 Connexion...")
        
        if self.app.api.login(username, password):
            self.query_one("#status").update("✅ Connecté !")
            self.app.push_screen("home")
        else:
            self.query_one("#status").update("")
            self.query_one("#error").update("❌ Identifiants incorrects")
    
    def do_signup(self) -> None:
        username = self.query_one("#username").value
        password = self.query_one("#password").value
        
        if not username or not password:
            self.query_one("#error").update("⚠️ Veuillez remplir tous les champs")
            return
        
        self.query_one("#error").update("")
        self.query_one("#status").update("🔄 Inscription...")
        
        if self.app.api.signup(username, password):
            self.query_one("#status").update("✅ Compte créé ! Connectez-vous")
            self.query_one("#password").value = ""
            self.query_one("#password").focus()
        else:
            self.query_one("#status").update("")
            self.query_one("#error").update("❌ Erreur d'inscription")
