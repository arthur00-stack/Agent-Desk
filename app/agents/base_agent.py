"""Classe de base : chaque agent = un system prompt + une manière de
construire son prompt utilisateur à partir du contexte partagé.
L'appel LLM et le parsing JSON sont mutualisés ici (pas de duplication).
"""
from app.llm_client import chat_json


class BaseAgent:
    name: str = "base"
    system_prompt: str = ""

    def analyze(self, context: dict) -> dict:
        user_prompt = self.build_prompt(context)
        result = chat_json(system=self.system_prompt, user=user_prompt)
        result["agent"] = self.name
        return result

    def build_prompt(self, context: dict) -> str:
        raise NotImplementedError
