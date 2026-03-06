"""
MaintenanceWorkflow — Workflow séquentiel de maintenance proactive.

Type   : SequentialAgent (Workflow Agent ADK)
Séquence : ArrBot → CommsBot

Ce workflow orchestre la routine de maintenance en deux phases séquentielles :
  1. ArrBot analyse les blocages, tente les réparations et génère le rapport
     (stocké dans le state via output_key="maintenance_report")
  2. CommsBot lit le rapport depuis le state (via {maintenance_report})
     et envoie les DM Discord aux utilisateurs concernés.

Déclenché par : transfer_to_agent depuis TriageBot sur commande "maintenance".
"""

from google.adk.agents import SequentialAgent

from media_support.agents.arr_bot import arr_bot
from media_support.agents.comms_bot import comms_bot
# ─────────────────────────────────────────────────────────────────────────────
# SequentialAgent : Workflow de maintenance
# L'ordre d'exécution est garanti : ArrBot PUIS CommsBot
# Le state partagé (maintenance_report) est automatiquement transmis entre les deux.
# ─────────────────────────────────────────────────────────────────────────────
maintenance_workflow = SequentialAgent(
    name="MaintenanceWorkflow",
    description=(
        "Workflow de maintenance proactive. "
        "Exécute séquentiellement ArrBot (analyse + réparation des downloads bloqués) "
        "puis CommsBot en tant qu'outil (notification Discord des utilisateurs concernés)."
    ),
    sub_agents=[
        arr_bot
    ],
)
