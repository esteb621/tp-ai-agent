"""
SupportWorkflow — Workflow parallèle de diagnostic support utilisateur.

Type   : ParallelAgent (Workflow Agent ADK)
Agents : ServerCheckBot ∥ PlexCheckBot (exécutés simultanément)

Ce workflow est déclenché quand un utilisateur signale un problème de lecture
(saccades, sous-titres manquants, etc.). Il lance en parallèle :
  - ServerCheckBot : vérifie l'état général du serveur (charge CPU/RAM simulée)
  - PlexCheckBot   : vérifie le flux Plex de l'utilisateur (transcodage, sous-titres)

Le résultat des deux vérifications est ensuite synthétisé par TriageBot.
"""

from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.models.lite_llm import LiteLlm
from ..agents.plex_bot import plex_check_bot
from ..agents.server_bot import server_check_bot

support_workflow = ParallelAgent(
    name="SupportWorkflow",
    description=(
        "Workflow de diagnostic support. Lance en parallèle la vérification "
        "du flux Plex et l'état du serveur pour diagnostiquer un problème de lecture."
    ),
    sub_agents=[
        plex_check_bot,    # Diagnostic flux Plex (parallèle)
        server_check_bot,  # Diagnostic serveur  (parallèle)
    ],
)
