"""Test rapide en ligne de commande, sans lancer le serveur ni le front.

Usage :
    USE_MOCK_LLM=1 python run_demo.py NVDA "Faut-il regarder NVDA avant les résultats ?"
    python run_demo.py TSLA "Le titre est-il trop cher après le rally ?"
"""

from app import config  # charge .env avant tout le reste, quel que soit le chemin emprunté ensuite
import json
import sys

from app.orchestrator import run_desk

if __name__ == "__main__":
    ticker = sys.argv[1] if len(sys.argv) > 1 else "NVDA"
    query = sys.argv[2] if len(sys.argv) > 2 else f"Faut-il investir dans {ticker} maintenant ?"
    result = run_desk(query, ticker)
    print(json.dumps(result, indent=2, ensure_ascii=False))
