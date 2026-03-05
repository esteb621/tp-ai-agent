"""
Outils pour interagir avec les APIs de Sonarr et Radarr (Arr Stack).

Ces outils utilisent les bibliothèques officielles `sonarr-py` et `radarr-py`
pour récupérer les informations sur les téléchargements bloqués et lancer de nouvelles recherches.
"""
import os
import re
from typing import Optional, List, Dict, Any

import sonarr
from sonarr.api.queue_api import QueueApi as SonarrQueueApi
from sonarr.api.command_api import CommandApi as SonarrCommandApi
from sonarr.api.series_lookup_api import SeriesLookupApi
from sonarr.api.missing_api import MissingApi as SonarrMissingApi
from sonarr.api.release_api import ReleaseApi as SonarrReleaseApi
from sonarr.models.command_resource import CommandResource as SonarrCommandResource

import radarr
from radarr.api.queue_api import QueueApi as RadarrQueueApi
from radarr.api.command_api import CommandApi as RadarrCommandApi
from radarr.api.movie_lookup_api import MovieLookupApi
from radarr.api.missing_api import MissingApi as RadarrMissingApi
from radarr.api.release_api import ReleaseApi as RadarrReleaseApi
from radarr.models.command_resource import CommandResource as RadarrCommandResource

SONARR_URL = os.getenv("SONARR_URL", "http://localhost:8989")
SONARR_API_KEY = os.getenv("SONARR_API_KEY", "")
RADARR_URL = os.getenv("RADARR_URL", "http://localhost:7878")
RADARR_API_KEY = os.getenv("RADARR_API_KEY", "")

# Global configuration objects for Sonarr and Radarr
SONARR_CONFIG = sonarr.Configuration(host=SONARR_URL)
SONARR_CONFIG.api_key['apikey'] = SONARR_API_KEY
SONARR_CONFIG.default_headers['X-Api-Key'] = SONARR_API_KEY

RADARR_CONFIG = radarr.Configuration(host=RADARR_URL)
RADARR_CONFIG.api_key['apikey'] = RADARR_API_KEY
RADARR_CONFIG.default_headers['X-Api-Key'] = RADARR_API_KEY


def get_stuck_downloads(media_type: str = "all", media_name: str | None = None) -> dict:
    """
    Récupère les médias bloqués (Queue) ou manquants (Wanted) depuis Sonarr/Radarr.
    Supporte le filtrage par regex sur le nom du média.
    """
    print(f"DEBUG: get_stuck_downloads - media_type={media_type}, media_name={media_name}")
    stuck = []
    has_errors = False
    error_messages = []
    
    # Prépare le regex si media_name est fourni
    name_regex = None
    if media_name:
        try:
            name_regex = re.compile(media_name, re.IGNORECASE)
        except Exception:
            name_regex = re.compile(re.escape(media_name), re.IGNORECASE)

    # --- Section Sonarr (Series/Episodes) ---
    if media_type in ["all", "serie"] and SONARR_API_KEY:
        try:
            with sonarr.ApiClient(SONARR_CONFIG) as api_client:
                # 1. Stuck in Queue
                queue_api = SonarrQueueApi(api_client)
                queue_page = queue_api.get_queue(page_size=100)
                for item in getattr(queue_page, "records", []):
                    title = getattr(item, "title", "Unknown")
                    if name_regex and not name_regex.search(title):
                        continue
                    
                    if getattr(item, "status", "").lower() not in ["completed", "downloading", "importing"]:
                        stuck.append({
                            "id": getattr(item, "id", None),
                            "media_type": "serie",
                            "media_name": title,
                            "series_id": getattr(item, "series_id", None),
                            "episode_id": getattr(item, "episode_id", None),
                            "status": getattr(item, "status", "unknown"),
                            "tracked_status": getattr(item, "tracked_download_state", "warning"),
                            "status_messages": [str(m) for m in getattr(item, "status_messages", [])],
                            "discord_id": "test_discord_id_123",
                            "source": "queue"
                        })

                # 2. Wanted (Missing)
                missing_api = SonarrMissingApi(api_client)
                missing_page = missing_api.get_wanted_missing(page_size=50)
                for record in getattr(missing_page, "records", []):
                    series_title = "Unknown Series"
                    if hasattr(record, "series"):
                        series_title = getattr(record.series, "title", "Unknown")
                    
                    if name_regex and not name_regex.search(series_title):
                        continue
                        
                    stuck.append({
                        "id": getattr(record, "id", None),
                        "media_type": "serie",
                        "media_name": f"{series_title} - S{getattr(record, 'season_number', 0):02}E{getattr(record, 'episode_number', 0):02}",
                        "series_id": getattr(record, "series_id", None),
                        "episode_id": getattr(record, "id", None),
                        "status": "Missing",
                        "tracked_status": "Wanted",
                        "status_messages": ["Episode is missing and not in queue"],
                        "discord_id": "test_discord_id_123",
                        "source": "wanted"
                    })
        except Exception as e:
            has_errors = True
            error_messages.append(f"Sonarr Error: {str(e)}")

    # --- Section Radarr (Movies) ---
    if media_type in ["all", "film"] and RADARR_API_KEY:
        try:
            with radarr.ApiClient(RADARR_CONFIG) as api_client:
                # 1. Stuck in Queue
                queue_api = RadarrQueueApi(api_client)
                queue_page = queue_api.get_queue(page_size=100)
                for item in getattr(queue_page, "records", []):
                    title = getattr(item, "title", "Unknown")
                    if name_regex and not name_regex.search(title):
                        continue

                    if getattr(item, "status", "").lower() not in ["completed", "downloading", "importing"]:
                        stuck.append({
                            "id": getattr(item, "id", None),
                            "media_type": "film",
                            "media_name": title,
                            "movie_id": getattr(item, "movie_id", None),
                            "status": getattr(item, "status", "unknown"),
                            "tracked_status": getattr(item, "tracked_download_state", "warning"),
                            "status_messages": [str(m) for m in getattr(item, "status_messages", [])],
                            "discord_id": "test_discord_id_radarr_456",
                            "source": "queue"
                        })

                # 2. Wanted (Missing)
                missing_api = RadarrMissingApi(api_client)
                missing_page = missing_api.get_wanted_missing(page_size=50)
                for record in getattr(missing_page, "records", []):
                    movie_title = getattr(record, "title", "Unknown Movie")
                    if name_regex and not name_regex.search(movie_title):
                        continue

                    stuck.append({
                        "id": getattr(record, "id", None),
                        "media_type": "film",
                        "media_name": movie_title,
                        "movie_id": getattr(record, "id", None),
                        "status": "Missing",
                        "tracked_status": "Wanted",
                        "status_messages": ["Movie is missing and not in queue"],
                        "discord_id": "test_discord_id_radarr_456",
                        "source": "wanted"
                    })
        except Exception as e:
            has_errors = True
            error_messages.append(f"Radarr Error: {str(e)}")

    return {
        "status": "error" if has_errors and not stuck else "success",
        "downloads": stuck,
        "error_message": "; ".join(error_messages) if error_messages else None
    }


def get_available_releases(media_id: int, media_type: str) -> dict:
    """
    Recherche les releases disponibles sur les indexeurs pour un ID donné.
    """
    releases = []
    try:
        if media_type == "serie":
            with sonarr.ApiClient(SONARR_CONFIG) as api_client:
                release_api = SonarrReleaseApi(api_client)
                results = release_api.list_release(episode_id=media_id)
                for r in results:
                    releases.append({
                        "guid": getattr(r, "guid", None),
                        "title": getattr(r, "title", "Unknown"),
                        "size": getattr(r, "size", 0),
                        "seeders": getattr(r, "seeders", 0),
                        "leechers": getattr(r, "leechers", 0),
                        "quality": getattr(r.quality, "quality", {}).get("name", "Unknown") if hasattr(r, "quality") else "Unknown",
                        "indexer": getattr(r, "indexer", "Unknown")
                    })
        else:
            with radarr.ApiClient(RADARR_CONFIG) as api_client:
                release_api = RadarrReleaseApi(api_client)
                results = release_api.list_release(movie_id=media_id)
                for r in results:
                    releases.append({
                        "guid": getattr(r, "guid", None),
                        "title": getattr(r, "title", "Unknown"),
                        "size": getattr(r, "size", 0),
                        "seeders": getattr(r, "seeders", 0),
                        "quality": getattr(r.quality, "quality", {}).get("name", "Unknown") if hasattr(r, "quality") else "Unknown",
                        "indexer": getattr(r, "indexer", "Unknown")
                    })
        
        releases.sort(key=lambda x: x["seeders"], reverse=True)
        return {"status": "success", "releases": releases[:10]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def download_release(guid: str, media_type: str) -> dict:
    """
    Lance le téléchargement d'une release spécifique via son GUID.
    """
    try:
        if media_type == "serie":
            with sonarr.ApiClient(SONARR_CONFIG) as api_client:
                release_api = SonarrReleaseApi(api_client)
                from sonarr.models.release_resource import ReleaseResource
                release_api.create_release(ReleaseResource(guid=guid))
        else:
            with radarr.ApiClient(RADARR_CONFIG) as api_client:
                release_api = RadarrReleaseApi(api_client)
                from radarr.models.release_resource import ReleaseResource
                release_api.create_release(ReleaseResource(guid=guid))
        
        return {"status": "success", "message": f"Release grabbed: {guid}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def search_and_replace_release(media_name: str) -> bool:
    """
    Déclenche une recherche automatique (SeriesSearch/MoviesSearch) via CommandApi.
    """
    if not media_name: return False
    try:
        with radarr.ApiClient(RADARR_CONFIG) as api_client:
            lookup_api = MovieLookupApi(api_client)
            movies = lookup_api.list_movie_lookup(term=media_name)
            if movies:
                movie_id = getattr(movies[0], "id", 0)
                if movie_id:
                    cmd_api = RadarrCommandApi(api_client)
                    cmd_api.create_command(RadarrCommandResource(name="MoviesSearch", movie_ids=[movie_id]))
                    return True
    except Exception: pass

    try:
        with sonarr.ApiClient(SONARR_CONFIG) as api_client:
            lookup_api = SeriesLookupApi(api_client)
            series = lookup_api.list_series_lookup(term=media_name)
            if series:
                series_id = getattr(series[0], "id", 0)
                if series_id:
                    cmd_api = SonarrCommandApi(api_client)
                    cmd_api.create_command(SonarrCommandResource(name="SeriesSearch", series_id=series_id))
                    return True
    except Exception: pass
    return False
