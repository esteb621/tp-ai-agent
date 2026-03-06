from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.models.lite_llm import LiteLlm
from ..callbacks import logging_callbacks
from google.genai.types import GenerateContentConfig

import os
from dotenv import load_dotenv
from media_support.tools import plex_tools
load_dotenv()

MISTRAL_MODEL = LiteLlm(
    model="ollama/mistral:latest",
    api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
)

server_check_bot = LlmAgent(
    name="ServerCheckBot",
    model=MISTRAL_MODEL,
    generate_content_config=GenerateContentConfig(
        temperature=0.2
    ),
    description="Media server health check agent.",
    instruction="""You are ServerCheckBot, a media server monitoring agent.

    A user has reported an issue. Without any additional tools available,
    perform a simulated server health check and return a report including:

    1. **Overall server status**: 

    2. **Analysis**: The server is operational. Performance appears within normal range.

    3. **Conclusion**: The reported issue is likely related to the client or stream
    configuration (see Plex diagnostics for further details).

    Keep your response concise, factual, and technical.
    
    CRITICAL INSTRUCTION: JUST OUTPUT THE SYSTEM STATUS. 
    DO NOT WRITE ANY FUNCTION CALL. DO NOT INVENT TOOLS like "diagnose", "response", or "reply".
    STOP COMPLETELY AFTER REPORTING THE METRICS.
""",
    output_key="server_diagnostic",
    tools=[plex_tools.check_server_health],
    after_agent_callback=logging_callbacks.on_agent_end,
)