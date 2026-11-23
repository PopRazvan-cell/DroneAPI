# 11: API pentru rezultate (tile-uri, detecții, statistici, exporturi)

| | |
|---|---|
| **Scop** | Tot ce îi trebuie frontend-ului ca să afișeze hărți, grafice și rapoarte |
| **Depinde de** | 03, 06, 10 |
| **Model AI** | Implementare: **mediu** · Review: **mare** |
| **Durată** | 3–4 zile |

## Ce se construiește

1. **Tile-uri raster cu `titiler.core` inclus în API:**
   - un `TilerFactory` montat sub `/api/v1/tiles/...`, cu un `path_dependency` propriu: primește `layer` + `id`, verifică organizația și întoarce calea locală a COG-ului. Clientul nu trimite niciodată o cale;
   - `GET /orthomosaics/{id}/tilejson?layer=ortho|dsm|mask|prob_water` întoarce TileJSON cu aceste URL-uri;
   - dacă randarea tile-urilor încarcă API-ul, aceeași imagine pornește un serviciu `tiles` separat (altă comandă), fără schimbări de cod.
   - colormap pentru `mask` din `core/classes.py`; `dsm` cu rescale și colormap `terrain`.
2. **Detecții:**
   - `GET /analyses/{id}/detections.geojson?class=water` (4326);
   - opțional, vector tiles: `GET /tiles/detections/{z}/{x}/{y}.pbf` cu `ST_AsMVT`.
3. **Statistici și timeline:**
   - `GET /parcels/{id}/stats?metric=water_pct&from&to` → serie de timp;
   - `GET /parcels/{id}/timeline` → zboruri + analize + KPI pe fiecare;
   - `GET /farms/{id}/summary` → KPI per parcelă (ultima valoare + trend).
4. **Comparație:** `GET /parcels/{id}/compare?a={analysis_id}&b={analysis_id}` → poligoane apărute, dispărute și persistente, cu arii (`ST_Difference`, `ST_Intersection` în UTM).
5. **Hartă de risc multi-eveniment:** `POST /parcels/{id}/risk-map` (task) → raster cu frecvența apei pe toate analizele `water` → COG + tilejson.
6. **Exporturi:**
   - `GET /analyses/{id}/export?format=geojson|shp|kml|csv`;
   - `POST /reports` → PDF per parcelă (WeasyPrint cu template HTML: hartă statică, KPI, grafice randate pe server cu matplotlib).
7. **Meteo (mock acum, real mai târziu):** `GET /farms/{id}/weather?from&to`. În dev citește din `weather_event` (seed). Adaptorul Open-Meteo e opțional.

## Criterii de acceptanță

- [ ] Ortomozaicul și masca din demo-ul sintetic se văd în orice client XYZ (ex. un `index.html` de test cu MapLibre) folosind tilejson-ul.
- [ ] Seria `water_pct` pe 3 zboruri seed se întoarce sortată și corectă.
- [ ] Comparația pe două analize sintetice cu apă deplasată dă arii apărute și dispărute corecte (test).
- [ ] Exportul Shapefile se deschide în QGIS. Raportul PDF se generează.
- [ ] `openapi/openapi.json` e regenerat și comis. Se pune un tag api nou, iar în `agridrone-web` se face `npm run api:sync`.

## Prompt de start

```
Implementezi pasul 11 din docs/dev-plan/11-results-api.md respectând docs/dev-plan/00-contracts.md.
Calculele spațiale (arii, diferențe) se fac în UTM (ST_Transform la SRID-ul UTM al parcelei).
La final regenerează openapi.json și listează endpoint-urile noi.
```
