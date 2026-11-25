# agridrone-api

Backend Python pentru AgriDrone CV: detecția zonelor cu băltire și a golurilor din culturi, din imagini de dronă.
Frontend-ul este în repo-ul separat `agridrone-web`.

## Cerințe

- Python 3.12 (manager: [uv](https://docs.astral.sh/uv/))
- Docker Engine + Docker Compose v2
- MySQL 8.0+ existent, în container pe host (serverul curent rulează 8.0.44; nu este pornit de acest stack; fără PostGIS)
- Linux sau macOS (pe macOS arm64, NodeODM rulează doar prin emulare, în profilul `odm`)

## Pornire rapidă

```bash
cp .env.example .env
# completează în .env datele containerului MySQL existent
uv sync
make up
uv run agridrone --help
```

`make up` pornește Redis, tusd, API-ul și worker-ul. MySQL este containerul existent de pe host,
configurat prin `MYSQL_HOST`/`MYSQL_PORT` în `.env`; API-ul îl verifică prin `/healthz`.
Toate serviciile cu healthcheck trebuie să ajungă `healthy`. NodeODM nu pornește implicit:

```bash
docker compose --env-file .env -f infra/docker-compose.yml --profile odm up -d
```

## Servicii locale

| Serviciu | Port host | URL / note |
|---|---|---|
| API | 7100 | <http://localhost:7100/docs> |
| tusd | 7101 | upload-uri reluabile, scrie în `data/store/_uploads` |
| MySQL | `MYSQL_PORT` (implicit 3306) | container existent pe host; nu pornește din compose |
| Redis | 7103 | broker Celery |
| NodeODM | 7104 | doar cu profilul `odm`, `platform: linux/amd64` |
| Web (Vite) | 5173 | `agridrone-web`, origine permisă prin CORS |

Porturile interne din containere rămân cele din contracte (API 8000, tusd 8080, Redis 6379,
NodeODM 3000). Pe host sunt mapate în intervalul 7100–7200, ca să nu intre în conflict
cu alte containere de pe mașină. MySQL își păstrează portul existent, configurabil prin `MYSQL_PORT`.
Web-ul trebuie configurat să apeleze API-ul la `http://localhost:7100`.

Containerul MySQL existent trebuie să fie accesibil din rețeaua Docker a stack-ului. Implicit se
folosește `host.docker.internal:MYSQL_PORT` (prin `extra_hosts: host-gateway`); dacă MySQL e într-o
rețea Docker comună, setează `MYSQL_HOST` la numele containerului și atașează serviciile la acea rețea.

API-ul, worker-ul și tusd montează același director `data/` și rulează cu UID/GID-ul utilizatorului
hostului (`AGRIDRONE_UID`/`AGRIDRONE_GID`, exportate de Makefile), ca scrierile să fie consistente.

## Comenzi

```bash
make up            # pornește infrastructura și aplicația
make down          # oprește serviciile
make logs          # logurile serviciilor
make test          # pytest
make lint          # ruff check + ruff format --check + mypy strict
make fmt           # ruff format + ruff check --fix
make migrate       # alembic upgrade head
make mock-data     # generatorul de date mock (placeholder până la pasul 02)
make openapi       # scrie openapi/openapi.json
make openapi-check # verifică dacă openapi/openapi.json este la zi
make gate-a0       # lint + teste + OpenAPI + smoke test compose
```

Testele și lint-ul se pot rula și direct:

```bash
uv run pytest
uv run ruff check
uv run mypy
```

## Configurare

Toate variabilele aplicației au prefixul `AGRIDRONE_` și sunt citite cu `pydantic-settings`.
Lista completă este în `.env.example`. `.env` nu se comite niciodată.

- `AGRIDRONE_ENV=dev|prod` — în `prod` logurile sunt JSON; în `dev`, text.
- `AGRIDRONE_STORAGE_DIR` — rădăcina fișierelor aplicației (implicit `./data/store`).
- `AGRIDRONE_DATABASE_URL` — SQLAlchemy async URL pentru MySQL (`mysql+asyncmy://...`); în Docker se construiește din `MYSQL_HOST`/`MYSQL_PORT`/`MYSQL_DATABASE`/`MYSQL_USER`/`MYSQL_PASSWORD`.
- `AGRIDRONE_REDIS_URL` — în Docker hostul este `redis`.
- `AGRIDRONE_CORS_ORIGINS` — listă separată prin virgule.
- Geometriile sunt stocate ca GeoJSON (EPSG:4326, lon/lat) în coloane `JSON`, cu coloane `bbox_*` pentru indexare; calculele metrice se fac în UTM, în Python.

## Structură

```
src/agridrone/
├── core/      # config, logging, coduri de clase, erori de domeniu
├── api/v1/    # routere FastAPI
├── db/        # modele SQLAlchemy, sesiuni, migrări Alembic
├── storage/   # FileStore pe disc local (pasul 04)
├── ingest/    # EXIF, validare, asociere zbor (pasul 04)
├── photogrammetry/  # mock + NodeODM (pasul 05)
├── geo/       # COG, reproiectare, decupare, teren (pasul 06)
├── cv/        # analizoare water/gaps (pașii 07–08)
├── mission/   # planificator de misiuni (pasul 14)
├── mock/      # date sintetice (pasul 02)
├── workers/   # Celery (pasul 10)
└── cli.py     # comanda `agridrone`
```

Contracte obligatorii: [`docs/dev-plan/00-contracts.md`](docs/dev-plan/00-contracts.md).
Planul pe faze: [`docs/IMPLEMENTATION_PLAN.md`](docs/IMPLEMENTATION_PLAN.md).
