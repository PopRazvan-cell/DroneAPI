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
- Porturile publicate pe host sunt în intervalul **7100–7200**:
  API `7100`, tusd `7101`, PostGIS `7102`, Redis `7103`, NodeODM `7104`.
  Porturile interne din containere rămân cele din contracte.
