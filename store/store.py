#!/usr/bin/env python3
# store.py
"""Point d'entrée StoreApp.TUI v2.0"""

import sys
import os

# Assure que les imports relatifs fonctionnent depuis le dossier store/
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import StoreApp


def main():
    try:
        app = StoreApp()
        app.run()
    except KeyboardInterrupt:
        print("\n  Au revoir !")
    except Exception as e:
        print(f"  Erreur fatale : {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
