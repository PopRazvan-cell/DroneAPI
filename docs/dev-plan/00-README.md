# AgriDrone CV: plan de dezvoltare cu date mock

Planul pornește dezvoltarea **fără dronă**. Folosim:

- **date sintetice** generate de noi; ele vin cu „adevărul” (măștile) inclus;
- **seturi publice** de imagini aeriene, pentru antrenare și validare;
- **poze și video-uri** găsite de noi, pentru ingestie și dashboard.

Fazele, Definition of Done și testele de gate: api în [IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md) (A0–A8), web în [agridrone-web/docs/IMPLEMENTATION_PLAN.md](../../../agridrone-web/docs/IMPLEMENTATION_PLAN.md) (W0–W8).

Codul stă în **două repo-uri**: `agridrone-api` (acesta) și `agridrone-web`. Detalii în [00-contracts.md §2 și §12](00-contracts.md).

Partea de dronă (Companion App, MQTT, control live) **nu intră** în acest plan. Singura excepție e planificatorul de misiuni (pasul 14): e geometrie pură, așa că îl putem face deja.

---

## Cum folosești planul cu un asistent AI

Fiecare fișier `NN-*.md` e un **brief independent**. Poți lucra cu un asistent AI pe o componentă, apoi cu altul pe următoarea.

1. **Dai asistentului AI trei fișiere:**
   - [00-contracts.md](00-contracts.md): regulile comune; fără el, componentele nu se potrivesc între ele;
   - fișierul componentei (ex. `07-cv-water-baseline.md`). Pentru pasul 12, din `agridrone-web/docs/`;
   - codul existent, dacă asistentul nu are acces direct la repo.
2. **Folosești promptul din secțiunea „Prompt de start”** a fișierului.
3. **Ceri întâi un plan**, apoi implementarea. Asistentul AI nu scrie cod până nu aprobi planul.
4. **Rulezi testele** din secțiunea „Criterii de acceptanță”. Pasul e gata doar când trec toate.
5. **Review încrucișat:** alt model (sau aceeași familie, la un nivel mai mare) face review pe diff. Vezi tabelul de mai jos.
6. **Commit pe un branch per pas** (ex. `feat/07-water-baseline`), apoi merge.

> În Claude Code, fișierul [CLAUDE.md](../../CLAUDE.md) din rădăcina fiecărui repo trimite automat la contractele lui.
> Pentru alte unelte (Cursor, Copilot, ChatGPT, Gemini), atașezi manual `00-contracts.md`.

---

## Ce nivel de model AI la ce tip de muncă

Nivelurile sunt generice, ca să meargă cu orice furnizor. În paranteză sunt echivalentele Claude actuale.

| Nivel | Exemple | Pentru ce |
|---|---|---|
| **Mare** | Claude Opus 5.5 (sau Fable 5.2 pentru cazurile cele mai grele) | Arhitectură, contracte, algoritmi CV/geo, orchestrarea pipeline-ului, debugging greu, review final |
| **Mediu** | Claude Sonnet 5.5 | API CRUD, frontend, infrastructură Docker, integrări, majoritatea codului „normal” |
| **Mic** | Claude Haiku 5.5 | Boilerplate, scripturi de download, fixture-uri, extinderea testelor, documentație, refactorizări mecanice |

**Reguli practice:**

- Contractele și interfețele le scrie (sau le revizuiește) un model **mare**. O greșeală acolo se propagă peste tot.
- Codul CV și geospațial are bug-uri „tăcute”, de exemplu CRS greșit sau arii calculate în grade. Aici folosești un model **mare** sau faci review cu unul mare.
- Review-ul îl face mereu un model **egal sau mai mare** decât cel care a scris codul.
- Când un model mediu sau mic se blochează de 2 ori pe aceeași eroare, treci pe un model mai mare. Nu insista.

---

## Pașii și dependențele

| # | Componentă | Depinde de | Nivel model (implementare / review) | Durată orientativă |
|---|---|---|---|---|
| | **Repo `agridrone-api`** | | | |
| 01 | [Repo, tooling, infra locală](01-repo-infra.md) | — | Mediu / Mare | 1–2 zile |
| 02 | [Date mock: generator sintetic + seturi publice](02-mock-data.md) | 01 | **Mare** / Mare | 3–5 zile |
| 03 | [Baza de date + API core (ferme, parcele)](03-db-api-core.md) | 01 | Mediu / Mare | 3–4 zile |
| 04 | [Stocare + ingestie media (upload, EXIF)](04-ingest-storage.md) | 03 | Mediu / Mare | 3–4 zile |
| 05 | [Fotogrametrie (mod mock + NodeODM)](05-photogrammetry.md) | 04 | Mediu / Mare | 2–4 zile |
| 06 | [Procesare geo: COG, decupare, teren](06-geo-processing.md) | 02 | **Mare** / Mare | 3–4 zile |
| 07 | [CV A: detecție apă (baseline clasic)](07-cv-water-baseline.md) | 02, 06 | **Mare** / Mare | 4–6 zile |
| 08 | [CV B: goluri în cultură (baseline clasic)](08-cv-gaps-baseline.md) | 02, 06 | **Mare** / Mare | 4–6 zile |
| 09 | [ML: antrenare modele de segmentare](09-ml-training.md) | 02, 07, 08 | **Mare** / Mare | 2–3 săpt. |
| 10 | [Orchestrare pipeline (Celery)](10-pipeline-orchestration.md) | 04, 05, 06, 07, 08 | **Mare** / Mare | 3–4 zile |
| 11 | [API rezultate: tile-uri, detecții, statistici](11-results-api.md) | 03, 06, 10 | Mediu / Mare | 3–4 zile |
| 13 | [Media: galerie poze și video](13-media-video.md) | 04 | Mediu / Mediu | 3–4 zile |
| 14 | [Planificator de misiuni (fără dronă)](14-mission-planner.md) | 03 | **Mare** / Mare | 3–5 zile |
| 15 | [Test end-to-end + demo](15-e2e-demo.md) (ambele repo-uri) | toate | Mediu / Mare | 2–3 zile |
| 16 | [Deploy: Docker Compose pe server Linux](16-deploy.md) | 01, 03, 12 (imaginea web) | Mediu / **Mare** | 2–3 zile |
| | **Repo `agridrone-web`** | | | |
| 12 | [Frontend + dashboard-uri](../../../agridrone-web/docs/12-frontend-dashboard.md) (inclusiv scheletul repo-ului) | 03 (tag `v0.1.0` cu `openapi.json`), 11 | Mediu / Mare | 2–3 săpt. |

### Ordinea recomandată (cu paralelizare)

```
Săpt. 1      01 ─► 02
Săpt. 2–3    03 ║ 06 ─► 07 ║ 08 ║ 14            (║ = în paralel, alt asistent AI sau altă persoană)
Săpt. 4–5    04 ─► 05 ─► 10 ─► 11   ║  12 (pornește pe mock API din OpenAPI)
Săpt. 6–7    12 ║ 13 ║ 09
Săpt. 8      15 ─► 16       (un staging cu 16 poate apărea mai devreme, după 11, pentru demo)
```

**Primul obiectiv vizibil** (sfârșitul săptămânii 3):

```bash
agridrone mock generate --preset water
agridrone analyze water ...
```

Rezultatul: o hartă cu apa detectată, plus metrici comparate cu adevărul sintetic.

---

## Când un pas e „gata” (Definition of Done)

- [ ] Codul respectă [00-contracts.md](00-contracts.md): structură, nume, CRS, coduri de clase.
- [ ] api: `uv run ruff check` și `uv run pytest` trec. web: `npm run lint && npm test` trec.
- [ ] Dacă s-a schimbat API-ul: `openapi/openapi.json` e comis, are tag nou, iar web-ul e sincronizat.
- [ ] Toate criteriile de acceptanță din fișierul pasului sunt îndeplinite și verificate prin rulare.
- [ ] Review făcut de un model de nivel egal sau mai mare, cu comentariile rezolvate.
- [ ] README-ul componentei (sau o secțiune în `docs/`) explică cum se rulează.
- [ ] Nicio cheie sau parolă în cod (doar în `.env`, care e în `.gitignore`).

---

## Repo-uri viitoare (nu acum)

| Repo | Când se creează | De ce separat |
|---|---|---|
| `agridrone-companion` | la începutul fazei cu drona | Aplicație Android (Kotlin, DJI MSDK v4), cu toolchain și ciclu de release proprii |
| `agridrone-deploy` | numai dacă apar mai multe servere sau clienți | Deocamdată deploy-ul (Docker Compose pe un server Linux) stă în `agridrone-api/deploy/`. Fără Terraform sau Kubernetes |
| `agridrone-ml` | numai dacă antrenarea devine grea (GPU, alt om, DVC) | Până atunci `ml/` rămâne în api, pentru că refolosește `agridrone.cv.eval` și codurile de clase |

Datele (sintetice, publice, zboruri) nu intră în niciun repo: stau pe discul serverului (contracte §8) și în backup.
