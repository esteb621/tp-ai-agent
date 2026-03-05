"""
main.py — Script de démarrage programmatique du système multi-agents.

Ce script instancie manuellement le Runner ADK avec InMemorySessionService,
permettant :
  1. D'exécuter une session de démonstration de la routine de maintenance
  2. De vérifier que tous les composants fonctionnent correctement
  3. D'être utilisé en CI/CD ou pour des tests unitaires

Note : Pour la démo interactive, utiliser `adk web` depuis la racine du projet.
       Ce script est le runner programmatique requis par le cahier des charges du TP.
"""

import asyncio
import os
from dotenv import load_dotenv

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

# Charger les variables d'environnement (.env)
load_dotenv()

# Import de l'agent racine depuis le package media_support
from media_support.agent import root_agent


# ─────────────────────────────────────────────────────────────────────────────
# Configuration de l'application
# ─────────────────────────────────────────────────────────────────────────────
APP_NAME = "media_support_system"
USER_ID = "demo_admin"
SESSION_ID = "demo_session_001"


async def run_demo_maintenance() -> None:
    """
    Exécute une session de démonstration de la routine de maintenance proactive.

    Instancie le Runner programmatique avec InMemorySessionService et envoie
    la commande de maintenance pour démontrer le flux complet :
      TriageBot → MaintenanceWorkflow → ArrBot → CommsBot → DM Discord simulé
    """
    print("\n" + "=" * 70)
    print("🎬  DÉMO — Système Multi-Agents Support Média")
    print("    Framework : Google ADK | Modèles : Mistral + Llama 3.2 (Ollama)")
    print("=" * 70)

    # ── 1. Initialisation du service de session en mémoire ─────────────────
    session_service = InMemorySessionService()
    print("\n✅ InMemorySessionService initialisé")

    # ── 2. Création de la session ──────────────────────────────────────────
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
        state={},  # State initial vide — sera rempli par output_key des agents
    )
    print(f"✅ Session créée : {SESSION_ID} (utilisateur : {USER_ID})\n")

    # ── 3. Instanciation du Runner avec l'agent racine ─────────────────────
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )
    print(f"✅ Runner instancié avec l'agent racine : {root_agent.name}\n")

    # ── 4. Définition du message de déclenchement ──────────────────────────
    demo_message = "Lance la routine de maintenance"
    print(f"📨 Envoi de la commande : '{demo_message}'")
    print("-" * 70)

    # ── 5. Exécution de la session ─────────────────────────────────────────
    user_input = Content(
        role="user",
        parts=[Part(text=demo_message)],
    )

    final_response = None
    try:
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=SESSION_ID,
            new_message=user_input,
        ):
            if event.is_final_response():
                final_response = event
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            print(f"\n🤖 Réponse finale de {root_agent.name} :")
                            print("-" * 70)
                            print(part.text)
                            print("-" * 70)
    except Exception as e:
        err = str(e)
        if "not found" in err and "Tool" in err:
            print(f"\n⚠️  Hallucination de tool : {err.split(chr(10))[0]}")
            print("   → Limitation des modèles locaux Ollama. La démo adk web est plus stable.")
        else:
            print(f"\n❌  Erreur inattendue : {e}")

    # ── 6. Affichage de l'état final du state partagé ─────────────────────
    final_session = await session_service.get_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID,
    )

    if final_session and final_session.state:
        print("\n📊 État final du State partagé (InMemorySessionService) :")
        for key, value in final_session.state.items():
            print(f"  ├─ {key}: {str(value)[:150]}{'...' if len(str(value)) > 150 else ''}")
    else:
        print("\n📊 State partagé : vide (aucune donnée persistée)")

    print("\n" + "=" * 70)
    print("✅  Démonstration terminée avec succès !")
    print("    → Pour la démo interactive, lancez : adk web")
    print("=" * 70 + "\n")


async def run_demo_support() -> None:
    """
    Exécute une session de démonstration du mode support réactif.

    Simule un utilisateur qui se plaint de saccades dans sa lecture Plex,
    déclenchant le SupportWorkflow en parallèle (PlexCheckBot + ServerCheckBot).
    """
    print("\n" + "=" * 70)
    print("🔍  DÉMO — Mode Support Réactif (problème de lecture)")
    print("=" * 70)

    session_service = InMemorySessionService()

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id="demo_session_support",
        state={},
    )

    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    demo_message = "Bonjour, mon film saccade depuis ce soir, il manque aussi les sous-titres français"
    print(f"📨 Message utilisateur : '{demo_message}'")
    print("-" * 70)

    user_input = Content(
        role="user",
        parts=[Part(text=demo_message)],
    )

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id="demo_session_support",
        new_message=user_input,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        print(f"\n🤖 Réponse finale de {root_agent.name} :")
                        print("-" * 70)
                        print(part.text)
                        print("-" * 70)

    print("\n" + "=" * 70)
    print("✅  Démo support terminée !")
    print("=" * 70 + "\n")


def main() -> None:
    """
    Point d'entrée principal du script de démonstration.

    Lance les deux scénarios de démonstration :
      1. Mode Proactif (maintenance)
      2. Mode Réactif (support utilisateur)
    """
    # Vérification qu'Ollama est accessible (tous les modèles tournent en local)
    from media_support.tools.arr_tools import get_stuck_downloads
    test =get_stuck_downloads(media_name="Attaque des titans")
    print(test)
    # import urllib.request
    # try:
    #     urllib.request.urlopen("http://localhost:11434", timeout=2)
    #     print("✅ Ollama détecté sur localhost:11434 — modèles Mistral + Llama 3.2 disponibles\n")
    # except Exception:
    #     print("⚠️  ATTENTION : Ollama n'est pas démarré ou inaccessible sur localhost:11434 !")
    #     print("   → Lancez Ollama avec : ollama serve")
    #     print("   → Vérifiez les modèles : ollama pull mistral && ollama pull llama3.2\n")

    # # Lancement de la démo maintenance (mode proactif)
    # print("\n🚀 Lancement du scénario 1 : Routine de maintenance proactive")
    # asyncio.run(run_demo_maintenance())

    # # Lancement de la démo support (mode réactif)
    # print("\n🚀 Lancement du scénario 2 : Support réactif (problème de lecture)")
    # asyncio.run(run_demo_support())


if __name__ == "__main__":
    main()
