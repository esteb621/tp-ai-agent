# Agent IA - Support Média (Plex & Arr Stack)

## 📌 Objectif du Projet

Ce projet utilise une architecture multi-agents (IA) pour diagnostiquer, gérer, et résoudre de manière autonome les problèmes liés à un serveur de streaming multimédia (Plex) et à sa chaîne de téléchargement automatisée (la fameuse "Arr Stack" : Sonarr, Radarr).
L'objectif est d'offrir une assistance technique automatisée : lorsqu'un utilisateur signale un problème (serveur lent, média manquant, fichier bloqué...), les agents enquêtent, trouvent la cause (requête bloquée, problème de transcodage, téléchargement planté), tentent de résoudre l'erreur (relancer un téléchargement, chercher une autre _release_) et informent l'utilisateur par message privé.

---

## 🏗️ Les outils impliqués (en dehors de ADK)

- **Plex** : Il s'agit du serveur multimédia personnel. Il organise les films et séries et permet de les diffuser (streamer) vers n'importe quel appareil (TV, Smartphone, PC).
- **Radarr** : Un gestionnaire de bibliothèques de films. Il surveille les indexeurs (trackers) pour trouver les films demandés de la meilleure qualité, et les envoie automatiquement aux clients de téléchargement (BitTorrent / Usenet).
- **Sonarr** : L'équivalent de Radarr, mais spécialisé pour le téléchargement et la gestion des Séries TV (gestion par saisons/épisodes).
- **Tautulli** : Un outil tiers de monitoring pour Plex. Il permet d'extraire des statistiques détaillées, notamment de savoir en temps réel qui regarde quoi, avec quelle qualité, et surtout s'il y a du _transcodage_ (souvent responsable de lenteurs) ou des problèmes de sous-titres.

---

## 🤖 Les Agents et Leurs Outils

L'architecture repose sur plusieurs agents ayant chacun un rôle très précis :

### 1. **TriageBot**

- **Rôle** : Point d'entrée principal. Il analyse la demande de l'utilisateur et détermine s'il s'agit d'une demande de support (problème de lecture) ou d'une demande de maintenance (média manquant ou téléchargement bloqué). Il transmet ensuite la requête au bon workflow.

### 2. **ArrBot**

- **Rôle** : Gère tout ce qui concerne Radarr et Sonarr.
- **Outils utilisés** :
  - `get_stuck_downloads` : Permet de trouver les téléchargements coincés, en erreur ou manquants.
  - `get_available_releases` : Cherche sur les trackers les _releases_ disponibles pour un média.
  - `download_release` : Lance le téléchargement d'une _release_ spécifique.
  - `search_and_replace_release` : Lance la commande automatique de l'API pour chercher une meilleure source.

### 3. **PlexCheckBot / ServerCheckBot**

- **Rôle** : Dans le workflow de support, son objectif est de vérifier ce qui se passe sur Plex en temps réel. Si l'utilisateur se plaint que "ça lag", il vérifie.
- **Outils utilisés** :
  - `check_plex_playback` : Interroge Tautulli pour récupérer la session de l'utilisateur, vérifier si le flux est en _Direct Play_ ou s'il y a du _Transcodage_ forcé, détecter l'absence de sous-titres et analyser le bitrate/résolution.

### 4. **CommsBot** (L'Agent de Communication)

- **Rôle** : C'est la face visible de l'IA. Il récupère les rapports techniques bruts générés par les autres robots (par exemple: "Erreur 500 sur le serveur", ou "Release rempacée avec succès") et formule une réponse claire, polie et adaptée pour l'utilisateur.
- **Outils utilisés** :
  - `send_discord_dm` : Envoie un message direct via Discord à l'utilisateur ciblé.

---

## 🧠 Modèles d'Intelligence Artificielle Utilisés

Le projet tourne localement et utilise **Ollama** pour interroger les modèles d'IA sans dépendre de clés d'API externes coûteuses :

- `ollama/mistral` : Le modèle principal de l'application. Utilisé par la majorité des agents (TriageBot, ArrBot, CommsBot) pour ses très bonnes capacités de suivi d'instructions et d'utilisation d'outils (Tool Calling / Function Calling).
- `ollama/llama3.2` : Parfois défini comme fallback ou dans certains workflows secondaires pour des tâches de diagnostic simples.

---

## 🚀 Installation & Lancement

### Pré-requis

1. Avoir **Python 3.10+** installé.
2. Avoir **Ollama** installé sur la machine hôte.
3. Télécharger les modèles nécessaires via le terminal :
   ```bash
   ollama pull mistral
   ollama pull llama3.2
   ```
4. Avoir des instances fonctionnelles de Sonarr, Radarr et Tautulli/Plex.

### Installation

1. **Cloner le repository** et se placer dans le dossier.
2. **Créer et activer un environnement virtuel python** :

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Sous Mac/Linux
   # ou .venv\Scripts\activate sous Windows
   ```

3. **Installer les dépendances** :
   _(Assurez-vous d'avoir un fichier `requirements.txt` avec les librairies adéquates ou installez `sonarr-py`, `radarr-py`, `requests`...)_

   ```bash
   pip install -r requirements.txt
   ```

   ou

   ```bash
   uv sync
   ```

4. **Configurer les variables d'environnement** :
   Créez un fichier `.env` à la racine du projet, en vous basant sur cet exemple :

   ```env
   # API ARR STACK
   SONARR_URL=http://localhost:8989
   SONARR_API_KEY=votre_cle_api_sonarr
   RADARR_URL=http://localhost:7878
   RADARR_API_KEY=votre_cle_api_radarr

   # API TAUTULLI / PLEX
   TAUTULLI_URL=http://localhost:8181
   TAUTULLI_API_KEY=votre_cle_api_tautulli
   ```

5. **Lancement** :
   ```bash
   python main.py
   ```
   L'agent sera alors opérationnel et prêt à analyser les requêtes !
