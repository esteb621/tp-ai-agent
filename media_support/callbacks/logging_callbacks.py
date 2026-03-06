"""
Callbacks de logging pour le système multi-agents.

Implémente deux callbacks ADK :
  - before_tool_callback  : loggue le démarrage de chaque outil
  - after_agent_callback  : loggue la fin de chaque agent

Signatures exactes vérifiées depuis le source ADK v1.26.0 :
  - before_tool_callback : (BaseTool, dict[str, Any], ToolContext) -> Optional[dict]
  - after_agent_callback : (CallbackContext) -> Optional[Content]
"""

from typing import Any, Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.llm_agent import LlmResponse

VALID_TOOLS = {
    "get_stuck_downloads",
    "search_and_replace_release", 
    "get_available_releases",
    "download_release",
    "comms_bot_tool"
}
def on_tool_start(
    tool: BaseTool,
    args: dict[str, Any],
    tool_context: ToolContext,
) -> Optional[dict]:
    """
    Callback déclenché AVANT l'exécution d'un outil (before_tool_callback).

    Affiche dans la console le nom de l'outil qui va être appelé ainsi que
    ses arguments d'entrée, pour un suivi en temps réel de l'activité.

    Args:
        tool (BaseTool)         : L'instance de l'outil qui va être exécuté.
        args (dict[str, Any])   : Les arguments passés à l'outil.
        tool_context (ToolContext): Le contexte d'exécution du callback.

    Returns:
        Optional[dict]: Retourner None = laisser l'outil s'exécuter normalement.
                        Retourner un dict = court-circuiter l'outil avec ce résultat.
    """
    if tool.name not in VALID_TOOLS:
        # Retourne une fausse réponse qui force l'agent à se corriger
        return {
            "error": f"Tool '{tool.name}' does not exist.",
            "instruction": f"You MUST only use one of: {', '.join(VALID_TOOLS)}. Try again with a valid tool."
        }
    return None  # Laisse passer si l'outil est valide


def on_agent_end(callback_context: CallbackContext) -> None:
    """
    Callback déclenché APRÈS la fin d'un agent LLM (after_agent_callback).

    Affiche dans la console le nom de l'agent qui vient de terminer son
    exécution, pour un suivi en temps réel des agents actifs.

    Args:
        callback_context (CallbackContext): Le contexte contenant les métadonnées
                                            de l'agent (nom, session, state, etc.).

    Returns:
        None: Retourner None = ne pas modifier ni remplacer la réponse de l'agent.
              Retourner un Content = remplacer la réponse de l'agent (éviter sauf besoin).
    """
    agent_name = getattr(callback_context, "agent_name", "Agent inconnu")

    print("\n" + "✅" * 30)
    print(f"[CALLBACK] 🏁  AGENT TERMINÉ : {agent_name}")
    print("✅" * 30 + "\n")

    # Retourner None = ne pas intercept la réponse de l'agent
    return None

def on_model_response(llm_response: LlmResponse, callback_context: CallbackContext):
    for part in llm_response.content.parts:
        if hasattr(part, "thought") and part.thought:
            print(f"🧠 [THINKING]: {part.thought}")
        if hasattr(part, "text") and part.text:
            print(f"💬 [TEXT]: {part.text}")