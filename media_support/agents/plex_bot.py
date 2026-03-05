from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.genai.types import GenerateContentConfig
from google.adk.tools.agent_tool import AgentTool

from media_support.tools import plex_tools
from media_support.agents import comms_bot
from media_support.callbacks.logging_callbacks import on_tool_start, on_agent_end

# ─────────────────────────────────────────────────────────────────────────────
# Modèle : Mistral via Ollama (local, sans clé API)
# ─────────────────────────────────────────────────────────────────────────────
MISTRAL_MODEL = LiteLlm(model="ollama/mistral:latest")


# CommsBot en tant qu'outil
comms_bot_tool = AgentTool(
    agent=comms_bot
)
# ─────────────────────────────────────────────────────────────────────────────
# Agent 1 : PlexCheckBot
# Diagnostique le flux Plex de l'utilisateur signalant le problème
# ─────────────────────────────────────────────────────────────────────────────
plex_check_bot = LlmAgent(
    name="PlexCheckBot",
    model=MISTRAL_MODEL,
    generate_content_config=GenerateContentConfig(
        temperature=0.2
    ),
    description="Agent de diagnostic Plex. Vérifie le flux de lecture d'un utilisateur.",
    instruction="""Tu es PlexCheckBot, spécialiste du diagnostic de flux Plex.
    
    ## YOUR TOOLS — USE ONLY THESE 2, NEVER INVENT OTHERS

    | Tool name (exact)            | Arguments                     | Purpose                                  |
    |------------------------------|-------------------------------|------------------------------------------|
    | check_plex_playback          | user: str                     | Get the current playback status          |
    | CommsBot                     | request: str                  | Send the final message to the user       |

    ## PROCEDURE — 2 STEPS IN ORDER
    
    1. Call `check_plex_playback` pour diagnostiquer le flux Plex de l'utilisateur (avec "utilisateur_plex" si non spécifié).
    2. Format your diagnosis into a clear text summary and call `CommsBot` with this text as the `request` argument.
    
    CRITICAL: ONCE YOU HAVE CALLED `CommsBot`, YOU MUST OUTPUT EXACTLY THE TEXT "STATUS: DONE" TO FINISH YOUR TURN.
    DO NOT WRITE ANYTHING ELSE. DO NOT CALL ANY MORE TOOLS.
    """,
    tools=[plex_tools.check_plex_playback, comms_bot_tool],
    output_key="plex_diagnostic",  # Stocke le diagnostic dans le state
    before_tool_callback=on_tool_start,
    after_agent_callback=on_agent_end,
)