"""Serveur MCP exposant Alpha Desk comme UN outil que Dust peut appeler.

C'est cette couche qui transforme Alpha Desk en vrai agent au sens du
règlement du hackathon : Dust est l'agent qui RAISONNE sur la conversation
et DÉCIDE d'appeler cet outil (ou pas, ou avec quels paramètres) ; ce
serveur ne fait qu'exposer l'action. La logique métier (3 analystes ->
risque -> arbitrage via Pipelex) ne change pas, elle est juste appelée
depuis un vrai agent conversationnel plutôt que déclenchée à la main.

Usage :
    python mcp_server.py
    # puis, pour le rendre joignable par Dust (hébergé) :
    ngrok http 8001
    # récupère l'URL https://xxxx.ngrok-free.app et enregistre-la dans
    # Dust : Spaces > Tools > Add Tool > Add MCP Server (+ /mcp à la fin
    # de l'URL, ex: https://xxxx.ngrok-free.app/mcp)

Note : construit avec `mcp` v2.2.0 (le nom de la classe a changé récemment,
FastMCP -> MCPServer — beaucoup de tutos en ligne sont encore sur l'ancienne
API, vérifié directement dans le package installé pour éviter ce piège).
"""

from app import config  # charge .env avant tout le reste, quel que soit le chemin emprunté ensuite
from mcp.server.mcpserver import MCPServer

from app.orchestrator import run_desk

mcp = MCPServer(name="Alpha Desk")


@mcp.tool()
def consult_alpha_desk(ticker: str, query: str) -> dict:
    """Convoque la desk de recherche IA (analystes macro/fondamental/technique,
    agent risque, portfolio manager) sur un ticker donné et renvoie le mémo
    d'investissement final (recommandation BUY/HOLD/SELL, raisons, risques
    clés) ainsi que l'avis détaillé de chaque analyste.

    À utiliser dès que l'utilisateur pose une vraie question d'investissement
    sur une action précise identifiable par son ticker (ex: "faut-il acheter
    NVDA avant les résultats ?", "TSLA est-il trop cher ?"). Ne pas utiliser
    pour des questions générales de culture financière qui ne visent pas un
    titre précis.

    Args:
        ticker: le symbole boursier, ex. "NVDA", "TSLA", "AAPL".
        query: la question ou la thèse de l'utilisateur, telle quelle.
    """
    return run_desk(query=query, ticker=ticker.upper())


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="0.0.0.0", port=8001, stateless_http=True)
