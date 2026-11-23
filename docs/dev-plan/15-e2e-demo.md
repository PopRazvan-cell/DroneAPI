# 15: Test end-to-end + demo

| | |
|---|---|
| **Scop** | Dovada că totul funcționează împreună pe date mock, plus un demo prezentabil |
| **Repo** | `make demo` și raportul de calitate în `agridrone-api`; Playwright în `agridrone-web` |
| **Depinde de** | toate |
| **Model AI** | Implementare: **mediu** · Review final al întregului sistem: **mare** |
| **Durată** | 2–3 zile |

## Ce se construiește

1. **`make demo`:**
   - `docker compose up`;
   - migrare;
   - `agridrone mock generate` (toate preseturile);
   - `seed-db`;
   - upload ca zboruri (inclusiv 3 zboruri post-ploaie la 24 h / 48 h / 72 h, cu apă care se retrage: generatorul primește `--water-level-delta`);
   - procesare;
   - la final afișează: „api gata pe :8000; pornește web-ul cu `cd ../agridrone-web && npm run dev`”.
2. **Scenariul demo (script scris, 5 minute):**
   1. harta fermei, cu 3 parcele colorate;
   2. parcela cu bălți: ortomozaic, stratul de apă, KPI, evoluția 24 h → 72 h, comparația swipe;
   3. parcela de porumb: goluri pe rânduri, buruieni, export SHP pentru reînsămânțare;
   4. upload live al unui folder de poze → progres → rezultat;
   5. planificatorul: misiune pentru o parcelă, export KML.
3. **E2E Playwright pe scenariul de mai sus**, în `agridrone-web/e2e/`. Rulează în CI-ul web, cu `PHOTOGRAMMETRY_MODE=mock`:
   - checkout `agridrone-api` la tag-ul din `api-version.txt`;
   - `make demo-ci` (fără deschiderea frontend-ului);
   - build web, apoi Playwright.
4. **Raport de calitate** (`docs/quality-report.md`, generat): benchmark-uri 07/08/09 pe sintetic și pe seturile publice, timpi de procesare și limitări cunoscute.
5. **Review de arhitectură cu un model mare:**
   - se dau ambele repo-uri și `00-contracts.md`;
   - se cer: abateri de la contracte (inclusiv §12, între repo-uri), cod duplicat, probleme de securitate și riscuri pentru faza cu drona reală.

## Criterii de acceptanță

- [ ] `make demo` merge de la zero pe o mașină curată, în < 15 minute (fără ODM real).
- [ ] Testul Playwright trece în CI-ul `agridrone-web`, contra tag-ului api fixat.
- [ ] Raportul de calitate e generat și include limitările.
- [ ] Lista de probleme din review e triată, iar cele critice sunt rezolvate.

## Ce urmează după acest pas

- Primele zboruri reale cu Litchi / Dronelink (KML din pasul 14), ingerate prin upload → validarea pe date reale.
- Ground truth pe teren → evaluarea reală a modelelor și fine-tuning (pasul 09 pe date proprii).
- Faza cu drona: Companion App și control din web (planul general, secțiunea 6).
