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
from ..tools import plex_tools
from ..callbacks import logging_callbacks
# ─────────────────────────────────────────────────────────────────────────────
# Modèles : Mistral et Llama 3.2 — tous les deux via Ollama (local)
# Prérequis : ollama pull mistral && ollama pull llama3.2 && ollama serve
# ─────────────────────────────────────────────────────────────────────────────
MISTRAL_MODEL = LiteLlm(model="ollama/mistral")
LLAMA_MODEL = LiteLlm(model="ollama/llama3.2")

# ─────────────────────────────────────────────────────────────────────────────
# Agent 1 : PlexCheckBot
# Diagnostique le flux Plex de l'utilisateur signalant le problème
# ─────────────────────────────────────────────────────────────────────────────
plex_check_bot = LlmAgent(
    name="PlexCheckBot",
    model=MISTRAL_MODEL,
    description="Agent de diagnostic Plex. Vérifie le flux de lecture d'un utilisateur.",
    instruction="""Tu es PlexCheckBot, spécialiste du diagnostic de flux Plex.
    Un utilisateur signale un problème de lecture. Effectue les actions suivantes :

    TON SEUL OUTIL DISPONIBLE EST check_plex_playback
    1. Appelle l'outil `check_plex_playback` avec le nom d'utilisateur extrait du message
    (si non précisé, utilise "utilisateur_plex" comme valeur par défaut).

    2. Analyse les résultats :
    - Si `transcoding` est True → problème probable de codec ou de bande passante
    - Si `missing_subtitles` est True → sous-titres non chargés ou absents de la librairie
    - Si `bitrate_kbps` < 5000 → débit insuffisant pour la qualité demandée

    3. Retourne un résumé de diagnostic clair avec :
    - Statut du flux (actif / inactif)
    - Problèmes détectés
    - Cause probable pour chaque problème
    - Recommandations de l'utilisateur (changer qualité, ajouter sous-titres, etc.)
    """,
    tools=[plex_tools.check_plex_playback],
    output_key="plex_diagnostic",  # Stocke le diagnostic dans le state
    before_tool_callback=logging_callbacks.on_tool_start,
    after_agent_callback=logging_callbacks.on_agent_end,
)

# ─────────────────────────────────────────────────────────────────────────────
# Agent 2 : ServerCheckBot
# Vérifie l'état général du serveur média (simulé), prendre sur tautulli
# ─────────────────────────────────────────────────────────────────────────────
server_check_bot = LlmAgent(
    name="ServerCheckBot",
    model=LLAMA_MODEL,
    description="Media server health check agent.",
    instruction="""You are ServerCheckBot, a media server monitoring agent.

    A user has reported an issue. Without any additional tools available,
    perform a simulated server health check and return a report including:

    1. **Overall server status** (simulated):
    - CPU: 45% usage (normal)
    - RAM: 12 GB / 32 GB used (normal)
    - Plex storage: 8.2 TB / 12 TB available (normal)
    - Active streams: 3 (2 direct play, 1 transcode)

    2. **Analysis**: The server is operational. Performance appears within normal range.

    3. **Conclusion**: The reported issue is likely related to the client or stream
    configuration (see Plex diagnostics for further details).

    Keep your response concise, factual, and technical.
""",
    output_key="server_diagnostic",
    after_agent_callback=logging_callbacks.on_agent_end,
)

# ─────────────────────────────────────────────────────────────────────────────
# ParallelAgent : Les deux vérifications s'exécutent simultanément
# ─────────────────────────────────────────────────────────────────────────────
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
