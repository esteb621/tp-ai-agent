"""
CommsBot — Agent chargé de la communication Discord.

Modèle : Mistral (via Ollama)
Rôle   : Rédiger des messages empathiques et les envoyer via send_discord_dm.

Ce bot dispose d'UN SEUL outil : send_discord_dm.
Il NE DOIT PAS chercher à récupérer le rapport via un outil — il est fourni
directement dans le contexte de ses instructions via le state partagé.
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from media_support.callbacks.logging_callbacks import on_tool_start, on_agent_end

# ─────────────────────────────────────────────────────────────────────────────
# Modèle : Mistral via Ollama (local, sans clé API)
# ─────────────────────────────────────────────────────────────────────────────
MISTRAL_MODEL = LiteLlm(model="ollama/mistral")

# ─────────────────────────────────────────────────────────────────────────────
# Définition de l'agent CommsBot
# ─────────────────────────────────────────────────────────────────────────────
comms_bot = LlmAgent(
    name="CommsBot",
    model=MISTRAL_MODEL,
    description=(
        "Discord communication agent. Writes empathetic messages to proactively "
        "inform users about the status of their media requests and outputs them as text."
    ),
    instruction="""You are CommsBot, the communication agent for the media support team.

## YOUR TASK

You do NOT have any tools. Your job is to output the message directly as text.

---

## INPUT DATA (Maintenance Report or User Request)

{request}

---

## YOUR TASK

Read the maintenance report above and:

1. Write a friendly, empathetic Discord message in French that includes:
   - 👋 A warm greeting
   - 📺 The media name
   - ❌ Why the download was stuck (in simple terms, no jargon)
   - ✅ What was done to fix it (new release found, or failed)
   - ⏱️ If fixed: "disponible dans ~1-2h" / If failed: "notre équipe continue de chercher"

2. Output this message as your final textual response. Do NOT try to call any tools.
""",
    tools=[],
    output_key="discord_comms_report",  # Stocke le rapport d'envoi dans le state
    before_tool_callback=on_tool_start,
    after_agent_callback=on_agent_end,
)
