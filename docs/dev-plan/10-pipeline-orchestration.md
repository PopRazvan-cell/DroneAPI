# 10: Orchestrarea pipeline-ului (Celery)

| | |
|---|---|
| **Scop** | De la „upload complet” la „rezultate în DB” automat, reluabil și observabil |
| **Depinde de** | 04, 05, 06, 07, 08 |
| **Model AI** | Implementare: **mare** · Review: **mare** |
| **Durată** | 3–4 zile |

## Ce se construiește (`agridrone/workers/`)

1. **`celery_app.py`:**
   - broker și backend Redis;
   - cozi `cpu`, `odm`, `gpu`;
   - serializare JSON;
   - `task_acks_late=True`, `worker_prefetch_multiplier=1`.
2. **Task-uri idempotente.** Fiecare task:
   - primește doar ID-uri;
   - citește intrările din DB și de pe disc și scrie ieșirile la cheile din contracte (scriere atomică, §8);
   - **nu face nimic dacă ieșirea există deja** (opțiunea `force` o recalculează);
   - publică progresul în Redis (`progress:{job_id}`) și starea în DB.
3. **Lanțul:**
   ```
   ingest_flight(flight_id)                         # din pasul 04
     → photogrammetry(flight_id)                    # coada odm (mock: secunde)
     → make_cogs(orthomosaic_id)                    # cpu
     → coregister(orthomosaic_id)                   # cpu, dacă există referință
     → terrain(orthomosaic_id)                      # cpu
     → group(analyze(orthomosaic_id, "water"), analyze(orthomosaic_id, "gaps"))   # după flight.type și season_crop
     → persist_results(analysis_ids)                # detecții în MySQL, parcel_stat
     → notify(flight_id)
   ```
4. **Tabel `job`** (sau folosește `analysis_run` + `flight.status`): `id`, `type`, `status` (`queued`|`running`|`succeeded`|`failed`), `progress`, `error`, `started_at`, `finished_at`, `params`.
5. **API:**
   - `POST /flights/{id}/process` (pornește tot lanțul);
   - `POST /analyses` (`{orthomosaic_id, type, analyzer, params}`): rulează doar analiza;
   - `GET /jobs/{id}`;
   - WebSocket `/ws/jobs`: progres live.
6. **Reîncercări:** backoff exponențial pe erori tranzitorii (rețea, NodeODM indisponibil), fără reîncercare pe erori de date. Erorile se salvează cu traceback-ul scurt.
7. **Comanda `agridrone demo run`:** pentru scenele sintetice, face de la cap la coadă seed DB, upload, procesare și afișarea statisticilor.

## Criterii de acceptanță

- [ ] `agridrone demo run --preset water` produce `analysis_run` cu `status=succeeded`, detecții în MySQL și `parcel_stat` populat.
- [ ] Rerularea aceluiași lanț fără `force` nu recalculează nimic (verificat prin loguri sau timp).
- [ ] Oprirea forțată a worker-ului la jumătate, urmată de repornire, duce lanțul la final.
- [ ] Testele de integrare rulează cu `task_always_eager=True` pentru logică și cu worker real în CI pentru un caz.

## Prompt de start

```
Implementezi pasul 10 din docs/dev-plan/10-pipeline-orchestration.md respectând docs/dev-plan/00-contracts.md.
Task-urile Celery sunt subțiri: doar orchestrare + I/O; logica stă în agridrone/geo, agridrone/cv, agridrone/photogrammetry.
Arată-mi întâi designul stărilor (job/flight/analysis_run) și tranzițiile.
```
