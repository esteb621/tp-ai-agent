"""
CommsBot — Agent chargé de la communication Discord.

Modèle : Mistral (via Ollama)
Rôle   : Rédiger des messages empathiques et les envoyer via send_discord_dm.

Ce bot dispose d'UN SEUL outil : send_discord_dm.
Il NE DOIT PAS chercher à récupérer le rapport via un outil — il est fourni
directement dans le contexte de ses instructions via le state partagé.
"""

from google.genai.types import GenerateContentConfig
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from media_support.callbacks.logging_callbacks import on_tool_start, on_agent_end

# ─────────────────────────────────────────────────────────────────────────────
# Modèle : Mistral via Ollama (local, sans clé API)
# ─────────────────────────────────────────────────────────────────────────────
import os
from dotenv import load_dotenv

load_dotenv()

MISTRAL_MODEL = LiteLlm(
    model="ollama/mistral:latest",
    api_base=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
)

# ─────────────────────────────────────────────────────────────────────────────
# Définition de l'agent CommsBot
# ─────────────────────────────────────────────────────────────────────────────
comms_bot = LlmAgent(
    name="CommsBot",
    model=MISTRAL_MODEL,
    generate_content_config=GenerateContentConfig(
        temperature=0.2
    ),
    description=(
        "Discord communication agent. Writes empathetic messages to proactively "
        "inform users about the status of their media requests and outputs them as text."
    ),
    instruction="""You are CommsBot, the communication agent for the media support team.

        ## YOUR TASK
        Read the maintenance report from `maintenance_report` in the session state and write a single Discord message. That's it.

        ---

        ## INPUT DATA
        (This is provided in the message you receive from the user or the workflow)

        ---
        ## INPUT HANDLING
        - You may receive the report as raw JSON or unstructured text.
        - DO NOT mention that the data is JSON. DO NOT analyze the structure (e.g. "The error_message field is null").
        - Pluck ONLY the problem and resolution out of the input and construct your message normally.

        ---
        ## OUTPUT RULES
        - Plain text only
        - No JSON, no code, no tool calls
        - One message, straight to the point
        - Same language as the original user request

        ---

        ## STYLE
        - Discord casual, like a real person typing
        - No greetings, no "Hello!", no sign-off
        - No corporate tone, no "we apologize for the inconvenience"
        - Short sentences, direct
        - 1-2 emojis max if it feels natural

        ---

        ## MESSAGE STRUCTURE (in order)
        1. Media name — lead with it
        2. What went wrong — simple words, zero jargon
        3. What was done + outcome:
        - Fixed → "ça arrive dans ~1-2h"
        - Not fixed → "on est dessus, pas d'ETA pour l'instant"

        ---
""",
    tools=[],
    output_key="discord_comms_report",  # Stocke le rapport d'envoi dans le state
    before_tool_callback=on_tool_start,
    after_agent_callback=on_agent_end,
)
