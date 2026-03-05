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

MISTRAL_MODEL = LiteLlm(model="ollama/mistral:latest")

comms_bot_tool = AgentTool(
    agent=comms_bot
)

arr_bot = LlmAgent(
    name="ArrBot",
    model=MISTRAL_MODEL,
    description=(
        "Technician agent specialized in stuck downloads (Sonarr/Radarr). "
        "Analyzes failed downloads, searches for alternative releases. "
        "The output is a maintenance report that will be analyzed by other agents."
    ),
    instruction="""You are ArrBot, the media server download technician.

    ## YOUR TOOLS — USE ONLY THESE 3, NEVER INVENT OTHERS

    | Tool name (exact)            | Arguments                     | Purpose                                  |
    |------------------------------|-------------------------------|------------------------------------------|
    | get_stuck_downloads          | media_type: str | Get stuck (queue) and missing (wanted) |
    | search_and_replace_release   | media_name: str               | Automated search & replace               |
    | get_available_releases       | media_id: int, media_type: str | Search indexers for available torrents   |
    | download_release             | guid: str, media_type: str    | Grab a specific torrent from indexers    |

    CRITICAL: NEVER call a tool whose name is not in the table above.
    NEVER invent tool names like "perform_maintenance", "analyse_probleme", etc.
    If you need a capability not covered by these tools, just write about it in text.

    ---

    ## PROCEDURE — 3 STEPS IN ORDER

    STEP 1 — Call `get_stuck_downloads` and specify the media type (serie or film).
    → You will get a list of items from 'queue' (stuck) or 'wanted' (missing).
    → If empty: STOP. Else: Proceed.

    STEP 2 — For each item:
    → OPTION A: If it's a simple stuck download, call `search_and_replace_release(media_name)`.
    → OPTION B (Manual): Call `get_available_releases(media_id, media_type)` to see what is available on indexers.
        *   Pick the best one (usually highest seeders/quality) and call `download_release(guid, media_type)`.

    STEP 3 — Call `comms_bot_tool` to communicate the outcome to the user.
    CRITICAL: YOU MUST FORMAT YOUR FINDINGS INTO A READABLE TEXT REPORT (e.g., "media_name | Issue | Action taken | Result").
    THEN pass this TEXT REPORT as the `request` argument to `comms_bot_tool`.
    DO NOT pass raw JSON data from your tool outputs. The user will not understand JSON.
    
    CRITICAL INSTRUCTION FOR STEP 3: You MUST use `comms_bot_tool` to send the final report. 
    Once `comms_bot_tool` finishes, YOU MUST OUTPUT EXACTLY THE TEXT "STATUS: DONE" TO FINISH YOUR TURN.
    DO NOT WRITE ANYTHING ELSE. DO NOT CALL ANY MORE TOOLS.
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
