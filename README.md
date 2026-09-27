# Alpha Desk

Alpha Desk est une desk de recherche actions pilotée par des agents IA. Pour
un ticker et une question, trois analystes spécialisés produisent chacun une
thèse, un agent Risque les challenge, puis un Portfolio Manager arbitre leurs
désaccords et rédige un mémo final (`BUY`, `HOLD` ou `SELL`).

> **Avertissement** : Alpha Desk est un prototype à but pédagogique. Ses
> sorties ne constituent pas un conseil en investissement. Les données peuvent
> être incomplètes, retardées ou remplacées par des données mock.

## Fonctionnalités

- Analyse macro, fondamentale et technique avec sorties structurées.
- Challenge Risque / Compliance dépendant des trois analyses précédentes.
- Arbitrage final du Portfolio Manager avec confiance, risques clés et avis
  dissident.
- Données de marché Finnhub et actualités via la recherche web OpenAI.
- Fallback automatique vers des données mock en cas de clé absente, d'erreur
  réseau ou de quota atteint.
- Interface web FastAPI avec synthèse vocale et saisie micro optionnelles via
  Gradium.
- Outil MCP `consult_alpha_desk` utilisable depuis un agent conversationnel
  comme Dust.

## Architecture

```text
Ticker + question
       |
       v
Snapshot Finnhub + actualites OpenAI
       |
       +--> Macro --------+
       +--> Fondamental --+--> Risque / Compliance --> Portfolio Manager
       +--> Technique ----+          (challenge)          (memo final)
```

En mode réel, Pipelex exécute ce workflow dans
[`app/pipelex_bundles/alpha_desk.mthods`](app/pipelex_bundles/alpha_desk.mthods) :
les trois spécialistes sont parallélisés, puis le risque et l'arbitrage sont
séquentiels. Si Pipelex échoue, l'orchestrateur utilise automatiquement le
chemin Python natif et renseigne `degraded_reason` dans la réponse API.

## Pré-requis

- Python 3.10 ou supérieur
- Une clé OpenAI pour le mode réel
- Une clé Finnhub facultative pour les données de marché
- Une clé Gradium facultative pour la voix

## Installation

Le script suivant crée le virtualenv, installe les dépendances, crée `.env` et
configure Pipelex avec le backend OpenAI :

```bash
./setup.sh
source .venv/bin/activate
```

Pour une installation manuelle :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Renseigne ensuite les variables nécessaires dans `.env` :

| Variable          | Obligatoire | Utilisation                       |
| ----------------- | ----------- | --------------------------------- |
| `OPENAI_API_KEY`  | Mode réel   | Agents et recherche web           |
| `OPENAI_MODEL`    | Non         | Modèle OpenAI, par défaut `gpt-5` |
| `FINNHUB_API_KEY` | Non         | Prix, métriques et secteur        |
| `USE_MOCK_LLM`    | Non         | `1` pour la démo hors-ligne       |
| `GRADIUM_API_KEY` | Non         | STT/TTS dans l'interface          |
| `GRADIUM_VOICE_*` | Non         | Voix par agent                    |

Ne versionne jamais `.env`. Les clés doivent rester dans l'environnement local
ou dans un gestionnaire de secrets.

## Utilisation

### Démo CLI

```bash
python run_demo.py NVDA "Faut-il regarder NVDA avant les résultats ?"
```

Le résultat JSON contient le ticker, le snapshot utilisé, les actualités, les
quatre stances, le mémo final et l'éventuel motif de fallback.

### Interface web

```bash
uvicorn app.main:app --reload
```

Ouvre ensuite <http://localhost:8000>. Le bouton micro et la lecture audio
restent désactivés automatiquement si Gradium n'est pas configuré.

### Mode hors-ligne

Pour développer, tester ou répéter une présentation sans appels externes :

```bash
USE_MOCK_LLM=1 uvicorn app.main:app --reload
```

Ce mode utilise les réponses mock et les snapshots mock déterministes. Il ne
nécessite ni clé OpenAI, ni clé Finnhub, ni connexion réseau pour le pipeline.

## API HTTP

| Méthode | Route      | Rôle                                         |
| ------- | ---------- | -------------------------------------------- |
| `POST`  | `/analyze` | Lance une analyse complète                   |
| `POST`  | `/speak`   | Synthétise un texte en WAV, ou renvoie `204` |
| `POST`  | `/listen`  | Transcrit un fichier audio WebM              |
| `GET`   | `/`        | Sert l'interface web                         |

Exemple d'appel :

```bash
curl -X POST http://localhost:8000/analyze \
  -H 'Content-Type: application/json' \
  -d '{"ticker":"NVDA","query":"Le titre est-il trop cher ?"}'
```

## Intégration MCP / Dust

Le serveur MCP expose un seul outil, `consult_alpha_desk(ticker, query)` :

```bash
python mcp_server.py
```

Il écoute sur `http://localhost:8001/mcp`. Pour un agent Dust hébergé, rends
ce port accessible avec un tunnel HTTPS, par exemple :

```bash
ngrok http 8001
```

Dans Dust, ajoute l'URL publique terminée par `/mcp` comme serveur MCP et
attache-le à l'agent conversationnel. Le serveur ne décide pas quand appeler
l'outil : c'est l'agent Dust qui choisit de convoquer la desk selon le contexte
de la conversation.

## Tests et validation Pipelex

```bash
python -m pytest tests/ -v
pipelex validate bundle app/pipelex_bundles/alpha_desk.mthods
```

Les tests couvrent notamment les snapshots mock, l'extraction JSON, le cache
TTL et le fallback automatique quand Pipelex échoue.

## Structure du projet

```text
app/
  agents/              Agents macro, fondamentaux, technique, risque et PM
  tools/               Marché, recherche web et voix
  orchestrator.py      Collecte des données et sélection du chemin d'exécution
  pipelex_bundles/     Définition du workflow Pipelex
  main.py              API FastAPI
frontend/              Interface HTML, CSS et JavaScript
tests/                 Tests automatisés
mcp_server.py          Adaptateur MCP pour les agents externes
run_demo.py            Point d'entrée CLI
setup.sh               Installation reproductible
```

## Dépannage rapide

- **`OPENAI_API_KEY` introuvable** : vérifie que `.env` existe à la racine et
  que le virtualenv est activé.
- **Pipelex indisponible** : lance `pipelex validate bundle ...` ; en mode
  réel, Alpha Desk doit basculer automatiquement sur le chemin Python natif.
- **Données mock affichées** : vérifie `FINNHUB_API_KEY`, le réseau et le
  ticker ; un fallback est volontairement appliqué en cas d'erreur.
- **Voix absente** : renseigne `GRADIUM_API_KEY` et les identifiants
  `GRADIUM_VOICE_*`. Le texte reste disponible sans eux.

## Sécurité

Si une clé a été copiée dans un dépôt, un log ou un fichier partagé, révoque-la
immédiatement auprès du fournisseur puis remplace-la. Utilise `.env` local,
jamais `.env.example`, pour les valeurs réelles.
