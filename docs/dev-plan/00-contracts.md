# 00: Contracte comune (obligatorii pentru orice asistent AI și orice componentă)

> Atașează fișierul ăsta la **fiecare** sesiune cu un asistent AI.
> Dacă o componentă are nevoie să schimbe ceva de aici, schimbarea se face **întâi aici** (PR separat, review cu un model mare), apoi în cod.

## 1. Stack și tooling

| Ce | Alegere |
|---|---|
| Python | 3.12 |
| Manager pachete | `uv` (`pyproject.toml` în rădăcina repo-ului; `ml/` are propriul `pyproject.toml`) |
| Lint / format | `ruff` (line-length 110), `ruff format` |
| Tipuri | `mypy --strict` pe `agridrone/core`, `agridrone/cv`, `agridrone/geo`, `agridrone/mission` |
| Teste | `pytest`, `pytest-asyncio`, `hypothesis` (pentru geometrie) |
| API | FastAPI, Pydantic v2, SQLAlchemy 2 (async, driver `asyncmy`), Alembic |
| DB | MySQL 8.4 LTS (InnoDB, `utf8mb4`), container existent pe host; nu se pornește din compose |
| Geometrii în DB | GeoJSON (EPSG:4326, lon/lat) în coloane `JSON` + coloane `bbox_*` pentru index B-tree; fără PostGIS |
| Cozi | Celery 5 + Redis |
| Stocare fișiere | **disc local** (sistem de fișiere), prin interfața `FileStore`. Fără S3 / MinIO |
| Upload-uri mari | protocolul **tus** (reluabil): serverul `tusd` + Uppy în web |
| Tile-uri raster | `titiler.core` **inclus în API** (nu serviciu separat) |
| Geo | `rasterio`, `rio-cogeo`, `shapely` 2, `geopandas`, `pyproj`, `whitebox` |
| CV / ML | `opencv-python-headless`, `scikit-image`, `numpy`; ML: `torch`, `segmentation-models-pytorch`, `onnxruntime` |
| CLI | `typer`, comanda `agridrone` |
| Frontend | în repo-ul separat `agridrone-web` (vezi §12) |

## 2. Repo-uri și structură

Proiectul are **două repo-uri**. Ele comunică **numai** prin contractul HTTP (§12).

| Repo | Conține | Pași din plan |
|---|---|---|
| `agridrone-api` (acesta) | backend Python, workers, CV, ML, mission planner, infra locală, date mock, planul (`docs/`) | 01–11, 13, 14, 15 |
| `agridrone-web` | aplicația React (dashboard-uri, hărți, upload, planificator UI), teste Playwright | 12 (+ partea UI din 15) |

Local, cele două se clonează unul lângă altul:

```
agri-drone/
├── agridrone-api/
└── agridrone-web/
```

Structura `agridrone-api`:

```
agridrone-api/
├── CLAUDE.md                     # trimite la docs/dev-plan/00-contracts.md
├── pyproject.toml  uv.lock  Dockerfile  Makefile  .env.example
├── src/agridrone/
│   ├── core/                     # config (pydantic-settings), logging, erori, tipuri comune
│   ├── db/                       # modele SQLAlchemy, sesiuni, migrations/ (Alembic)
│   ├── api/v1/                   # routere FastAPI
│   ├── storage/                  # interfața FileStore + LocalFileStore, URL-uri semnate, hook-uri tus
│   ├── ingest/                   # EXIF, validare, asociere zbor
│   ├── photogrammetry/           # mock + NodeODM
│   ├── geo/                      # COG, reproiectare, decupare, teren
│   ├── cv/                       # analizoare: water/, gaps/, common/
│   ├── mission/                  # planificator misiuni (geometrie pură)
│   ├── mock/                     # generator date sintetice, download seturi publice
│   ├── workers/                  # Celery app + task-uri
│   └── cli.py                    # typer: `agridrone ...`
├── tests/
│   └── unit/  integration/  fixtures/
├── openapi/openapi.json          # contractul cu agridrone-web, generat și comis (§12)
├── ml/                           # antrenare (proiect uv separat), configs, notebooks
├── infra/                        # docker-compose.yml pentru dezvoltare locală
├── deploy/                       # producție: compose.prod.yml, Caddyfile, deploy.sh, backup.sh (pasul 16)
├── data/                         # NU intră în git (doar .gitkeep)
│   └── synthetic/  public/  samples/  work/
└── docs/
    ├── Plan_Proiect_AgriDrone.pdf
    └── dev-plan/
```

## 3. Sisteme de coordonate (sursa nr. 1 de bug-uri)

- **În DB**, geometriile sunt în **EPSG:4326** (lon/lat).
- **Calculele** (arii, distanțe, buffere, grile) se fac **numai într-un CRS proiectat în metri**, ales cu `agridrone.geo.crs.utm_crs_for(geom) -> pyproj.CRS`:
  - EPSG:32635 (UTM 35N) pentru estul României;
  - EPSG:32634 (UTM 34N) pentru vest.
- **Rasterele** procesate se salvează în CRS-ul UTM al parcelei.
- **Interzis:** `geom.area` sau `buffer()` pe geometrii în 4326.
- **MySQL:** nu există PostGIS. Geometriile se stochează ca GeoJSON (EPSG:4326, lon/lat) în coloane
  `JSON`, însoțite de coloane `bbox_min_lon`, `bbox_min_lat`, `bbox_max_lon`, `bbox_max_lat` pentru
  filtre și index B-tree. Toate calculele metrice (arii, buffere, intersecții, diferențe) se fac în
  Python, cu Shapely/GeoPandas/pyproj, în CRS proiectat UTM. Nu se folosesc funcții spațiale MySQL
  pentru arii sau distanțe.
- **Locația implicită a datelor sintetice:** centrul parcelei la `lat=44.55, lon=27.10` (Bărăgan, UTM 35N).

## 4. Formate de date

| Artefact | Format |
|---|---|
| Ortomozaic | COG GeoTIFF, 3 benzi RGB `uint8` (sau 4 cu alpha), compresie JPEG/WEBP, overview-uri |
| DSM / DTM | COG GeoTIFF, 1 bandă `float32`, metri, `nodata = -9999` |
| Mască de clase | COG GeoTIFF, 1 bandă `uint8`, coduri din §5, `nodata = 0` |
| Probabilități | COG GeoTIFF `uint8` (0–255 = 0–1), câte o bandă pe clasă |
| Detecții | GeoJSON (EPSG:4326) cu proprietățile din §6 + tabel MySQL (geometrie JSON + bbox) |
| Parcele (import) | GeoJSON / KML / Shapefile (zip) |

## 5. Coduri de clase (identice în măști, ML, DB și frontend)

| Cod | Nume (`class_name`) | Culoare UI |
|---|---|---|
| 0 | `nodata` | transparent |
| 1 | `soil` | `#A1887F` |
| 2 | `vegetation` | `#43A047` |
| 3 | `water` | `#1E88E5` |
| 4 | `wet_soil` | `#5D4037` |
| 5 | `weed` | `#FDD835` |
| 6 | `gap` | `#E53935` (ieșire a analizei de goluri, nu clasă de pixel brut) |
| 7 | `other` | `#9E9E9E` (drumuri, umbre, obiecte) |
| 255 | `ignore` | — (doar la antrenare) |

Codurile sunt definite **o singură dată**, în `agridrone/core/classes.py` (`IntEnum` + culori). Frontend-ul le primește din `GET /api/v1/meta/classes`.

## 6. Interfața comună a analizoarelor

```python
# agridrone/cv/common/base.py
class AnalysisType(StrEnum):
    WATER = "water"
    GAPS = "gaps"

@dataclass(frozen=True)
class AnalysisInput:
    ortho_path: Path                 # COG RGB, CRS UTM
    parcel_geom_utm: BaseGeometry    # în CRS-ul rasterului
    dsm_path: Path | None = None
    reference_dsm_path: Path | None = None   # zbor „uscat”, opțional
    params: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class AnalysisResult:
    mask_path: Path                  # COG uint8, coduri §5
    detections: gpd.GeoDataFrame     # CRS UTM; coloane: class_name, area_m2, confidence, geometry
    stats: dict[str, float]          # chei din §7
    debug_paths: dict[str, Path]     # imagini intermediare (opțional)

class Analyzer(Protocol):
    type: AnalysisType
    version: str                     # ex. "water-baseline-0.1.0"
    def run(self, inp: AnalysisInput, out_dir: Path) -> AnalysisResult: ...
```

Registrul analizoarelor e în `agridrone/cv/registry.py`: `get_analyzer(type, name="baseline")`.

## 7. Nume de metrici (statistici)

`parcel_area_m2`, `water_area_m2`, `water_pct`, `water_zones`, `water_max_zone_m2`, `wet_soil_pct`,
`veg_cover_pct`, `gap_area_m2`, `gap_pct`, `gap_zones`, `gap_max_zone_m2`, `weed_pct`,
`plants_per_ha` (opțional), `rows_detected` (opțional).

Procentele sunt **0–100** și se calculează față de `parcel_area_m2` (după bufferul intern al parcelei).

## 8. Stocarea fișierelor (disc local)

- Rădăcina e `AGRIDRONE_STORAGE_DIR`: `./data/store` în dev, `/srv/agridrone/files` pe server.
- Căile de mai jos sunt **chei relative** la rădăcină. În DB se salvează numai cheia, niciodată calea absolută.
- **Scriere atomică:** fișier temporar în același director, apoi `os.replace`. Un fișier pe jumătate scris nu e niciodată vizibil.
- Fișierele nu se expun direct din disc. Clientul le primește numai prin API, după verificarea organizației, cu URL-uri semnate (§9).

```
{org_id}/parcels/{parcel_id}/flights/{flight_id}/raw/{filename}
{org_id}/parcels/{parcel_id}/flights/{flight_id}/video/{filename}
{org_id}/parcels/{parcel_id}/flights/{flight_id}/ortho/orthophoto.cog.tif
{org_id}/parcels/{parcel_id}/flights/{flight_id}/ortho/dsm.cog.tif
{org_id}/parcels/{parcel_id}/flights/{flight_id}/ortho/dtm.cog.tif
{org_id}/parcels/{parcel_id}/analyses/{analysis_id}/mask.cog.tif
{org_id}/parcels/{parcel_id}/analyses/{analysis_id}/detections.geojson
{org_id}/parcels/{parcel_id}/analyses/{analysis_id}/debug/...
{org_id}/parcels/{parcel_id}/flights/{flight_id}/thumbs/{media_id}.jpg
{org_id}/parcels/{parcel_id}/flights/{flight_id}/hls/{media_id}/...
models/{name}/{version}/model.onnx
_uploads/                          # zona de lucru a tusd (fișiere incomplete), nu se servește
```

Toate trebuie să fie pe **același sistem de fișiere**, ca mutarea din `_uploads/` în `raw/` să fie un `rename`, nu o copiere.

ID-urile sunt UUID v7 (sortabile după timp), generate în aplicație.

## 9. Convenții API

- Prefix: `/api/v1`. JSON cu nume `snake_case`. Date ISO-8601 UTC.
- **Erori:** `application/problem+json` (RFC 9457) cu `type`, `title`, `status`, `detail`.
- **Paginare:** `?limit=50&offset=0`; răspuns `{ "items": [...], "total": N }`.
- **Geometrii** în request și response: GeoJSON (EPSG:4326).
- **Fișiere către browser** (poze, thumbnail-uri, video, HLS, exporturi): URL-uri semnate de forma `/api/v1/files/{scope}/{id}/...?exp=<unix>&sig=<hmac>`.
  - HMAC-SHA256 cu `AGRIDRONE_SECRET_KEY`; expirare implicită 15 min;
  - așa funcționează în `<img>` și `<video>`, care nu pot trimite header-ul `Authorization`;
  - răspunsul suportă `Range` (necesar pentru video).
- **Tile-uri:** `/api/v1/tiles/{layer}/{id}/{z}/{x}/{y}.png`. API-ul mapează `id` → fișier după ce verifică organizația. Clientul nu trimite niciodată o cale de fișier.
- **Autentificare (deocamdată):** token static de dezvoltare `Authorization: Bearer dev-token`, acceptat **numai** când `AGRIDRONE_ENV=dev`. Modelul `user` și `org` există din start, ca să adăugăm OIDC mai târziu fără migrare dureroasă.
- Contractul OpenAPI se exportă cu `agridrone openapi` în `openapi/openapi.json` (vezi §12).

## 10. Configurare

- Prin variabile de mediu `AGRIDRONE_*` (pydantic-settings). `.env.example` stă în repo, `.env` niciodată.
- Comutatoare importante:
  - `AGRIDRONE_PHOTOGRAMMETRY_MODE=mock|nodeodm`
  - `AGRIDRONE_DATA_DIR=./data` (date mock și publice)
  - `AGRIDRONE_STORAGE_DIR=./data/store` (fișierele aplicației, §8)
  - `AGRIDRONE_SECRET_KEY` (semnarea URL-urilor de fișiere)
  - `AGRIDRONE_TUS_URL=http://localhost:8080/files/` (dev; în prod `/uploads/`, același domeniu)
  - `AGRIDRONE_CORS_ORIGINS=http://localhost:5173` (dev-serverul din `agridrone-web`; în prod nu e nevoie, web și API sunt pe același domeniu)
  - `AGRIDRONE_ENV=dev|prod`
  - `AGRIDRONE_PUBLIC_URL` (prod, vezi pasul 16)
- **Deploy:** un singur server Linux cu `docker compose` (pasul 16). Fără Kubernetes. Imaginile se publică în GHCR, cu tag-uri `vX.Y.Z`.

## 11. Reguli pentru codul scris de asistenți AI

- Funcții pure în `cv/`, `geo/` și `mission/`: fără DB, fără rețea, fără variabile globale. I/O doar prin căi primite ca parametri.
- Fiecare funcție CV sau geo nouă primește un test pe date sintetice mici (≤ 512×512 px), generate în fixture.
- Fără `print`: se folosește `logging` (`agridrone.core.logging.get_logger`).
- Dependențele noi se justifică în PR. Se preferă cele deja listate în §1.
- Nu se modifică fișierele altei componente fără să fie menționat explicit în PR.

## 12. Contractul dintre `agridrone-api` și `agridrone-web`

- **Singura sursă de adevăr e `openapi/openapi.json`**, comis în `agridrone-api`.
  - CI-ul api pică dacă fișierul comis diferă de cel generat (`agridrone openapi --check`).
  - Orice PR care schimbă API-ul include și `openapi.json` regenerat, iar descrierea PR-ului listează endpoint-urile schimbate.
- **Versionare:**
  - api primește tag-uri `vX.Y.Z`;
  - o schimbare care strică clienții (câmp șters sau redenumit, tip schimbat) cere versiune majoră nouă sau un câmp nou în paralel cu cel vechi, până se actualizează web-ul;
  - adăugările sunt libere.
- **Cum ajunge contractul în web:** `agridrone-web` ține o copie în `src/api/openapi.json`, actualizată cu `npm run api:sync`.
  - local, copiază din `../agridrone-api/openapi/openapi.json`;
  - în CI, ia fișierul de la un tag api fixat în `api-version.txt`.
- **Date mock pentru web:** `agridrone mock export-frontend-fixtures --out <dir>` scrie JSON-uri și câteva tile-uri PNG mici. Web-ul le comite în `src/mocks/fixtures/` și le folosește în MSW.
- **Ce NU se duplică în web:**
  - codurile și culorile claselor vin la rulare din `GET /api/v1/meta/classes`;
  - nicio geometrie UTM nu trece prin API, doar GeoJSON EPSG:4326.
- **În producție** (pasul 16): web și API stau pe același domeniu, în spatele Caddy. Web-ul apelează `/api/...` relativ, fără CORS.
- **Porturi locale:**
  - pe host: api `7100`, tusd `7101`, Redis `7103`, NodeODM `7104`;
  - MySQL este containerul existent de pe host, cu portul din `MYSQL_PORT` (implicit `3306`); nu este pornit de stack;
  - web (Vite): `5173`;
  - în containere, porturile interne rămân cele clasice: API `8000`, tusd `8080`,
    Redis `6379`, NodeODM `3000`. Maparea host → container se face în `infra/docker-compose.yml`.
