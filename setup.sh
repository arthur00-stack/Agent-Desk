#!/usr/bin/env bash
# Setup complet et idempotent d'Alpha Desk. Relançable sans risque après
# chaque nouvelle version dézippée : recrée .pipelex/ (jamais livré dans le
# zip, spécifique à la machine) avec le bon choix de backend (OpenAI direct,
# pas le Gateway Pipelex par défaut).
set -e
cd "$(dirname "$0")"

echo "-> Environnement virtuel..."
python3 -m venv .venv
source .venv/bin/activate

echo "-> Installation des dépendances..."
pip install -q -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo "-> .env créé depuis .env.example : OUVRE-LE et remplis tes clés API avant de continuer !"
fi

echo "-> Configuration Pipelex (backend OpenAI direct, pas le Gateway)..."
printf 'y\n15\n\n' | pipelex init config --local > /tmp/pipelex_init.log 2>&1 || true
if grep -q '"OpenAI"' .pipelex/inference/backends.toml 2>/dev/null && \
   grep -A2 '\[openai\]' .pipelex/inference/backends.toml | grep -q 'enabled = true'; then
  echo "   OK : backend OpenAI actif."
else
  echo "   ATTENTION : vérifie .pipelex/inference/backends.toml à la main (voir README)."
fi

echo ""
echo "Setup terminé. Prochaines étapes :"
echo "  1. Vérifie que .env contient bien tes vraies clés (OPENAI_API_KEY, FINNHUB_API_KEY, GRADIUM_API_KEY)"
echo "  2. source .venv/bin/activate   (si ce n'est pas déjà fait dans ce terminal)"
echo "  3. python -m pytest tests/ -v"
echo "  4. python run_demo.py NVDA \"Faut-il investir dans NVDA maintenant ?\""
