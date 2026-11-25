# 03: Baza de date + API core (organizații, ferme, parcele, zboruri)

| | |
|---|---|
| **Scop** | Modelul de date și API-ul de bază pe care se sprijină restul |
| **Depinde de** | 01 |
| **Model AI** | Implementare: **mediu** · Schema DB și review: **mare** |
| **Durată** | 3–4 zile |

## Ce se construiește

1. **Modele SQLAlchemy** (`agridrone/db/models.py`). Geometriile sunt GeoJSON (EPSG:4326, lon/lat) în coloane `JSON`, cu coloane `bbox_*` pentru filtre și index B-tree. Calculele metrice se fac în Python, în UTM:
   - `organization`, `user` (cu `role`: `admin`, `agronomist`, `pilot`, `viewer`);
   - `farm` (`org_id`, `name`, `location` JSON Point);
   - `parcel` (`farm_id`, `name`, `geom` JSON MultiPolygon, `bbox_min_lon`, `bbox_min_lat`, `bbox_max_lon`, `bbox_max_lat`, `area_ha` calculat în UTM, `apia_code`, `notes`);
   - `season_crop` (`parcel_id`, `season`, `crop`, `sowing_date`, `target_density_per_ha`, `row_spacing_m`);
   - `flight` (`parcel_id`, `flown_at`, `type`: `post_rain` | `routine` | `reference_dry`, `altitude_m`, `status`, `notes`);
   - `media_asset`, `orthomosaic`, `analysis_run`, `detection` (geom JSON + bbox), `parcel_stat`: doar schema aici; se populează în pașii 04–11;
   - `weather_event` (`farm_id`, `start`, `end`, `precip_mm`, `source`).
2. **Migrare Alembic inițială**, cu index B-tree pe coloanele `bbox_*` ale geometriilor (MySQL nu are GiST/PostGIS).
3. **Routere `api/v1`:**
   - `GET/POST /farms`, `GET/PATCH/DELETE /farms/{id}`;
   - `GET/POST /parcels`, `GET/PATCH/DELETE /parcels/{id}`, cu filtru `farm_id` și `bbox`;
   - `POST /parcels/import`: GeoJSON / KML / Shapefile zip, cu răspuns de previzualizare + `commit=true`;
   - `GET/POST /parcels/{id}/crops`;
   - `GET/POST /flights`, `GET /flights/{id}`, cu filtre `parcel_id`, `from`, `to`, `type`;
   - `GET /meta/classes` (din `core/classes.py`);
   - `GET /healthz`.
4. **Validări geometrice:**
   - geometria e validă (altfel `make_valid`);
   - aria se calculează în UTM;
   - limită de 2000 ha per parcelă;
   - se respinge o geometrie în afara României (bbox), cu mesaj clar.
5. **Autentificare dev:** dependency FastAPI care acceptă `Bearer dev-token` și mapează pe un user seed. Fiecare query filtrează după `org_id`.
6. **Export OpenAPI:** `agridrone openapi` scrie `openapi/openapi.json` (contractul cu `agridrone-web`, `00-contracts.md` §12). La sfârșitul pasului se pune tag-ul `v0.1.0`, ca web-ul să pornească pe el.
7. **`agridrone db seed`** (folosește `mock seed-db` din 02 dacă există).

## Criterii de acceptanță

- [ ] `make migrate` creează schema pe o bază goală. `alembic downgrade base` funcționează.
- [ ] Testele de integrare (pytest + containerul MySQL existent, sau testcontainers) acoperă CRUD-ul pe ferme și parcele, importul GeoJSON și KML, și izolarea între organizații (un user din org A nu vede org B).
- [ ] `area_ha` pentru un dreptunghi cunoscut (ex. 100 × 100 m) iese 1,00 ± 0,01.
- [ ] Erorile ies în format problem+json.
- [ ] `openapi/openapi.json` e generat, valid și comis.

## Prompt de start

```
Implementezi pasul 03 din docs/dev-plan/03-db-api-core.md respectând docs/dev-plan/00-contracts.md.
Începe cu schema (modele + migrare) și arată-mi-o înainte de routere.
Folosește SQLAlchemy 2 async + driver asyncmy + FastAPI. Testele de integrare rulează pe containerul MySQL existent.
Fără GeoAlchemy2 și fără funcții spațiale MySQL: geometriile sunt GeoJSON în coloane JSON, cu bbox_*.
Atenție: ariile se calculează în UTM (agridrone.geo.crs.utm_crs_for), niciodată în 4326.
```

## Capcane

- Shapefile-urile APIA pot fi în Stereo70 (EPSG:3844). Importul citește `.prj` și reproiectează în 4326.
- KML poate conține mai multe poligoane sau foldere. Se afișează lista și utilizatorul alege.
