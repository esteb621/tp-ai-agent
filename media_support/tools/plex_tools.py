"""
Outil pour la vérification des flux Plex via Tautulli.

Interroge l'API de Tautulli pour diagnostiquer les problèmes de lecture d'un
utilisateur spécifique (transcodage, sous-titres, etc.).
"""
import os
import requests

TAUTULLI_URL = os.getenv("TAUTULLI_URL", "http://localhost:8181")
TAUTULLI_API_KEY = os.getenv("TAUTULLI_API_KEY", "")


def check_plex_playback(user: str) -> dict:
    """
    Vérifie l'état du flux de lecture Plex pour un utilisateur donné via Tautulli.

    Args:
        user (str): Le nom d'utilisateur Plex.

    Returns:
        dict: Dictionnaire de diagnostic.
    """
    if not user or not isinstance(user, str):
        return {
            "status": "error",
            "user": "inconnu",
            "error": "Le nom d'utilisateur Plex ne peut pas être vide.",
            "transcoding": False,
            "missing_subtitles": False,
        }

    if not TAUTULLI_API_KEY:
        return {
            "status": "error",
            "user": user,
            "error": "TAUTULLI_API_KEY n'est pas configurée.",
            "transcoding": False,
            "missing_subtitles": False,
        }

    try:
        r = requests.get(
            f"{TAUTULLI_URL}/api/v2",
            params={"apikey": TAUTULLI_API_KEY, "cmd": "get_activity"},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            sessions = data.get("response", {}).get("data", {}).get("sessions", [])

            for session in sessions:
                session_user = session.get("user", "")
                session_username = session.get("username", "")

                if session_user.lower() == user.lower() or session_username.lower() == user.lower():
                    # Session trouvée
                    transcode_decision = session.get("transcode_decision", "direct play")
                    video_decision = session.get("video_decision", "direct play")
                    is_transcoding = transcode_decision != "direct play" or video_decision != "direct play"
                    
                    subtitle_lang = session.get("subtitle_language", "")
                    has_subtitles = session.get("subtitles", "none").lower() != "none" and subtitle_lang

                    media_title = session.get("full_title", session.get("title", "Titre Inconnu"))

                    print(f"[Tautulli] 🔍 Session trouvée pour l'utilisateur '{user}'")
                    print(f"[Tautulli] 🎬 Média : {media_title}")

                    return {
                        "status": "active",
                        "user": session_username or session_user or user,
                        "media_title": media_title,
                        "transcoding": is_transcoding,
                        "transcode_reason": session.get("transcode_video_reason", ""),
                        "missing_subtitles": not has_subtitles,
                        "subtitle_language": subtitle_lang if has_subtitles else "Aucun",
                        "bitrate_kbps": int(session.get("bitrate", "0")),
                        "resolution": session.get("video_resolution", ""),
                    }

            # Si on arrive ici, l'utilisateur n'a pas de session active
            return {
                "status": "inactive",
                "user": user,
                "transcoding": False,
                "missing_subtitles": False,
            }
        else:
            return {
                "status": "error",
                "user": user,
                "error": f"Erreur de l'API Tautulli: HTTP {r.status_code}",
                "transcoding": False,
                "missing_subtitles": False,
            }

    except Exception as e:
        return {
            "status": "error",
            "user": user,
            "error": f"Impossible de se connecter à Tautulli : {str(e)}",
            "transcoding": False,
            "missing_subtitles": False,
        }
