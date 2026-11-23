# AgriDrone CV — API Implementation Plan (backend developer)

Phased plan for the **`agridrone-api`** repo, from an empty repo to a deployed backend, using **mock data only** (no drone).
The frontend has its own plan: [agridrone-web/docs/IMPLEMENTATION_PLAN.md](../../agridrone-web/docs/IMPLEMENTATION_PLAN.md).

Each phase ends with a **gate**: a Definition of Done (DoD) plus tests that must pass. A phase is complete only when `make gate-aN` is green in CI and the manual checks are ticked in the phase's last PR.

- Step briefs (what to build, starter prompts, pitfalls): [dev-plan/00-README.md](dev-plan/00-README.md)
- Contracts: [dev-plan/00-contracts.md](dev-plan/00-contracts.md) (§12 is the contract with the web repo)

---

## Overview

| Phase | Name | Steps | Weeks | Exit demo | Hands off to web |
|---|---|---|---|---|---|
| **A0** | Foundations | 01 | 1 | `make up`, empty CLI, `/healthz`, `/meta/classes` | **H0** |
| **A1** | Synthetic data & geo core | 02, 06 | 1–2 | Synthetic water scene opens in QGIS | — |
| **A2** | Analysis baselines | 07, 08 | 2–4 | `agridrone analyze water` / `gaps` + benchmark vs. ground truth | **H2** |
| **A3** | Platform core | 03, 14 | 2–4 (parallel to A2) | Farms/parcels CRUD in Swagger; mission exported to KML | **H1** |
| **A4** | Ingest & pipeline | 04, 05, 10 | 4–5 | Photo folder → mock ortho → analysis → stats, one command | **H3** (stubs at start) |
| **A5** | Results & media API | 11, 13 | 5–7 | Tiles, stats, timeline, compare, exports, HLS over HTTP | **H4** (stubs at start) |
| **A6** | ML models (parallel, optional) | 09 | 6–8 | ML analyzer beats the classic baseline | — |
| **A7** | End-to-end & demo | 15 (api part) | 8 | `make demo` from a clean machine | **H5** |
| **A8** | Deploy + real auth | 16 + auth | 8–9 | Staging over HTTPS; deploy, rollback, restore rehearsed | **H6** |

```
A0 ─► A1 ─► A2 ──────────► A4 ─► A5 ─► A7 ─► A8
 └────────► A3 (parallel) ─┘           A6 (parallel from A2, optional for A7)
```

**Rules**

- A phase starts only when the phases it depends on have passed their gates.
- `make gate-aN` is added in the phase's first PR and stays in CI permanently, so later work cannot silently break an earlier gate.
- Thresholds (IoU, timings, tolerances) come from the step briefs. Changing one needs a PR explaining why, reviewed by a large model.
- **Contract first:** when a phase adds endpoints the web needs, its **first PR** publishes them as OpenAPI stubs (real schemas, handlers return `501`) and cuts a tag. Implementation follows. This lets the web developer work in parallel instead of waiting.

---

## Handoffs to the web developer

The contract between the two developers is `openapi/openapi.json` at a tag (contracts §12). Each handoff is a tag plus a short note in the release description listing new or changed endpoints.

| ID | When | Tag | What web gets | Web phase it unblocks |
|---|---|---|---|---|
| **H0** | end of A0 | `v0.0.1` | `healthz`, `meta/classes`, problem+json shape, dev auth; local `docker compose` incl. `tusd` | W0, W1 |
| **H1** | end of A3 | `v0.1.0` | Farms, parcels (incl. import), crops, flights, missions (`plan`, CRUD, export) | W2, W3 |
| **H2** | end of A2 | — | `agridrone mock export-frontend-fixtures`: JSON fixtures + small tile PNGs for the 3 demo parcels and 3 post-rain flights | W2 |
| **H3** | **start** of A4 | `v0.2.0` (stubs), then `v0.2.x` (real) | `upload-session`, tus flow, media list, capture summary, analyses, jobs + `/ws/jobs` | W4 |
| **H4** | **start** of A5 | `v0.3.0` (stubs), then `v0.3.x` (real) | tilejson + tiles, detections, stats, timeline, farm summary, compare, risk map, exports, reports, weather, media/HLS | W5, W6 |
| **H5** | end of A7 | `v0.4.0` | `make demo-ci` usable from web CI for Playwright | W7 |
| **H6** | A8 | `v1.0.0` | Login / logout / session endpoints; prod config (same-origin `/api`) | W8 |

**Requests from web:** the web developer files issues labelled `api-request` for missing fields or endpoints. They are triaged at the weekly sync (see the bottom of this file) and added to the current or next phase.

---

## Global Definition of Done (every phase)

- [ ] Code follows the contracts: structure, naming, CRS rules, class codes, storage keys.
- [ ] `uv run ruff check`, `uv run ruff format --check`, `uv run mypy` (strict packages) and `uv run pytest` pass.
- [ ] If the API changed: `openapi/openapi.json` regenerated and committed (`agridrone openapi --check` passes), tag cut, release note lists endpoint changes, web developer notified.
- [ ] No breaking change to an endpoint the web already uses without a parallel field or a major version (contracts §12).
- [ ] No secrets in git (`gitleaks` in CI); `.env.example` lists every new variable.
- [ ] Every new CV/geo function has a unit test on small synthetic data (≤ 512×512 px).
- [ ] Review by an equal-or-larger model, comments resolved or answered.
- [ ] How-to-run documented.
- [ ] This phase's gate and all previous gates pass in CI.

---

## A0 — Foundations

**Goal:** the repo builds, tests and runs locally with one command.
**Steps:** [01](dev-plan/01-repo-infra.md). **Entry:** none.

**Deliverables**
- Repo layout per contracts §2, `pyproject.toml`, `Dockerfile`, `infra/docker-compose.yml` (postgis, redis, tusd), `Makefile`, CI, pre-commit, `.env.example`.
- `agridrone.core` (`config`, `logging`, `classes`, `errors`); CLI with empty sub-commands; `/api/v1/healthz`, `/api/v1/meta/classes`; CORS for `http://localhost:5173`.

**Definition of Done**
- [ ] Global DoD.
- [ ] Fresh clone → `make up` → all services `healthy` in < 5 min on macOS arm64.
- [ ] Storage dir writable from `api`, `worker` and `tusd` (same UID).
- [ ] Tag `v0.0.1` builds and pushes `ghcr.io/<org>/agridrone-api` (linux/amd64). **H0 delivered.**

**Gate tests — `make gate-a0`**

| Test | Pass criterion |
|---|---|
| `tests/unit/core/test_settings.py` | Defaults load; `AGRIDRONE_` env overrides; `dev-token` refused when `AGRIDRONE_ENV=prod` |
| `tests/unit/core/test_classes.py` | Codes and colours match contracts §5 exactly |
| `tests/integration/test_healthz.py` | `GET /api/v1/healthz` → 200 with DB, Redis and storage status |
| `tests/integration/test_meta_classes.py` | Returns every code from §5 |
| `tests/integration/test_cors.py` | Preflight from `http://localhost:5173` allowed; other origins not |
| `tests/smoke/compose_up.sh` | `docker compose up --wait` succeeds; postgis, redis, tusd healthy |
| `tests/smoke/cli_help.sh` | `agridrone --help` lists `mock analyze mission openapi db ingest demo` |
| `agridrone openapi --check` | Committed `openapi.json` equals the generated one |

---

## A1 — Synthetic data & geo core

**Goal:** deterministic test scenes with ground truth, plus the geo toolbox every analysis relies on.
**Steps:** [02](dev-plan/02-mock-data.md), [06](dev-plan/06-geo-processing.md). **Entry:** A0 gate.

**Deliverables**
- `agridrone mock generate` (presets `water`, `gaps_rows`, `gaps_dense`, `tiny`, plus `--water-level-delta`), `mock photos`, public dataset downloaders with `MANIFEST.json`, `data/samples/SOURCES.md`.
- `agridrone.geo`: `crs`, `cog`, `raster`, `clip`, `terrain`, `vectorize`, `grid`, `coregister`.

**Definition of Done**
- [ ] Global DoD.
- [ ] The `water` scene opens in QGIS at lat 44.55 / lon 27.10 (screenshot in the PR).
- [ ] At least one public dataset downloaded, licence checked and recorded.
- [ ] `mypy --strict` passes on `agridrone.geo`.

**Gate tests — `make gate-a1`**

| Test | Pass criterion |
|---|---|
| `tests/unit/mock/test_determinism.py` | Same preset + seed → identical mask hash |
| `tests/unit/mock/test_scene_truth.py` | `water_pct` in `scene.json` = % from `truth_mask` (± 0.01) |
| `tests/unit/mock/test_presets_perf.py` | `water` preset generates in < 60 s |
| `tests/unit/mock/test_photos_exif.py` | `mock photos` writes valid GPS EXIF/XMP, read back with `piexif` |
| `tests/unit/geo/test_crs.py` (hypothesis) | 4326 → UTM → 4326 error < 1 mm; East Romania → EPSG:32635 |
| `tests/unit/geo/test_area.py` | 100 × 100 m square → 10 000 ± 5 m² |
| `tests/unit/geo/test_cog.py` | Passes `rio cogeo validate`; mask overviews contain only existing class codes |
| `tests/unit/geo/test_terrain.py` | `depth_in_sink` finds every generated depression centre |
| `tests/unit/geo/test_vectorize.py` | Vectorized truth mask reproduces `water_area_m2` within ± 1 % |
| `tests/unit/geo/test_coregister.py` | 2.5 m shift + 1° rotation realigned to < 0.2 m |

---

## A2 — Analysis baselines

**Goal:** classic (non-ML) detection of standing water and crop gaps, measured against ground truth.
**Steps:** [07](dev-plan/07-cv-water-baseline.md), [08](dev-plan/08-cv-gaps-baseline.md). **Entry:** A1 gate.

**Deliverables**
- `WaterBaselineAnalyzer`, `GapsBaselineAnalyzer` (contracts §6), registered in `cv/registry.py`.
- `agridrone.cv.eval` and `agridrone bench water|gaps --seeds 20` (Markdown + JSON report).
- `agridrone mock export-frontend-fixtures` built from these results. **H2 delivered.**

**Definition of Done**
- [ ] Global DoD.
- [ ] Benchmark report committed under `docs/benchmarks/`.
- [ ] Water analyzer run on one real public orthomosaic (DroneDeploy); visual result in the PR.
- [ ] Known limitations documented in the analyzer and the report.
- [ ] Fixture export reviewed with the web developer (format agreed, committed in web).

**Gate tests — `make gate-a2`**

| Test | Pass criterion |
|---|---|
| `tests/unit/cv/test_eval_metrics.py` | IoU / precision / recall correct on hand-made masks |
| `tests/unit/cv/test_analyzer_contract.py` | Both analyzers return valid COG mask, UTM detections, only §7 metric keys |
| `bench water --seeds 20` (with DSM) | **IoU(water) ≥ 0.80**, area error ≤ 10 % |
| `bench water --seeds 20 --no-dsm` | IoU(water) ≥ 0.60 |
| `tests/unit/cv/water/test_shadows.py` | Shadows detected as water in < 20 % of their area |
| `tests/unit/cv/water/test_perf.py` | `water` scene analysed in < 30 s |
| `tests/unit/cv/gaps/test_rows.py` | Row angle ± 1°, spacing ± 5 % |
| `bench gaps --preset gaps_rows` | Recall ≥ 0.85 on gaps > 1 m; `gap_pct` relative error ≤ 15 % |
| `bench gaps --preset gaps_dense` | IoU(gap) ≥ 0.70 |
| `tests/unit/cv/gaps/test_weed_near_gap.py` | A weed near a gap does not hide it |
| `tests/unit/cv/gaps/test_auto_mode.py` | `auto` picks rows vs. dense correctly on both presets |
| `tests/unit/mock/test_frontend_fixtures.py` | Exported fixtures validate against the OpenAPI response schemas |

---

## A3 — Platform core (parallel to A2)

**Goal:** data model and API for farms, parcels and flights; the mission planner as a pure library.
**Steps:** [03](dev-plan/03-db-api-core.md), [14](dev-plan/14-mission-planner.md). **Entry:** A0 gate (14 also needs `geo.crs` from A1).

**Deliverables**
- PostGIS schema + Alembic, routers for orgs/farms/parcels/crops/flights, GeoJSON/KML/SHP import, dev auth, org isolation, problem+json.
- `agridrone.mission` (`camera`, `grid`, `estimate`, `export`) and `/missions` endpoints.
- `agridrone db seed` with the demo farm. Tag `v0.1.0`. **H1 delivered.**

**Definition of Done**
- [ ] Global DoD.
- [ ] Seeded DB browsable in Swagger UI with the dev token.
- [ ] KML mission for a 20 ha parcel opens in Google Earth or QGIS (screenshot in the PR).
- [ ] 20 ha at 80 m (75/70) falls within 12–15 ha per battery, or the difference is explained.

**Gate tests — `make gate-a3`**

| Test | Pass criterion |
|---|---|
| `tests/integration/db/test_migrations.py` | `upgrade head` then `downgrade base` on an empty DB |
| `tests/integration/api/test_farms_parcels_crud.py` | Full CRUD; `{items,total}` paging; problem+json errors |
| `tests/integration/api/test_parcel_import.py` | GeoJSON, KML, zipped SHP (incl. Stereo70) import correctly |
| `tests/integration/api/test_org_isolation.py` | Org-A user gets 404 on every org-B resource |
| `tests/unit/api/test_geometry_validation.py` | Invalid geometry repaired; > 2000 ha and outside Romania rejected |
| `tests/integration/api/test_area.py` | 100 × 100 m parcel → `area_ha` 1.00 ± 0.01 |
| `tests/unit/mission/test_grid_hypothesis.py` | Random convex/concave polygons: full coverage (sampled), line spacing ± 1 cm, no photo point outside the buffer |
| `tests/unit/mission/test_estimate.py` | Battery split with resume points; 20 ha / 80 m in range |
| `tests/unit/mission/test_export.py` | JSON round-trips; valid KML; Litchi CSV header matches the verified format |

---

## A4 — Ingest & pipeline

**Goal:** a flight goes from photos to analysis results in the DB, automatically.
**Steps:** [04](dev-plan/04-ingest-storage.md), [05](dev-plan/05-photogrammetry.md), [10](dev-plan/10-pipeline-orchestration.md). **Entry:** A2 and A3 gates.

**Deliverables**
- **First PR:** OpenAPI stubs for upload-session, media, capture summary, analyses, jobs and `/ws/jobs` message schema → tag `v0.2.0`. **H3 delivered.**
- `FileStore` (local disk), signed URLs, tus flow (`pre-create` / `post-finish` hooks), EXIF/XMP, dedup, blur score, thumbnails, capture summary, `agridrone ingest folder`.
- `PhotogrammetryEngine`: `MockEngine` (default), `NodeOdmEngine`.
- Celery queues; idempotent chain ingest → photogrammetry → COG → analysis → vectorize → stats; job status over WebSocket; `agridrone demo run`.

**Definition of Done**
- [ ] Global DoD.
- [ ] `agridrone demo run --preset water` from an empty DB in < 2 min (mock photogrammetry).
- [ ] One small public ODM dataset processed with NodeODM end to end (on an x86 machine if emulation is too slow).
- [ ] Every failure ends as `failed` with a useful message, never an unhandled exception.
- [ ] Stubs from `v0.2.0` all replaced by real handlers; no `501` left in this scope.

**Gate tests — `make gate-a4`**

| Test | Pass criterion |
|---|---|
| `tests/unit/storage/test_filestore.py` | Atomic write; `../` keys rejected; `move` is a same-filesystem rename |
| `tests/unit/storage/test_signed_urls.py` | Valid → 200; expired/tampered → 403; Range → 206 |
| `tests/unit/ingest/test_exif_xmp.py` | GPS, time and DJI `RelativeAltitude` from mock and real samples |
| `tests/unit/ingest/test_quality.py` | Blurred fixture flagged `blurry`; sharp one not |
| `tests/integration/ingest/test_tus_flow.py` | Valid token uploads; invalid rejected at `pre-create`; interrupted upload resumes |
| `tests/integration/ingest/test_dedup.py` | Re-upload creates no duplicates |
| `tests/integration/ingest/test_rejects.py` | No-GPS photo accepted with warning; non-media rejected with reason |
| `tests/integration/photogrammetry/test_mock_engine.py` | Synthetic flight → ortho + DSM at contract keys in < 10 s |
| `tests/integration/pipeline/test_chain_eager.py` | `status=succeeded`, detections in PostGIS, `parcel_stat` populated |
| `tests/integration/pipeline/test_idempotent.py` | Re-run without `force` recomputes nothing |
| `tests/integration/pipeline/test_worker_restart.py` (real worker) | Killed mid-chain, restarted, chain completes |
| `tests/integration/pipeline/test_ws_jobs.py` | `/ws/jobs` emits progress events matching the published schema |
| `tests/integration/pipeline/test_stats_match_truth.py` | `water_pct` within the A2 tolerance of `scene.json` |

---

## A5 — Results & media API

**Goal:** everything the dashboard needs: map tiles, detections, statistics, comparisons, exports, media.
**Steps:** [11](dev-plan/11-results-api.md), [13](dev-plan/13-media-video.md). **Entry:** A4 gate.

**Deliverables**
- **First PR:** OpenAPI stubs for every endpoint in steps 11 and 13 → tag `v0.3.0`. **H4 delivered.**
- Tiles via `titiler.core` inside the API, tilejson, detections GeoJSON, stats/timeline, farm summary, compare, risk map, exports (GeoJSON/SHP/KML/CSV), PDF report, weather (seeded).
- HLS transcoding, SRT parser, frame extraction, gallery endpoints with signed URLs.
- `db seed` includes 3 post-rain flights (24/48/72 h) processed end to end.

**Definition of Done**
- [ ] Global DoD.
- [ ] Demo ortho + mask visible in a plain MapLibre test page using only the tilejson.
- [ ] SHP export opens in QGIS; a PDF report is attached to the PR.
- [ ] Web developer has confirmed the real endpoints work against their screens (W6 smoke).

**Gate tests — `make gate-a5`**

| Test | Pass criterion |
|---|---|
| `tests/integration/results/test_tiles.py` | Demo ortho tile → 200 PNG; other org's ID → 404; no endpoint accepts a file path |
| `tests/integration/results/test_timeseries.py` | `water_pct` for 3 seeded flights sorted and correct |
| `tests/integration/results/test_compare.py` | Shifted water → correct appeared / disappeared areas (UTM) |
| `tests/integration/results/test_exports.py` | GeoJSON, SHP zip, KML, CSV valid; feature count = detections |
| `tests/integration/results/test_report_pdf.py` | PDF generated, non-empty, contains the KPI values |
| `tests/integration/results/test_risk_map.py` | Frequency raster over 3 water analyses has values 0–3 in the right places |
| `tests/integration/media/test_hls.py` | Test MP4 → playlist + segments + poster via signed URLs |
| `tests/unit/media/test_srt_parser.py` | Fake DJI SRT → LineString with timestamps |
| `tests/integration/media/test_gallery_paging.py` | 300 photos paged with thumbnails, < 300 ms per page |
| `tests/contract/test_no_stubs.py` | No route in the OpenAPI returns `501` |

---

## A6 — ML models (parallel, optional for the demo)

**Goal:** learned segmentation models that beat the baselines, behind the same `Analyzer` interface.
**Steps:** [09](dev-plan/09-ml-training.md). **Entry:** A2 gate.

**Definition of Done**
- [ ] Global DoD (including `ml/`).
- [ ] Runs tracked in MLflow; `model_card.json` complete (data, metrics, limits, training-data licences).
- [ ] ONNX at `models/{name}/{version}/model.onnx`, selectable per analysis (`analyzer=ml`).
- [ ] Synthetic-to-real gap reported honestly.

**Gate tests — `make gate-a6`**

| Test | Pass criterion |
|---|---|
| `ml/tests/test_dataset_tiles.py` | Tiles and masks aligned; only §5 codes (+255) |
| `ml/tests/test_train_smoke.py` | 1-epoch training on `tiny` runs on CPU in CI |
| `bench water --analyzer ml` (synthetic) | IoU > baseline on the same seeds |
| `bench water --analyzer ml --dataset dronedeploy` | IoU(water) > classic baseline on the DroneDeploy test split |
| `tests/integration/cv/test_onnx_parity.py` | Backend ONNX metrics = `ml/eval.py` ± 0.01 |

---

## A7 — End-to-end & demo (api part)

**Goal:** the whole backend comes up with demo data from scratch, ready for the web e2e suite.
**Steps:** [15](dev-plan/15-e2e-demo.md). **Entry:** A5 gate (A6 optional).

**Deliverables**
- `make demo` (local, prints how to start web) and `make demo-ci` (headless, for web CI). Tag `v0.4.0`. **H5 delivered.**
- `docs/quality-report.md` (generated), `docs/demo.md` (5-minute script, written together with the web developer).

**Definition of Done**
- [ ] Global DoD.
- [ ] `make demo` on a clean machine in < 15 min (no real ODM).
- [ ] Web Playwright demo suite (W7) green against `v0.4.0`.
- [ ] Architecture review by a large model over **both** repos; findings triaged; critical ones fixed.

**Gate tests — `make gate-a7`**

| Test | Pass criterion |
|---|---|
| `tests/e2e/make_demo.sh` (clean CI runner) | `make demo-ci` < 15 min; all 3 parcels have stats; 3 post-rain flights show decreasing `water_pct` |
| `agridrone quality-report --check` | Report regenerates without diffs |
| All previous gates | `gate-a0` … `gate-a6` still green |

---

## A8 — Deploy + real authentication

**Goal:** the system runs on the Linux server over HTTPS, with backups and repeatable deploys, behind real login.
**Steps:** [16](dev-plan/16-deploy.md) + authentication (user/password with argon2 and secure session cookies, or OIDC). **Entry:** A7 gate. A staging server may exist earlier, only behind a VPN or Caddy basic auth.

**Deliverables**
- **First PR:** auth endpoints in OpenAPI (login, logout, me) → tag. **H6 delivered.**
- `deploy/compose.prod.yml`, `Caddyfile`, `deploy.sh` (with rollback), `backup.sh` (restic over SFTP to another machine), `docs/deploy.md`, `docs/restore.md`.

**Definition of Done**
- [ ] Global DoD.
- [ ] Blank Ubuntu 24.04 x86_64 → working app over HTTPS in < 1 hour following `docs/deploy.md`.
- [ ] Only 80/443 public; SSH restricted.
- [ ] Deploy and rollback rehearsed on staging.
- [ ] Nightly backup running; a restore onto a blank server performed and documented.
- [ ] Disk, RAID and uptime alerts configured and fired once as a test.
- [ ] Tag `v1.0.0`.

**Gate tests — `make gate-a8`** (against staging)

| Test | Pass criterion |
|---|---|
| `tests/unit/auth/test_passwords.py` | argon2 hashing; wrong password rejected; timing-safe compare |
| `tests/integration/auth/test_sessions.py` | Login sets HttpOnly/Secure/SameSite cookie; logout invalidates; org isolation still holds |
| `tests/deploy/ports.sh` | External scan finds only 80 and 443 |
| `tests/deploy/tls.sh` | Valid certificate; HTTP → HTTPS; HSTS present |
| `tests/deploy/health.sh` | `/api/v1/healthz` 200 with DB, Redis, free disk |
| `tests/deploy/auth_prod.sh` | `Bearer dev-token` → 401; anonymous → 401; login works |
| `tests/deploy/internal_blocked.sh` | `/api/internal/*` unreachable from outside |
| `tests/deploy/upload_resume.sh` | 300 photos via `/uploads/`; interrupted upload resumes |
| `tests/deploy/deploy_rollback.sh` | Tag N+1 healthy; rollback to N healthy; downtime ≤ a few seconds |
| `tests/deploy/backup_restore.sh` | Latest snapshot restored on a blank server; row counts and a file checksum match |

---

## Coordination with the web developer

- **Weekly sync (30 min):** check handoff dates, triage `api-request` issues, agree on the next tag.
- **Shared timeline** (weeks are indicative):

| Week | API (this plan) | Web | Handoff |
|---|---|---|---|
| 1 | A0, A1 starts | W0, W1 | H0 `v0.0.1` |
| 2 | A1 | W1 | — |
| 3 | A2 ║ A3 | W2 on hand-written mocks | — |
| 4 | A2 ║ A3 → A4 stubs | W2, W3 | H1 `v0.1.0`, H2 fixtures, H3 `v0.2.0` |
| 5 | A4 → A5 stubs | W4 | H4 `v0.3.0` |
| 6–7 | A5 ║ A6 | W5, W6 | `v0.3.x` real endpoints |
| 8 | A7 | W7 | H5 `v0.4.0` |
| 9 | A8 | W8 | H6 auth, `v1.0.0` |

- **Blocked rule:** if the web is blocked for more than a day on a missing endpoint, the api developer ships a stub for it first, then the implementation.
