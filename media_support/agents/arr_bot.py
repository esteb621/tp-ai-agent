"""
ArrBot — Agent technicien chargé des téléchargements bloqués.

Modèle : Mistral (via Ollama) — meilleur que Llama 3.2 pour le function calling
Rôle   : Exécuter la routine de maintenance proactive.
          - Récupère la liste des téléchargements bloqués via get_stuck_downloads
          - Tente de trouver une release alternative via search_and_replace_release
          - Invoque CommsBot comme outil (AgentTool) pour notifier les utilisateurs
          - Génère un rapport détaillé stocké dans output_key="maintenance_report"
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool

from media_support.tools.arr_tools import (
    get_stuck_downloads, 
    search_and_replace_release,
    get_available_releases,
    download_release
)
from media_support.agents.comms_bot import comms_bot
from media_support.callbacks.logging_callbacks import on_tool_start, on_agent_end

# ─────────────────────────────────────────────────────────────────────────────
# Modèle : Mistral via Ollama — meilleur support du function calling
# Llama 3.2 avait tendance à halluciner des noms de tools inexistants
# ─────────────────────────────────────────────────────────────────────────────
MISTRAL_MODEL = LiteLlm(model="ollama/mistral")

# ─────────────────────────────────────────────────────────────────────────────
# AgentTool : CommsBot est invoqué par ArrBot comme un outil.
# C'est le mécanisme de délégation "AgentTool" requis par le TP.
# ─────────────────────────────────────────────────────────────────────────────
comms_bot_tool = AgentTool(agent=comms_bot)

# ─────────────────────────────────────────────────────────────────────────────
# Définition de l'agent ArrBot
# ─────────────────────────────────────────────────────────────────────────────
arr_bot = LlmAgent(
    name="ArrBot",
    model=MISTRAL_MODEL,
    description=(
        "Technician agent specialized in stuck downloads (Sonarr/Radarr). "
        "Analyzes failed downloads, searches for alternative releases, "
        "and triggers user communication via CommsBot."
    ),
    instruction="""You are ArrBot, the media server download technician.

## YOUR TOOLS — USE ONLY THESE 3, NEVER INVENT OTHERS

| Tool name (exact)            | Arguments                     | Purpose                                  |
|------------------------------|-------------------------------|------------------------------------------|
| get_stuck_downloads          | media_type: str, media_name: str | Get stuck (queue) and missing (wanted) |
| search_and_replace_release   | media_name: str               | Automated search & replace               |
| get_available_releases       | media_id: int, media_type: str | Search indexers for available torrents   |
| download_release             | guid: str, media_type: str    | Grab a specific torrent from indexers    |
| CommsBot                     | request: str                  | Inform users via Discord                 |

CRITICAL: NEVER call a tool whose name is not in the table above.
NEVER invent tool names like "perform_maintenance", "analyse_probleme", etc.
If you need a capability not covered by these tools, just write about it in text.

---

## PROCEDURE — 4 STEPS IN ORDER

STEP 1 — Call `get_stuck_downloads` (media_type="all" or specific).
  → You will get a list of items from 'queue' (stuck) or 'wanted' (missing).
  → If empty: STOP. Else: Proceed.

STEP 2 — For each item:
  → OPTION A: If it's a simple stuck download, call `search_and_replace_release(media_name)`.
  → OPTION B (Manual): Call `get_available_releases(media_id, media_type)` to see what is available on indexers.
      *   Pick the best one (usually highest seeders/quality) and call `download_release(guid, media_type)`.

STEP 3 — Write the maintenance report summarizing actions:
[media_name] | [Issue] | [Action taken: Auto-Search or Manual Grab] | [Result]

STEP 4 — Call `CommsBot` with the report in the `request` argument.
""",
    tools=[
        get_stuck_downloads,
        search_and_replace_release,
        get_available_releases,
        download_release,
        comms_bot_tool,
    ],
    output_key="maintenance_report",  # Le rapport est stocké dans le state partagé
    before_tool_callback=on_tool_start,
    after_agent_callback=on_agent_end,
)
