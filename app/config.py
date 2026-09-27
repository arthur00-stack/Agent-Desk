"""Charge les variables d'environnement (.env) explicitement depuis la racine
du projet, quel que soit le répertoire depuis lequel le script est lancé.
Si python-dotenv manque, on prévient bruyamment plutôt que d'échouer en
silence plus loin avec un KeyError incompréhensible.
"""
import sys
from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

try:
    from dotenv import load_dotenv

    if not _ENV_PATH.exists():
        print(
            f"[Alpha Desk] ATTENTION : {_ENV_PATH} n'existe pas. "
            f"Fais : cp .env.example .env, puis remplis tes clés.",
            file=sys.stderr,
        )
    load_dotenv(dotenv_path=_ENV_PATH, override=True)
except ImportError:
    print(
        "[Alpha Desk] ATTENTION : python-dotenv n'est pas installé, .env ne sera "
        "PAS chargé (tu vas avoir des KeyError sur les clés API). "
        "Lance : pip install -r requirements.txt dans ton venv activé.",
        file=sys.stderr,
    )
