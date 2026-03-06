from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool
from google.genai.types import GenerateContentConfig
from media_support.tools.arr_tools import (
    get_stuck_downloads, 
    search_and_replace_release,
    get_available_releases,
    download_release
)
from media_support.agents.comms_bot import comms_bot
from media_support.callbacks.logging_callbacks import on_tool_start, on_agent_end
import os
from dotenv import load_dotenv

MISTRAL_MODEL = LiteLlm(
    model="ollama/mistral:latest",
    api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
)


arr_bot = LlmAgent(
    name="ArrBot",
    model=MISTRAL_MODEL,
    generate_content_config=GenerateContentConfig(
        temperature=0.2
    ),
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

    ---

    ## PROCEDURE — 3 STEPS IN ORDER (DONT SKIP ONE OF THEM)

    STEP 1 — Call `get_stuck_downloads` and specify the media type (serie or film).
    You can guess the media type depending your knowledge
    → You will get a list of items from 'queue' (stuck) or 'wanted' (missing).
    → If empty: STOP. Else: Proceed.

    STEP 2 — For each item:
    → OPTION A: If it's a simple stuck download, call `search_and_replace_release(media_name)`.
    → OPTION B (Manual): Call `get_available_releases(media_id, media_type)` to see what is available on indexers.
        *   Pick the best one (usually highest seeders/quality) and call `download_release(guid, media_type)`.

    STEP 3 — OUTPUT YOUR REPORT
    You have finished using tools. Now write a plain text summary directly in your response.
    No tool call. No function call. Just text.

    Format:
    - Media: <name>
    - Issue: <what was wrong>
    - Action: <what you did>
    - Solution: <what you can do>
    - Result: <success or failure>

    STOP after writing this. Your turn is over.
""",
    tools=[
        get_stuck_downloads,
        search_and_replace_release,
        get_available_releases,
        download_release,
    ],
    output_key="maintenance_report",  # Le rapport est stocké dans le state partagé
    before_tool_callback=on_tool_start,
    after_agent_callback=on_agent_end,
)
