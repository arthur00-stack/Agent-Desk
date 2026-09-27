"""Exécute le pipeline Pipelex (utilisé uniquement en mode réel, hors USE_MOCK_LLM).

On passe par la CLI `pipelex run bundle` plutôt que par le SDK Python interne :
c'est l'interface publique stable de Pipelex, et elle écrit un
`working_memory.json` qui contient déjà, nommé, le résultat de chaque étape.

Note importante : les pipes du bundle produisent du **texte** (pas le
concept générique "JSON" de Pipelex), parce que ce dernier génère un schéma
sans `additionalProperties: false`, que le mode "structured outputs" strict
d'OpenAI refuse (erreur 400 `invalid_json_schema`). On demande donc à
chaque agent de répondre en JSON *dans du texte libre* (comme le fait déjà
le chemin natif `app/agents/*.py`, qui fonctionne), et on parse nous-mêmes
avec le même extracteur robuste que `llm_client.py` — c'est littéralement
la même stratégie qui a déjà fait ses preuves sur le chemin de secours.
"""
import json
import subprocess
import tempfile
from pathlib import Path

from app.llm_client import _extract_json

BUNDLE_PATH = Path(__file__).parent / "pipelex_bundles" / "alpha_desk.mthds"
STANCE_KEYS = ["macro", "fundamentals", "technical", "risk"]


class PipelexRunError(RuntimeError):
    pass


def run_desk_via_pipelex(ticker: str, query: str, snapshot: dict, news: list) -> dict:
    inputs = {
        "ticker": ticker,
        "sector": snapshot.get("sector", "N/A"),
        "news": "\n".join(f"- {n}" for n in news),
        "snapshot": json.dumps(snapshot, ensure_ascii=False),
        "query": query,
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        inputs_path = Path(tmpdir) / "inputs.json"
        inputs_path.write_text(json.dumps(inputs, ensure_ascii=False), encoding="utf-8")
        output_dir = Path(tmpdir) / "results"

        result = subprocess.run(
            [
                "pipelex", "run", "bundle", str(BUNDLE_PATH),
                "--pipe", "run_desk",
                "--inputs", str(inputs_path),
                "--output-dir", str(output_dir),
                "--no-graph",
                "--no-pretty-print",
            ],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(Path(__file__).parent.parent),  # racine du projet : .pipelex/ y est
        )
        if result.returncode != 0:
            raise PipelexRunError(f"Pipelex a échoué :\n{result.stderr[-3000:]}")

        run_dirs = sorted(output_dir.glob("run_desk_output_*"))
        if not run_dirs:
            raise PipelexRunError("Pipelex n'a produit aucun dossier de résultat.")

        memory_path = run_dirs[-1] / "working_memory.json"
        memory = json.loads(memory_path.read_text(encoding="utf-8"))
        root = memory.get("root", {})

    stances = []
    for key in STANCE_KEYS:
        stuff = root.get(key, {})
        raw_text = stuff.get("content", {}).get("text", "")
        parsed = _extract_json(raw_text)
        parsed["agent"] = key
        stances.append(parsed)

    memo_raw_text = root.get("memo", {}).get("content", {}).get("text", "")
    memo = _extract_json(memo_raw_text)
    memo["agent"] = "portfolio_manager"

    return {"stances": stances, "memo": memo}
