# 01: Repo `agridrone-api`, tooling și infrastructură locală

| | |
|---|---|
| **Scop** | Scheletul repo-ului `agridrone-api`, care rulează local cu o singură comandă. Scheletul `agridrone-web` e în pasul 12 (repo-ul web) |
| **Depinde de** | — |
| **Model AI** | Implementare: **mediu** · Review: **mare** |
| **Durată** | 1–2 zile |

> **Stare:** ✅ Completat la 2026-11-25. Tracker: [STATUS.md](STATUS.md).
> Validarea de runtime a stack-ului Docker se face pe host; în sandbox `docker compose config` trece,
> dar nu există Docker daemon. Porturile publicate pe host sunt 7100–7200, cele interne rămân cele din contracte.

## Ce se construiește

1. **Structura de foldere** din `00-contracts.md` §2, cu `.gitkeep` în folderele goale și `.gitignore`. Se ignoră:
   - `data/`, `.env`, `*.tif`, `*.onnx`;
   - `.venv/`, `__pycache__/`.
2. **`pyproject.toml`** în rădăcina repo-ului (uv):
   - dependențele din contracte, cu grupuri: `dev`, `geo`, `cv`;
   - entry point `agridrone = "agridrone.cli:app"`.
3. **`agridrone/core/`:**
   - `config.py`: `Settings` cu pydantic-settings, prefix `AGRIDRONE_`;
   - `logging.py`: log JSON în producție, text în dev;
   - `classes.py`: coduri de clase §5;
   - `errors.py`: excepții de domeniu.
4. **`agridrone/cli.py`** (typer) cu subcomenzile goale `mock`, `analyze`, `mission`, `openapi`, `db`.
5. **`infra/docker-compose.yml`:**
   - `postgis` (imaginea `postgis/postgis:16-3.4`);
   - `redis:7`;
   - `tusd` (`tusproject/tusd`): upload-uri reluabile, scrie în `${AGRIDRONE_STORAGE_DIR}/_uploads`, cu hook-uri HTTP spre API (pasul 04);
   - **fără** MinIO și fără TiTiler separat: fișierele stau pe disc, iar tile-urile le servește API-ul (pasul 11);
   - `api`, `worker` și `tusd` montează **același** director de stocare;
   - `nodeodm` (`opendronemap/nodeodm`) în profilul `odm`, care nu pornește implicit;
   - serviciile `api` și `worker` pornesc din același `Dockerfile` (în rădăcină, multi-stage, cu GDAL);
   - porturile din `00-contracts.md` §12.
   - API-ul are CORS deschis pentru `AGRIDRONE_CORS_ORIGINS` (implicit `http://localhost:5173`), ca web-ul să meargă direct pe el.
6. **`.env.example`** cu toate variabilele.
7. **`Makefile` sau `justfile`:**
   - `up`, `down`, `test`, `lint`, `fmt`, `migrate`;
   - `mock-data` (pasul 02), `openapi` (scrie `openapi/openapi.json`).
8. **CI** în GitHub Actions:
   - `ruff`, `mypy` și `pytest`;
   - `agridrone openapi --check`: pică dacă `openapi/openapi.json` nu e la zi;
   - pe tag `vX.Y.Z`: build `linux/amd64` și push în `ghcr.io/<org>/agridrone-api` (folosit la deploy, pasul 16).
9. **pre-commit:** ruff, end-of-file-fixer, check-added-large-files (blochează fișiere peste 5 MB).

## Criterii de acceptanță

- [x] `make up` pornește postgis, redis și tusd. Toate sunt `healthy`.
- [x] `uv run agridrone --help` afișează subcomenzile.
- [x] `uv run pytest` rulează și trece (cel puțin un test de smoke pe `Settings` și `classes`).
- [x] Directorul de stocare există și e scriibil din `api`, `worker` și `tusd` (același UID în containere).
- [x] `make openapi` scrie `openapi/openapi.json`, iar `agridrone openapi --check` trece.
- [x] Pe Mac arm64 imaginile pornesc nativ sau sunt marcate explicit `platform: linux/amd64`. Imaginea NodeODM e doar amd64: rulează lent prin emulare, de aceea e într-un profil separat.

## Prompt de start

```
Ești un inginer Python senior. Construiești pasul 01 (repo-ul agridrone-api) din docs/dev-plan/01-repo-infra.md
pentru proiectul descris în docs/dev-plan/00-contracts.md (respectă-l strict).
Întâi propune lista de fișiere și conținutul lor pe scurt; așteaptă confirmarea.
Apoi implementează, rulează `make up`, `uv run pytest`, `uv run ruff check` și raportează rezultatul.
Workstation: macOS arm64. Nu adăuga dependențe în afara celor din contracte fără să le justifici.
```

## Capcane

- GDAL/rasterio în Docker: folosește o imagine de bază cu GDAL (ex. `ghcr.io/osgeo/gdal:ubuntu-small-3.9.x`) sau wheel-urile `rasterio` care includ GDAL. Nu compila GDAL.
- Permisiuni pe volumul comun: `api`, `worker` și `tusd` rulează cu același UID/GID (ex. `1000:1000`), altfel apar erori de scriere doar în producție.
