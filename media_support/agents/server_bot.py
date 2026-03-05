from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.models.lite_llm import LiteLlm
from ..callbacks import logging_callbacks
from google.genai.types import GenerateContentConfig

MISTRAL_MODEL = LiteLlm(model="ollama/mistral:latest")

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

    1. **Overall server status** (simulated):
    - CPU: 45% usage (normal)
    - RAM: 12 GB / 32 GB used (normal)
    - Plex storage: 8.2 TB / 12 TB available (normal)
    - Active streams: 3 (2 direct play, 1 transcode)

    2. **Analysis**: The server is operational. Performance appears within normal range.

    3. **Conclusion**: The reported issue is likely related to the client or stream
    configuration (see Plex diagnostics for further details).

    Keep your response concise, factual, and technical.
    
    CRITICAL INSTRUCTION: JUST OUTPUT THE SYSTEM STATUS. 
    DO NOT WRITE ANY FUNCTION CALL. DO NOT INVENT TOOLS like "diagnose", "response", or "reply".
    STOP COMPLETELY AFTER REPORTING THE METRICS.
""",
    output_key="server_diagnostic",
    after_agent_callback=logging_callbacks.on_agent_end,
)