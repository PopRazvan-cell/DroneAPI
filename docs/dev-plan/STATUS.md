# Starea implementării

**Ultima actualizare:** 2026-11-25
**Pas curent:** **02 — Date mock: generator sintetic + seturi publice** (nu început)

Se bifează un pas numai după ce criteriile lui de acceptanță sunt îndeplinite. După fiecare pas:
commit + push, apoi actualizarea acestui fișier.

| Pas | Componentă | Stare |
|---|---|---|
| 01 | [Repo, tooling, infra locală](01-repo-infra.md) | ✅ Completat |
| 02 | [Date mock: generator sintetic + seturi publice](02-mock-data.md) | ⏳ Următorul |
| 03 | [Baza de date + API core](03-db-api-core.md) | ☐ |
| 04 | [Stocare + ingestie media](04-ingest-storage.md) | ☐ |
| 05 | [Fotogrametrie](05-photogrammetry.md) | ☐ |
| 06 | [Procesare geo](06-geo-processing.md) | ☐ |
| 07 | [CV A: detecție apă](07-cv-water-baseline.md) | ☐ |
| 08 | [CV B: goluri în cultură](08-cv-gaps-baseline.md) | ☐ |
| 09 | [ML: antrenare modele](09-ml-training.md) | ☐ |
| 10 | [Orchestrare pipeline](10-pipeline-orchestration.md) | ☐ |
| 11 | [API rezultate](11-results-api.md) | ☐ |
| 12 | Frontend (`agridrone-web`) | ➖ Alt repo |
| 13 | [Media: galerie și video](13-media-video.md) | ☐ |
| 14 | [Planificator de misiuni](14-mission-planner.md) | ☐ |
| 15 | [End-to-end + demo](15-e2e-demo.md) | ☐ |
| 16 | [Deploy](16-deploy.md) | ☐ |

## Note

- **Pasul 01** este complet la nivel de cod și configurație. În sandbox, `make up` nu a putut rula
  pentru că nu există Docker daemon; `docker compose config -q` trece. Rularea completă a stack-ului
  și verificarea `healthy` se fac pe hostul cu Docker.
- **Baza de date:** MySQL 8.4 LTS (InnoDB, `utf8mb4`) rulează în containerul existent de pe host;
  compose-ul nu pornește un MySQL. Conexiunea se configurează prin `MYSQL_HOST`/`MYSQL_PORT`/
  `MYSQL_DATABASE`/`MYSQL_USER`/`MYSQL_PASSWORD`. Geometriile sunt GeoJSON (EPSG:4326, lon/lat)
  în coloane `JSON`, cu coloane `bbox_*` pentru index B-tree; fără PostGIS. Calculele metrice se fac
  în Python, în UTM.
- Pentru `make up`, `.env` trebuie să conțină datele reale ale MySQL-ului existent; stack-ul nu
  creează baza de date și nu pornește un container MySQL.
- Porturile publicate pe host pentru stack-ul nostru sunt în intervalul **7100–7200**:
  API `7100`, tusd `7101`, Redis `7103`, NodeODM `7104`. MySQL folosește portul existent
  (`MYSQL_PORT`, implicit `3306`). Porturile interne din containere rămân cele din contracte.
