"""
Outil pour la vérification des flux Plex via Tautulli.

Interroge l'API de Tautulli pour diagnostiquer les problèmes de lecture d'un
utilisateur spécifique (transcodage, sous-titres, etc.).
"""
import os
import requests
from typing import Optional

TAUTULLI_URL = os.getenv("TAUTULLI_URL", "http://localhost:8181")
TAUTULLI_API_KEY = os.getenv("TAUTULLI_API_KEY", "")
APP_MODE = os.getenv("APP_MODE", "mock").lower()

class RawAPI:
    """Wrapper minimaliste pour l'API Tautulli utilisant requests."""
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _get(self, cmd: str, params: Optional[dict] = None) -> requests.Response:
        url = f"{self.base_url}/api/v2"
        query_params = {"apikey": self.api_key, "cmd": cmd}
        if params:
            query_params.update(params)
        return requests.get(url, params=query_params, timeout=10)

    def activity(self) -> requests.Response:
        return self._get("get_activity")

api = RawAPI(base_url=TAUTULLI_URL, api_key=TAUTULLI_API_KEY)



def response(text: str) -> str:
    """
    Outil de réponse. Obligatoire pour retourner le diagnostic final.
    
    Args:
        text (str): Le contenu de ton message de réponse.
    """
    return text

def check_plex_playback(media_name: str) -> dict:
    """
    Vérifie l'état du flux de lecture Plex pour un média donné via Tautulli.

    Args:
        media_name (str): Le titre du média.

    Returns:
        dict: Dictionnaire de diagnostic.
    """
    if not media_name or not isinstance(media_name, str):
        return {
            "status": "error",
            "media_name": "inconnu",
            "error": "Le nom du média ne peut pas être vide.",
            "transcoding": False,
            "missing_subtitles": False,
        }

    if APP_MODE == "mock":
        print(f"[Tautulli] (MOCK) Simulation d'une session pour '{media_name}'")
        return {
            "status": "active",
            "user": "demo_user",
            "media_title": media_name,
            "transcoding": True,
            "transcode_reason": "Bitrate exceeds limit",
            "missing_subtitles": True,
            "subtitle_language": "Aucun",
            "bitrate_kbps": 8000,
            "resolution": "1080p",
        }

    if not TAUTULLI_API_KEY:
        return {
            "status": "error",
            "media_name": media_name,
            "error": "TAUTULLI_API_KEY n'est pas configurée.",
            "transcoding": False,
            "missing_subtitles": False,
        }

    try:
        r = api.activity()
        if r.status_code == 200:
            data = r.json()
            sessions = data.get("response", {}).get("data", {}).get("sessions", [])

            for session in sessions:
                media_title = session.get("full_title", session.get("title", "Titre Inconnu"))

                if media_name.lower() in media_title.lower():
                    # Session trouvée
                    transcode_decision = session.get("transcode_decision", "direct play")
                    video_decision = session.get("video_decision", "direct play")
                    is_transcoding = transcode_decision != "direct play" or video_decision != "direct play"
                    
                    subtitle_lang = session.get("subtitle_language", "")
                    has_subtitles = session.get("subtitles", "none") != "none" and subtitle_lang

                    session_username = session.get("username", session.get("user", "Inconnu"))

                    print(f"[Tautulli] 🔍 Session trouvée pour le média '{media_title}' (utilisateur: {session_username})")

                    return {
                        "status": "active",
                        "user": session_username,
                        "media_title": media_title,
                        "transcoding": is_transcoding,
                        "transcode_reason": session.get("transcode_video_reason", ""),
                        "missing_subtitles": not has_subtitles,
                        "subtitle_language": subtitle_lang if has_subtitles else "Aucun",
                        "bitrate_kbps": int(session.get("bitrate", "0")),
                        "resolution": session.get("video_resolution", ""),
                    }

            # Si on arrive ici, l'utilisateur n'a pas de session active pour ce média
            return {
                "status": "inactive",
                "media_name": media_name,
                "transcoding": False,
                "missing_subtitles": False,
            }
        else:
            return {
                "status": "error",
                "media_name": media_name,
                "error": f"Erreur de l'API Tautulli: HTTP {r.status_code}",
                "transcoding": False,
                "missing_subtitles": False,
            }

    except Exception as e:
        return {
            "status": "error",
            "media_name": media_name,
            "error": f"Impossible de se connecter à Tautulli : {str(e)}",
            "transcoding": False,
            "missing_subtitles": False,
        }


def check_server_health() -> dict:
    """
    Vérifie l'état du serveur Plex via Tautulli.

    Returns:
        dict: Dictionnaire de diagnostic.
    """
    if APP_MODE == "mock":
        return {
            
        }

    if not TAUTULLI_API_KEY:
        return {
            "status": "error",
            "error": "TAUTULLI_API_KEY n'est pas configurée.",
        }

    try:
        r = api.activity()
        if r.status_code == 200:
            data = r.json()
            sessions = data.get("response", {}).get("data", {}).get("sessions", [])

            return {
                "status": "active",
                "sessions": sessions,
            }
        else:
            return {
                "status": "error",
                "error": f"Erreur de l'API Tautulli: HTTP {r.status_code}",
            }

    except Exception as e:
        return {
            "status": "error",
            "error": f"Impossible de se connecter à Tautulli : {str(e)}",
        }