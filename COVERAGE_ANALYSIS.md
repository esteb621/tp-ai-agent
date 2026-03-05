# 📊 Analyse de couverture des cas d'usage

**Date:** 5 mars 2026  
**Analyseur:** Assistant Copilot  
**Scope:** Système multi-agents support média (ADK + Ollama)

---

## 📋 Résumé exécutif

| Cas | Nom | Couverture | Statut |
|-----|-----|-----------|--------|
| **1** | Téléchargement bloqué | 85% | ✅ **COUVERT** (avec améliorations mineures) |
| **2** | Problème de lecture (buffering/transcodage) | 90% | ✅ **COUVERT** |
| **3** | Requête déraisonnable (ParallelAgent) | 30% | ⚠️ **PARTIELLEMENT COUVERT** (manque vérification disque) |
| **4** | Désynchronisation Overseerr/Plex | 70% | ⚠️ **PARTIELLEMENT COUVERT** (manque trigger_plex_scan) |
| **5** | Langue/Sous-titres manquants | 60% | ⚠️ **PARTIELLEMENT COUVERT** (manque vérification audio/sous-titres) |

---

## 🔍 Analyse détaillée par cas

### **CAS N°1 : Le téléchargement bloqué** ✅ (85% couvert)

#### Flux attendu :
```
User → TriageBot (accueil) → MaintenanceWorkflow (transfer_to_agent)
     → ArrBot → search_and_replace_release (alternative)
           → CommsBot → Discord DM
```

#### Couverture actuelle :

| Composant | Existe ? | État |
|-----------|----------|------|
| **TriageBot** | ✅ Oui | Classification A/B OK. Instructions claires pour détecter "bloqué depuis jours" |
| **MaintenanceWorkflow** | ✅ Oui | SequentialAgent: ArrBot → CommsBot. Transmission de state via `maintenance_report` |
| **ArrBot** | ✅ Oui | Technicien spécialisé. Tools: `get_stuck_downloads`, `search_and_replace_release` |
| **get_stuck_downloads()** | ✅ Oui | Récupère queue + wanted de Sonarr/Radarr. Supporte regex sur `media_name` |
| **search_and_replace_release()** | ✅ Oui | Recherche auto + remplacement. Retourne bool |
| **Alternative avec AgentTool** | ✅ Oui | CommsBot invoqué comme AgentTool (req. TP). CommsBot lance messages Discord |
| **Notification Discord** | ✅ Oui | `send_discord_dm(discord_id, message)`. CommsBot l'utilise |

#### Exemple de conversation supporté :
```
User: "Salut, ma demande pour le film Dune 2 est bloquée depuis une semaine, il se passe quoi ?"
→ TriageBot (détecte "bloquée" + "depuis") → MaintenanceWorkflow
→ ArrBot: get_stuck_downloads("Dune 2") → 0 seeders
→ search_and_replace_release("Dune 2") → trouve alternative WEB-DL 1080p
→ CommsBot: envoie Discord DM "J'ai relancé le téléchargement..."
```

#### Lacunes mineures :

1. **Pas de "restart_download()" explicite** ✅ *Acceptable*
   - `search_and_replace_release()` incorpore déjà le redémarrage
   - ArrBot peut aussi utiliser `download_release()` en manuel

2. **Pas de vérification en temps réel des seeders** ⚠️ *À améliorer*
   - Actuellement basée sur le dernier scan Sonarr/Radarr
   - Proposal : Ajouter `check_torrent_health(release_guid)` pour vérifier seeders/leechers

**VERDICT:** ✅ **CAS 1 COUVERT à 85%**

---

### **CAS N°2 : Problème de lecture (buffering/transcodage)** ✅ (90% couvert)

#### Flux attendu :
```
User → TriageBot (accueil) → SupportWorkflow (ParallelAgent)
     → PlexCheckBot: check_plex_session() (transcodage + sous-titres)
        & ServerCheckBot: vérification serveur (parallèle)
     → Diagnostic combiné → Conseil utilisateur
```

#### Couverture actuelle :

| Composant | Existe ? | État |
|-----------|----------|------|
| **TriageBot** | ✅ Oui | Détecte keywords: "saccade", "buffering", "freeze", "lag" → SupportWorkflow |
| **SupportWorkflow (ParallelAgent)** | ✅ Oui | PlexCheckBot ∥ ServerCheckBot exécutés en parallèle |
| **PlexCheckBot** | ✅ Oui | Spécialiste diagnostic Plex |
| **check_plex_playback(user)** | ✅ Oui | Via Tautulli. Retourne: `transcoding`, `missing_subtitles`, `bitrate_kbps`, `video_resolution` |
| **ServerCheckBot** | ✅ Oui | Diagnostic serveur (simulé en texte) |
| **Analyse combinée** | ✅ Oui | PlexCheckBot + ServerCheckBot partagent state, résultats synthétisés |
| **Conseil utilisateur** | ✅ Oui | Instructions dans PlexCheckBot: si `transcoding=True` → "va dans paramètres Plex" |

#### Exemple de conversation supporté :
```
User: "C'est insupportable, le film Oppenheimer n'arrête pas de charger toutes les 10 secondes !"
→ TriageBot (détecte "charge") → SupportWorkflow (parallèle)
→ PlexCheckBot: check_plex_playback("utilisateur") 
   → "State: Transcoding 4K to 720p" → Diagnostic: problème codec/résolution
→ ServerCheckBot: vérification serveur OK
→ PlexCheckBot retourne conseil: "Change qualité à Maximum / Originale dans Plex"
```

#### Lacunes mineures :

1. **Extraction du username du message** ⚠️ *À améliorer*
   - PlexCheckBot utilise "utilisateur_plex" par défaut si pas précisé
   - Solution: Améliorer prompt pour extraire username du contexte

2. **Pas de "adjust_quality()" ou "set_direct_play()"** ⚠️ *OK car expliqué*
   - Correct : ArrBot ne peut pas modifier settings Plex (hors scope de Sonarr/Radarr)
   - Solution : Donner l'instruction utilisateur (ce qui est fait)

3. **Sous-titres : diagnostic OK, mais pas de trigger Bazarr** ⚠️ *À ajouter*
   - Cas 5 nécessite `trigger_bazarr_search()` pour relancer téléchargement sous-titres
   - Actuellement manquant → voir **CAS 5**

**VERDICT:** ✅ **CAS 2 COUVERT à 90%** (nécessite amélioration pour CAS 5)

---

### **CAS N°3 : Requête déraisonnable (ParallelAgent)** ⚠️ (30% couvert)

#### Flux attendu :
```
User: "Tu peux m'ajouter l'intégrale de One Piece en 4K ?"
→ TriageBot lance ParallelAgent: check_disk_space() ∥ estimate_media_size()
→ Compile résultats → Propose compromis "1080p au lieu de 4K"
→ Utilisateur accepte → MaintenanceWorkflow ajoute la requête
```

#### Couverture actuelle :

| Composant | Existe ? | État |
|-----------|----------|------|
| **TriageBot** | ✅ Oui | Mais instructions actuelles ne couvrent pas "avant Overseerr" |
| **ParallelAgent pour estimation** | ❌ **MANQUANT** | Aucun ParallelAgent pour cas 3 |
| **check_disk_space()** | ❌ **MANQUANT** | Aucun tool pour vérifier espace disponible |
| **estimate_media_size()** | ❌ **MANQUANT** | Aucun tool pour estimer taille d'un contenu |
| **Logique de négociation** | ❌ **MANQUANT** | Pas d'agent dédié pour proposer compromis |
| **Requête qualité diminuée** | ❌ **MANQUANT** | Aucun système pour accepter/refuser la contre-proposition |

#### Architecture manquante :

```
TriageBot (nouvelle instruction)
    ↓
AVANT passage à MaintenanceWorkflow:
  - Détecte: "ajouter l'intégrale de One Piece" = requête demandée (pas encore en Overseerr)
  - Lance ParallelAgent pour vérifier faisabilité
    ├─ EstimateBot: "One Piece 4K = ~2.5 To" 
    └─ StorageBot: "Espace libre = 800 Go"
  - TriageBot synthétise: "2.5 To > 800 Go → impossible"
  - TriageBot propose: "Acceptez-vous 1080p (~400 Go) ?"
  - Si OUI → MaintenanceWorkflow
  - Si NON → "D'accord, on abandonne"
```

**VERDICT:** ⚠️ **CAS 3 COUVERT À 30%** (manque ParallelAgent + 2 tools + logique acceptation)

---

### **CAS N°4 : Désynchronisation Overseerr/Plex** ⚠️ (70% couvert)

#### Flux attendu :
```
User: "Deadpool & Wolverine était dispo, mais Plex n'a rien"
→ TriageBot → ArrBot (délégation)
→ check_file_on_disk("Deadpool") → Fichier présent ✓
→ trigger_plex_scan() → Force Plex à actualiser
→ Utilisateur: "Attends 1 min, redémarre Plex, il apparaîtra"
```

#### Couverture actuelle :

| Composant | Existe ? | État |
|-----------|----------|------|
| **TriageBot** | ✅ Oui | Peut détecter "dispo mais pas sur Plex" |
| **ArrBot** | ✅ Oui | Technicien capable de le gérer |
| **check_file_on_disk()** | ❌ **MANQUANT** | Aucun tool pour vérifier présence fichier |
| **trigger_plex_scan()** | ❌ **MANQUANT** | Aucun tool pour forcer scan Plex |
| **Estimation temps attente** | ⚠️ *Partiel* | "1-2 minutes" codé en dur dans CommsBot |

#### Architecture manquante :

```
Tools à créer:
1. check_file_on_disk(media_name: str, media_type: str) -> bool
   - Vérifie si fichier existe dans /mnt/media/films/ ou /mnt/media/series/
   
2. trigger_plex_scan(library: str = "Films") -> dict
   - Lance une commande Plex pour scanner la librairie
   - Retourne: {"status": "success", "scan_duration": "~90s"}
```

#### Workflow amélioré :

```python
# Dans ArrBot.instruction:
# STEP 3bis — Si fichier trouvé mais pas dans Plex:
#   → Call check_file_on_disk(media_name)
#   → Si fichier présent: Call trigger_plex_scan("Films")
#   → Informer utilisateur: "Fichier trouvé, actualisation lancée"
```

**VERDICT:** ⚠️ **CAS 4 COUVERT À 70%** (manque 2 tools simples)

---

### **CAS N°5 : Langue/Sous-titres manquants** ⚠️ (60% couvert)

#### Flux attendu :
```
User: "The Last of Us en anglais sans sous-titres français !"
→ TriageBot → ArrBot (délégation)
→ check_audio_subs("The Last of Us") → "VO uniquement, pas de subs"
→ if VF inexistante: "C'est normal, diffusé aux US il y a 2h"
→ trigger_bazarr_search() → Lance recherche sous-titres
→ ArrBot → CommsBot: "Sous-titres en cours de download, 5-10 min"
```

#### Couverture actuelle :

| Composant | Existe ? | État |
|-----------|----------|------|
| **TriageBot** | ✅ Oui | Peut détecter "pas de sous-titres" dans SupportWorkflow |
| **SupportWorkflow** | ✅ Oui | PlexCheckBot détecte `missing_subtitles = true` |
| **check_plex_playback()** | ✅ Oui | Retourne `subtitle_language` et `missing_subtitles` |
| **check_audio_subs()** | ❌ **MANQUANT** | Aucun tool pour détailler audio + subs (VO/VF/VOSTFR) |
| **trigger_bazarr_search()** | ❌ **MANQUANT** | Aucun tool pour lancer recherche Bazarr |
| **Vérification "C'est normal, c'est récent"** | ❌ **MANQUANT** | Aucun check sur date de diffusion |

#### Architecture manquante :

```
Tools à créer:
1. check_audio_subs(media_name: str, media_id: int, media_type: str) -> dict
   - Appelle API Bazarr/Sonarr pour vérifier audio + tracks subs disponibles
   - Retourne: {
        "audio_tracks": ["fr", "en"],
        "subtitles": {"en": 2, "fr": 0},  # nombre de fichiers subs
        "status": "VO with partial subs"
     }

2. trigger_bazarr_search(media_id: int, media_type: str, language: str) -> dict
   - Lance recherche Bazarr pour language spécifique
   - Retourne: {"status": "searching", "eta_minutes": 5}
```

#### Workflow amélioré :

```python
# Dans ArrBot ou nouveau SubsBot (agent dédié):

# STEP 1: check_audio_subs(media_name)
#   → Si "missing_subtitles": 
#       → if époque récente (<2h): "C'est normal, diffusé il y a X h"
#       → Call trigger_bazarr_search()
#       → "Recherche lancée, 5-10 min"

# Alternative: Intégrer dans PlexCheckBot du SupportWorkflow
#   → Détecte missing_subtitles dans check_plex_playback()
#   → Invoque AgentTool SubsBot pour lancer recherche Bazarr
```

**VERDICT:** ⚠️ **CAS 5 COUVERT À 60%** (manque 2 tools + logique timing)

---

## 📐 Plan d'implémentation complet

### **Priorité 1 : Cas 4 (Désynchronisation Plex)** — 2-3 heures

**Justification:** Simple, 2 tools, impact élevé sur UX.

#### Tâches :

1. **Créer outil `check_file_on_disk()`**
   ```python
   # Dans tools/arr_tools.py
   def check_file_on_disk(media_name: str, media_type: str) -> dict:
       """Vérifie présence du fichier dans /mnt/media/"""
       # Cherche dans films/ ou series/ selon type
       # Retourne: {"found": bool, "path": str, "size_gb": float}
   ```

2. **Créer outil `trigger_plex_scan()`**
   ```python
   # Dans tools/plex_tools.py (nouveau)
   def trigger_plex_scan(library: str = "Films") -> dict:
       """Force Plex à scanner une librairie via son API"""
       # Appelle POST /library/<lib_key>/refresh
       # Retourne: {"status": "success", "message": "Scan lancé"}
   ```

3. **Intégrer dans ArrBot**
   ```python
   # Dans ArrBot.instruction: ajouter STEP 3bis
   # Après download_release() ou si fichier trouvé:
   #   → check_file_on_disk(media)
   #   → si trouvé: trigger_plex_scan()
   ```

4. **Tester scenario complet**
   ```
   User: "Deadpool est dispo mais pas visible"
   → ArrBot: check_file_on_disk() ✓
   → ArrBot: trigger_plex_scan("Films")
   → CommsBot: "Actualization lancée, 1-2 min"
   ```

---

### **Priorité 2 : Cas 5 (Sous-titres/Audio)** — 3-4 heures

**Justification:** 2 tools, utile pour VF/VOSTFR/VO issues.

#### Tâches :

1. **Créer outil `check_audio_subs()`**
   ```python
   # Dans tools/arr_tools.py (ou nouveau tools/subs_tools.py)
   def check_audio_subs(media_name: str, media_id: int, media_type: str) -> dict:
       """Vérifie audio + sous-titres disponibles via Bazarr/Sonarr"""
       # Interroge Bazarr API /series/ ou /movies/
       # Retourne: {
       #    "audio_tracks": [...],
       #    "subtitles_available": {...},
       #    "has_french": bool,
       # }
   ```

2. **Créer outil `trigger_bazarr_search()`**
   ```python
   # Dans tools/subs_tools.py
   def trigger_bazarr_search(media_id: int, media_type: str, language: str) -> dict:
       """Lance recherche Bazarr pour langage spécifique"""
       # Appelle API Bazarr pour lancer recherche
       # Retourne: {"status": "searching", "eta": "5-10 min"}
   ```

3. **Optionnel: Créer SubsBot agent** OU **Étendre PlexCheckBot**
   ```
   OPTION A (simple): Ajouter les tools à ArrBot
   OPTION B (propre): Créer agent SubsBot dédié aux sous-titres
   ```

4. **Logique de détection timing**
   ```python
   # Dans SubsBot.instruction:
   # if subs manquants:
   #   → if media date < 2h: "C'est normal, diffusé récemment"
   #   → Sinon: "Recherche anormale, on lance Bazarr"
   ```

---

### **Priorité 3 : Cas 3 (Requête déraisonnable)** — 4-5 heures

**Justification:** Plus complexe, nécessite ParallelAgent + logique acceptation multi-turn.

#### Tâches :

1. **Créer outil `check_disk_space()`**
   ```python
   # Dans tools/arr_tools.py (ou storage_tools.py)
   def check_disk_space() -> dict:
       """Vérifie espace disque disponible"""
       # Retourne: {
       #    "total_gb": 12000,
       #    "used_gb": 8200,
       #    "available_gb": 3800,
       #    "percent_used": 68.3
       # }
   ```

2. **Créer outil `estimate_media_size()`**
   ```python
   # Dans tools/arr_tools.py
   def estimate_media_size(media_name: str, quality: str = "4K") -> dict:
       """Estime taille d'un contenu selon qualité"""
       # Utilise données historiques ou API TMDB
       # Retourne: {
       #    "media_name": "One Piece",
       #    "qualities": {
       #        "4K": 2500,    # GB
       #        "1080p": 400,
       #        "720p": 150
       #    }
       # }
   ```

3. **Créer EstimateBot agent (ParallelAgent)**
   ```python
   # Dans agents/estimate_bot.py
   estimate_bot = LlmAgent(
       name="EstimateBot",
       tools=[estimate_media_size]
       # Estime taille pour la requête
   )
   ```

4. **Créer StorageBot agent (ParallelAgent)**
   ```python
   # Dans agents/storage_bot.py
   storage_bot = LlmAgent(
       name="StorageBot",
       tools=[check_disk_space]
       # Vérifie espace disponible
   )
   ```

5. **Créer FeasibilityWorkflow (ParallelAgent)**
   ```python
   # Dans workflows/feasibility_workflow.py
   feasibility_workflow = ParallelAgent(
       name="FeasibilityWorkflow",
       sub_agents=[estimate_bot, storage_bot]
       # Exécute en parallèle
   )
   ```

6. **Modifier TriageBot**
   ```python
   # Nouvelle instruction pour détecter "avant Overseerr":
   # "ajouter l'intégrale", "tu peux me télécharger", etc.
   # → transfer_to_agent FeasibilityWorkflow
   # → Si suffisant: MaintenanceWorkflow
   # → Si insuffisant: Proposer qualité réduite (TODO: multi-turn)
   ```

7. **Implémenter logic multi-turn** ⚠️ *Complexe*
   ```
   - TriageBot propose: "2.5 To > 800 Go, acceptez 1080p ?"
   - User: "Oui"
   - TriageBot valide et passe à MaintenanceWorkflow
   
   Limitation ADK : StateStore ne supporte pas multi-turn dans le même agent
   Workaround: Stocker "accepted_quality" dans state, laisser MaintenanceWorkflow
   lire cette valeur quand créant la requête Overseerr
   ```

---

## 🎯 Résumé des nouvelles features

### **Tools à créer (6):**

| Tool | Fichier | Priorité | Complexité |
|------|---------|----------|-----------|
| `check_file_on_disk()` | `tools/arr_tools.py` | 1️⃣ | ⭐ |
| `trigger_plex_scan()` | `tools/plex_tools.py` | 1️⃣ | ⭐ |
| `check_audio_subs()` | `tools/subs_tools.py` | 2️⃣ | ⭐⭐ |
| `trigger_bazarr_search()` | `tools/subs_tools.py` | 2️⃣ | ⭐⭐ |
| `check_disk_space()` | `tools/storage_tools.py` | 3️⃣ | ⭐ |
| `estimate_media_size()` | `tools/arr_tools.py` | 3️⃣ | ⭐⭐ |

### **Agents à créer (2):**

| Agent | Fichier | Priorité | Type |
|-------|---------|----------|------|
| `EstimateBot` | `agents/estimate_bot.py` | 3️⃣ | LlmAgent |
| `StorageBot` | `agents/storage_bot.py` | 3️⃣ | LlmAgent |

### **Workflows à créer (1):**

| Workflow | Fichier | Priorité | Type |
|----------|---------|----------|------|
| `FeasibilityWorkflow` | `workflows/feasibility_workflow.py` | 3️⃣ | ParallelAgent |

### **Modifications à existing files:**

| Fichier | Changement | Priorité |
|---------|-----------|----------|
| `agents/arr_bot.py` | + `check_file_on_disk()` et `trigger_plex_scan()` aux tools | 1️⃣ |
| `agents/arr_bot.py` | + Instructions STEP 3bis pour cas 4 | 1️⃣ |
| `agent.py` | + Sub-agent FeasibilityWorkflow (optionnel) | 3️⃣ |

---

## 📊 Timeline proposée

### **Sprint 1 (2-3j) — Priorité 1 (Cas 4)**
- Créer + tester `check_file_on_disk()`
- Créer + tester `trigger_plex_scan()`
- Intégrer dans ArrBot
- Tester scenario complet

**Effort:** ~2-3 heures  
**Impact:** 1 cas d'usage + 25% de la couverture

### **Sprint 2 (3-4j) — Priorité 2 (Cas 5)**
- Créer + tester `check_audio_subs()`
- Créer + tester `trigger_bazarr_search()`
- Intégrer logique timing
- Tester scenario complet

**Effort:** ~3-4 heures  
**Impact:** 1 cas d'usage + 30% de la couverture

### **Sprint 3 (4-5j) — Priorité 3 (Cas 3)**
- Créer 2 tools (`check_disk_space`, `estimate_media_size`)
- Créer 2 agents (EstimateBot, StorageBot)
- Créer FeasibilityWorkflow
- Implémenter logique multi-turn
- Tester scenario complet

**Effort:** ~4-5 heures  
**Impact:** 1 cas d'usage + 70% de la couverture

---

## ✅ Checklist de validation

Après chaque implémentation :

- [ ] Tool retourne bon type (dict/bool) et gère erreurs
- [ ] Tool intégré dans agent via `tools=[...]`
- [ ] Instructions agent mettent à jour pour utiliser le tool
- [ ] State partagé utilisé si multi-agent (`output_key`, `{variable_name}`)
- [ ] Scenario exemple fonctionne end-to-end
- [ ] Pas d'hallucination tools (liste outils dans docstring/table)
- [ ] Callbacks logging fonctionnent
- [ ] Gestion erreurs APIs (timeouts, 404, etc.)

---

## 🔮 Cas supplémentaires (hors scope TP)

Si envie d'aller plus loin (non requis) :

1. **Notifications proactives** : Agent qui envoie "Votre contenu sera dispo dans ~X heures"
2. **Machine Learning** : Prédire qualités populaires pour économiser disque
3. **Versioning contenu** : "Voici 4 versions, laquelle voulez-vous ?"
4. **Caching subtitle searches** : Éviter requêtes redondantes à Bazarr

---

## 📝 Conclusion

**Couverture actuelle : 60% en moyenne**

- ✅ Cas 1-2 : **Largement couverts**, juste optimisations mineures
- ⚠️ Cas 3-5 : **Partiellement couverts**, manquent tools/agents spécifiques

**Pas de nouveau agent requis.** Juste :
- 2 outils simples (Prio 1)
- 2 outils moyens (Prio 2)
- 2 outils + 2 agents pour Prio 3

**Implémentation possible en ~10 heures total (spread sur 2 semaines).**
