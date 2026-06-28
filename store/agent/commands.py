# agent/commands.py
"""Gestionnaire de commandes de l'agent"""

import sys
from typing import List, Dict, Callable, Any


class CommandManager:
    """Gestionnaire de commandes"""
    
    def __init__(self):
        self.commands: Dict[str, Dict[str, Any]] = {}
        self._register_default_commands()
    
    def _register_default_commands(self):
        """Enregistre les commandes par défaut"""
        self.register("init", "Initialise un nouveau projet", self.cmd_init)
        self.register("build", "Build le package", self.cmd_build)
        self.register("publish", "Publie le package", self.cmd_publish)
        self.register("status", "Affiche le statut du projet", self.cmd_status)
        self.register("clean", "Nettoie les fichiers de build", self.cmd_clean)
        self.register("version", "Affiche la version de l'agent", self.cmd_version)
        self.register("help", "Affiche l'aide", self.cmd_help)
    
    def register(self, name: str, description: str, handler: Callable):
        """Enregistre une commande"""
        self.commands[name] = {
            "description": description,
            "handler": handler
        }
    
    def execute(self, cmd: str, args: List[str], agent) -> bool:
        """Exécute une commande"""
        if cmd in self.commands:
            try:
                return self.commands[cmd]["handler"](args, agent)
            except Exception as e:
                print(f"❌ Erreur: {e}")
                return False
        else:
            print(f"❌ Commande inconnue: {cmd}")
            print(f"ℹ️ Tapez 'agent help' pour voir les commandes disponibles")
            return False
    
    # === Commandes ===
    
    def cmd_init(self, args: List[str], agent) -> bool:
        """Initialise un nouveau projet"""
        if len(args) < 3:
            print("Usage: agent init <nom> <auteur> <bundle>")
            print("Exemple: agent init 'Mon App' 'Moi' 'com.mon.app'")
            return False
        
        name = args[0]
        author = args[1]
        bundle = args[2]
        
        return agent.init_project(name, author, bundle)
    
    def cmd_build(self, args: List[str], agent) -> bool:
        """Build le package"""
        result = agent.build()
        return result.get("success", False)
    
    def cmd_publish(self, args: List[str], agent) -> bool:
        """Publie le package"""
        # Vérifier le token
        token = args[0] if args else None
        if not token:
            print("⚠️ Veuillez fournir votre token")
            print("Usage: agent publish <token>")
            return False
        
        result = agent.publish(token)
        return result.get("success", False)
    
    def cmd_status(self, args: List[str], agent) -> bool:
        """Affiche le statut"""
        status = agent.status()
        print("\n📊 Statut de l'agent")
        print("=" * 40)
        print(f"Agent: {status['agent']['name']} v{status['agent']['version']}")
        print(f"Projet: {'✅ Initialisé' if status['project']['initialized'] else '❌ Non initialisé'}")
        
        if status['project']['metadata']:
            print("\n📦 Métadonnées:")
            for key, value in status['project']['metadata'].items():
                print(f"  {key}: {value}")
        
        print(f"\nÉtat: {status['agent']['state']}")
        return True
    
    def cmd_clean(self, args: List[str], agent) -> bool:
        """Nettoie les fichiers de build"""
        agent.builder.clean()
        print("✅ Nettoyage terminé")
        return True
    
    def cmd_version(self, args: List[str], agent) -> bool:
        """Affiche la version"""
        print(f"🤖 StoreApp.Agent v{agent.VERSION}")
        return True
    
    def cmd_help(self, args: List[str], agent) -> bool:
        """Affiche l'aide"""
        print("\n📚 Commandes disponibles:")
        print("=" * 40)
        for cmd, info in sorted(self.commands.items()):
            print(f"  {cmd:10} - {info['description']}")
        print("\n💡 Exemple: agent init 'Mon App' 'Moi' 'com.mon.app'")
        return True
