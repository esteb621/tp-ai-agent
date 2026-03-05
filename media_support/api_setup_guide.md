# Guide de Configuration des APIs (Sonarr / Radarr / Tautulli)

Ce projet utilise désormais de véritables requêtes API vers Sonarr, Radarr et Tautulli pour récupérer des informations réelles sur vos médias plutôt que d'utiliser des données fictives ("mocker").

Pour que l'agent puisse communiquer avec ces services, vous devez fournir les URLs et les Clés API (API Keys) de chacun d'eux.

## 1. Récupérer vos clés API

### Sonarr

1. Ouvrez l'interface web de Sonarr.
2. Allez dans **Settings** > **General**.
3. Sous la section **Security**, copiez la valeur de `API Key`.
4. Notez également l'URL de votre Sonarr (ex: `http://localhost:8989`).

### Radarr

1. Ouvrez l'interface web de Radarr.
2. Allez dans **Settings** > **General**.
3. Sous la section **Security**, copiez la valeur de `API Key`.
4. Notez l'URL de votre Radarr (ex: `http://localhost:7878`).

### Tautulli (pour Plex)

1. Ouvrez l'interface web de Tautulli.
2. Allez dans **Settings** > **Web Interface**.
3. Descendez jusqu'à la section **API** et copiez `API Key` (ou générez-en une si elle n'existe pas).
4. Notez l'URL de Tautulli (ex: `http://localhost:8181`).

## 2. Configuration du fichier `.env`

À la racine du projet `Agent IA`, ouvrez (ou créez) le fichier `.env` et ajoutez les variables suivantes avec vos propres valeurs (remplacez les exemples par vos vraies infos) :

```env
# Configuration Sonarr
SONARR_URL=http://localhost:8989
SONARR_API_KEY=votre_cle_api_sonarr_ici

# Configuration Radarr
RADARR_URL=http://localhost:7878
RADARR_API_KEY=votre_cle_api_radarr_ici

# Configuration Tautulli
TAUTULLI_URL=http://localhost:8181
TAUTULLI_API_KEY=votre_cle_api_tautulli_ici
```

## 3. Test de bon fonctionnement

Vous pouvez utiliser le script de test ci-dessous pour vérifier rapidement que vos identifiants sont corrects avant de lancer l'agent complet.

Créez un fichier temporaire `test_api.py` à la racine :

```python
import os
from dotenv import load_dotenv
from media_support.tools.arr_tools import get_stuck_downloads
from media_support.tools.plex_tools import check_plex_playback

load_dotenv()

print("--- Test Sonarr/Radarr ---")
res = get_stuck_downloads()
print(res)

print("\n--- Test Tautulli ---")
res2 = check_plex_playback("votre_nom_utilisateur_plex")
print(res2)
```

Exécutez ce script via le terminal avec la commande `python test_api.py` ou `uv run test_api.py`. Si le champ `status` vaut `"success"` ou `"inactive"`/`"active"` sans code d'erreur HTTP, l'intégration fonctionne !
