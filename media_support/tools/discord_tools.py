"""
Outil de simulation pour l'envoi de messages Discord (DM).

Les messages sont affichés dans la console (visible dans le terminal adk web).
Pour une intégration réelle, remplacer par l'API REST Discord avec DISCORD_BOT_TOKEN.
"""


def send_discord_dm(discord_id: str, message: str) -> str:
    """
    Simule l'envoi d'un message privé (DM) à un utilisateur Discord.

    Affiche le message formaté dans la console du terminal `adk web`,
    ce qui permet de voir le résultat directement dans l'interface.

    Args:
        discord_id (str): L'identifiant Discord de l'utilisateur destinataire.
        message (str): Le contenu du message à envoyer (max 2000 caractères).

    Returns:
        str: Confirmation d'envoi ou message d'erreur.
    """
    try:
        if not discord_id or not isinstance(discord_id, str):
            raise ValueError("L'identifiant Discord ne peut pas être vide.")
        if not message or not isinstance(message, str):
            raise ValueError("Le message ne peut pas être vide.")
        if len(message) > 2000:
            message = message[:1997] + "..."

        # Affichage console — visible dans le terminal adk web
        print("\n" + "=" * 60)
        print(f"📨 Discord DM → {discord_id}")
        print("-" * 60)
        print(message)
        print("=" * 60 + "\n")

        return f"SUCCESS: Message envoyé à {discord_id}"

    except Exception as e:
        error_msg = f"ERROR: Impossible d'envoyer le DM à '{discord_id}' : {str(e)}"
        print(f"❌ {error_msg}")
        return error_msg
