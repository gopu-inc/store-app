#!/usr/bin/env python3
# agent_cli.py
"""CLI de l'agent StoreApp.TUI"""

import sys
import os
from pathlib import Path

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from store.agent import Agent


def main():
    """Point d'entrée de l'agent"""
    args = sys.argv[1:]
    
    if len(args) == 0:
        args = ["help"]
    
    cmd = args[0]
    cmd_args = args[1:]
    
    agent = Agent()
    
    if cmd == "gestionary_version":
        print(f"🤖 StoreApp.Agent v{agent.VERSION}")
        print(f"📦 Gestionary Version: 2.0.0")
        return 0
    
    # Exécuter la commande
    success = agent.run_command(cmd, cmd_args)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
