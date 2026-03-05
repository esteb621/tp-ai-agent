# 🎯 Plan d'action — Synthèse exécutive

## 📊 État des cas d'usage

```
CAS 1 : Téléchargement bloqué
├─ Couverture: ✅ 85% — COUVERT
├─ Manque: Vérification seeders en temps réel (optionnel)
└─ Action: AUCUNE — Fonctionne comme prévu

CAS 2 : Problème de lecture (buffering/transcodage)
├─ Couverture: ✅ 90% — COUVERT
├─ Manque: Extraction username du message (amélioration UX)
└─ Action: AUCUNE — Fonctionnel, peut être optimisé plus tard

CAS 3 : Requête déraisonnable (avant Overseerr)
├─ Couverture: ⚠️ 30% — PARTIELLEMENT COUVERT
├─ Manque: 2 tools + 2 agents + logique multi-turn
│          (check_disk_space, estimate_media_size, EstimateBot, StorageBot)
└─ Action: 🔴 CRITIQUE — Ajouter ParallelAgent + tools

CAS 4 : Désynchronisation Overseerr/Plex
├─ Couverture: ⚠️ 70% — PARTIELLEMENT COUVERT
├─ Manque: check_file_on_disk(), trigger_plex_scan()
└─ Action: 🟡 PRIORITAIRE — 2 tools simples à ajouter

CAS 5 : Langue/Sous-titres manquants
├─ Couverture: ⚠️ 60% — PARTIELLEMENT COUVERT
├─ Manque: check_audio_subs(), trigger_bazarr_search()
└─ Action: 🟡 PRIORITAIRE — 2 tools + logique timing
```

---

## 🛠️ Features à implémenter (par ordre de priorité)

### **Priorité 1 : CAS 4 (Plex Sync)** — ⏱️ 2-3h

```
✅ Cas couvert: Désynchronisation Overseerr/Plex

Tools à créer:
├─ check_file_on_disk(media_name, media_type) → dict
│  └─ Cherche fichier dans /mnt/media/{films,series}/
└─ trigger_plex_scan(library = "Films") → dict
   └─ Force refresh Plex via API

Où intégrer:
└─ ArrBot: Ajouter 2 tools aux tools=[...], 
           + STEP 3bis dans instruction

Exemple:
  User: "Deadpool est dispo mais pas visible sur Plex"
  ArrBot: check_file_on_disk("Deadpool") → ✓ Fichier trouvé
  ArrBot: trigger_plex_scan("Films") → Actualisation lancée
  CommsBot: "Fichier trouvé, Plex en cours d'actualisation (1-2 min)"
```

---

### **Priorité 2 : CAS 5 (Audio/Subs)** — ⏱️ 3-4h

```
✅ Cas couvert: Langue/Sous-titres manquants

Tools à créer (dans tools/subs_tools.py):
├─ check_audio_subs(media_name, media_id, media_type) → dict
│  └─ Appelle Bazarr pour détailler audio + subs dispo
└─ trigger_bazarr_search(media_id, media_type, language) → dict
   └─ Lance recherche Bazarr pour langage spécifique

Où intégrer:
└─ ArrBot (ou nouveau SubsBot): Ajouter tools + logique
   - Si subs manquants ET media récent (<2h): "C'est normal"
   - Sinon: trigger_bazarr_search() → "5-10 min de recherche"

Exemple:
  User: "The Last of Us en anglais, pas de subs français !"
  SubsBot: check_audio_subs("The Last of Us") → VO uniquement
  SubsBot: "Ep diffusé il y a 2h, pas de VF encore"
  SubsBot: trigger_bazarr_search() → "Recherche subs lancée"
  CommsBot: "Sous-titres en recherche (5-10 min), relance après"
```

---

### **Priorité 3 : CAS 3 (Requête déraisonnable)** — ⏱️ 4-5h

```
⚠️ Cas partiellement couvert: Requête déraisonnable avant Overseerr

Architecture complète à créer:

1️⃣ Tools (dans tools/storage_tools.py):
   ├─ check_disk_space() → dict
   │  └─ Retourne {total_gb, used_gb, available_gb, percent_used}
   └─ estimate_media_size(media_name, quality) → dict
      └─ Retourne {media_name, qualities: {4K: 2500, 1080p: 400, 720p: 150}}

2️⃣ Agents à créer:
   ├─ EstimateBot (dans agents/estimate_bot.py)
   │  └─ tool: estimate_media_size()
   └─ StorageBot (dans agents/storage_bot.py)
      └─ tool: check_disk_space()

3️⃣ Workflow:
   └─ FeasibilityWorkflow (dans workflows/feasibility_workflow.py)
      └─ ParallelAgent: EstimateBot ∥ StorageBot

4️⃣ Logique dans TriageBot:
   └─ Nouvelle classification: "CATEGORY D — Requête avant Overseerr"
      → Détecte: "ajouter", "télécharger l'intégrale", etc.
      → transfer_to_agent FeasibilityWorkflow
      → Compile résultats
      → Propose: "Acceptez-vous 1080p au lieu de 4K ?"
      → Si OUI: MaintenanceWorkflow

Exemple:
  User: "Tu peux m'ajouter l'intégrale de One Piece en 4K stp ?"
  TriageBot: Lance FeasibilityWorkflow (parallèle)
  EstimateBot: One Piece 4K = 2.5 To
  StorageBot: Espace libre = 800 Go
  TriageBot: "2.5 To > 800 Go... Acceptez 1080p (400 Go) ?"
  User: "Oui d'accord !"
  TriageBot → MaintenanceWorkflow (avec quality="1080p")
```

---

## 📋 Checklist d'implémentation

### **Phase 1 — Cas 4 (Plex Sync)**

- [ ] Créer `check_file_on_disk()` dans `tools/arr_tools.py`
  - [ ] Cherche dans `/mnt/media/films/` et `/mnt/media/series/`
  - [ ] Retourne `{found: bool, path: str, size_gb: float}`
  - [ ] Gère erreurs: permission denied, path not found

- [ ] Créer `trigger_plex_scan()` dans `tools/plex_tools.py`
  - [ ] Appelle API Plex `/library/<lib_key>/refresh`
  - [ ] Retourne `{status: "success", message: str}`
  - [ ] Gère erreurs: timeout, 404, API down

- [ ] Ajouter outils à `ArrBot.tools=[...]`
  - [ ] `check_file_on_disk`
  - [ ] `trigger_plex_scan`

- [ ] Mettre à jour `ArrBot.instruction`
  - [ ] Ajouter STEP 3bis: "Si fichier trouvé mais pas dans Plex"
  - [ ] Instructions claires: quand appeler les tools

- [ ] Tester scenario:
  - [ ] User report "fichier dispo mais pas visible"
  - [ ] ArrBot appelle `check_file_on_disk()` → ✓ Trouvé
  - [ ] ArrBot appelle `trigger_plex_scan()`
  - [ ] CommsBot notifie user

---

### **Phase 2 — Cas 5 (Audio/Subs)**

- [ ] Créer `tools/subs_tools.py` (nouveau fichier)
  - [ ] `check_audio_subs(media_name, media_id, media_type)`
    - [ ] Interroge Bazarr API
    - [ ] Retourne `{audio_tracks, subtitles_available, has_french}`
  - [ ] `trigger_bazarr_search(media_id, media_type, language)`
    - [ ] Lance recherche Bazarr
    - [ ] Retourne `{status, eta_minutes}`

- [ ] Intégrer dans ArrBot OU créer SubsBot
  - [ ] Ajouter tools
  - [ ] Logique: si subs manquants
    - [ ] Si media récent (<2h): "C'est normal"
    - [ ] Sinon: `trigger_bazarr_search()`

- [ ] Tester scenario:
  - [ ] User report "pas de subs français"
  - [ ] Tool détecte media récent → message explicatif
  - [ ] Tool lance recherche Bazarr
  - [ ] CommsBot notifie timing (5-10 min)

---

### **Phase 3 — Cas 3 (Requête déraisonnable)**

- [ ] Créer `tools/storage_tools.py` (nouveau fichier)
  - [ ] `check_disk_space()` → `{total, used, available, percent}`
  - [ ] `estimate_media_size(media_name, quality)` → `{media, qualities}`

- [ ] Créer `agents/estimate_bot.py`
  - [ ] Utilise `estimate_media_size()`
  - [ ] LlmAgent simple

- [ ] Créer `agents/storage_bot.py`
  - [ ] Utilise `check_disk_space()`
  - [ ] LlmAgent simple

- [ ] Créer `workflows/feasibility_workflow.py`
  - [ ] ParallelAgent: EstimateBot ∥ StorageBot
  - [ ] Compilation résultats

- [ ] Modifier `agent.py` (TriageBot)
  - [ ] Nouvelle instruction CATEGORY D
  - [ ] Detection "ajouter intégrale", "télécharger"
  - [ ] transfer_to_agent FeasibilityWorkflow
  - [ ] Logic: compile résultats → propose compromise

- [ ] Tester scenario:
  - [ ] User request "One Piece 4K"
  - [ ] FeasibilityWorkflow lance parallèle
  - [ ] EstimateBot: 2.5 To
  - [ ] StorageBot: 800 Go dispo
  - [ ] TriageBot: "Proposez 1080p ?"
  - [ ] User: "OK"
  - [ ] MaintenanceWorkflow ajoute avec quality="1080p"

---

## ⏱️ Timeline estimée

| Phase | Tâches | Durée | Dépendances |
|-------|--------|-------|-------------|
| **Phase 1** | CAS 4 (Plex Sync) | 2-3h | Aucune |
| **Phase 2** | CAS 5 (Audio/Subs) | 3-4h | Aucune (indépendant) |
| **Phase 3** | CAS 3 (Requête) | 4-5h | Aucune (indépendant) |
| **Total** | Toutes phases | ~10h | Possible en parallèle |

**Recommandation:** Implémenter Phase 1 + 2 d'abord (simples, impact rapide),  
puis Phase 3 (plus complexe, logique multi-turn).

---

## 📌 Notes importantes

✅ **AUCUN nouvel agent requis** sauf SubsBot optionnel (Cas 5)  
✅ **Pas de modification architecture ADK** — tools standards suffisent  
✅ **ParallelAgent et StateStore** — déjà utilisés avec succès (SupportWorkflow)  
✅ **Ollama/Mistral** — suffisant pour logique d'orchestration  

⚠️ **Défis à prévoir:**
- Extraction username du context message (PlexCheckBot) — à raffiner
- Multi-turn "acceptez-vous ce compromis ?" — StateStore limité
- APIs externes (Plex, Bazarr) — ajouter timeouts/retry logic
- Mockups tools pour démo sans APIs réelles — déjà partiellement fait

---

## 📚 Références

- **Fichier d'analyse complet:** `COVERAGE_ANALYSIS.md`
- **Code existant:**
  - `media_support/agents/arr_bot.py` — Architecture ArrBot
  - `media_support/workflows/support_workflow.py` — ParallelAgent pattern
  - `media_support/tools/arr_tools.py` — Template pour nouveaux tools
  - `media_support/tools/plex_tools.py` — Template outils Plex

---

**Prêt à démarrer ? Commencez par Phase 1 (CAS 4) — c'est simple et impactful ! 🚀**
