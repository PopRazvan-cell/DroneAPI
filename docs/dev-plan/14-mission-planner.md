# 14: Planificator de misiuni (geometrie pură, fără dronă)

| | |
|---|---|
| **Scop** | Din poligonul parcelei și parametri → linii de zbor, puncte foto, estimări, export |
| **Depinde de** | 03 (parcele); 06 (`geo.crs`) |
| **Model AI** | Implementare: **mare** · Review: **mare** · Teste hypothesis: **mediu** |
| **Durată** | 3–5 zile |

> Nu are nevoie de dronă. Exportul KML / CSV (Litchi) se poate folosi manual la primele zboruri reale. La integrarea cu drona (planul general, secțiunea 6), aceeași misiune JSON va fi trimisă aplicației Companion.

## Ce se construiește (`agridrone/mission/`)

1. **`camera.py`:** profilul camerei: Mini 2, senzor ≈ 6,17 × 4,55 mm, focală 4,49 mm, 4000 × 3000 px, interval minim foto 2 s.
   - `gsd_cm(alt)`;
   - `footprint_m(alt)`;
   - `alt_for_gsd(gsd)`.
2. **`grid.py`** (`plan_grid(parcel_4326, params) -> Mission`):
   - parcela → UTM;
   - direcția = latura cea mai lungă a dreptunghiului minim rotit (sau unghi dat);
   - distanța dintre linii = `footprint_across × (1 − side_overlap)`;
   - liniile se extind cu `buffer_m` peste parcelă și se taie pe poligonul cu buffer; pe poligoane concave apar mai multe segmente;
   - ordonare în serpentină (boustrophedon), cu tranziții minime;
   - puncte foto la `footprint_along × (1 − front_overlap)`;
   - viteza = min(`max_speed`, distanța dintre poze / interval).
3. **`estimate.py`:**
   - lungimea traseului, timpul (cu viraje: penalitate fixă per viraj), numărul de poze;
   - **împărțirea pe baterii:** `usable_flight_min` (implicit 18), cu rezervă pentru drumul dus-întors la Home; fiecare baterie primește un punct de reluare.
4. **`export.py`:**
   - JSON (formatul intern, versionat, pentru Companion App mai târziu);
   - KML (linii + puncte);
   - CSV compatibil Litchi: formatul de coloane se verifică pe documentația Litchi la implementare.
5. **API:**
   - `POST /missions/plan` (previzualizare, nu se salvează);
   - `POST /missions`;
   - `GET /missions/{id}`;
   - `GET /missions/{id}/export?format=json|kml|litchi_csv`.
6. **Opțional:** altitudine ajustată după un DEM public (terrain follow aproximativ). Mini 2 zboară relativ la punctul de decolare.

## Criterii de acceptanță

- [ ] Teste hypothesis pe poligoane aleatoare (convexe și concave):
  - fiecare punct al parcelei e acoperit de cel puțin o amprentă de poză (verificat pe eșantion);
  - distanța dintre linii adiacente = valoarea calculată, cu ± 1 cm;
  - niciun punct foto nu e în afara poligonului extins cu buffer.
- [ ] Pentru 20 ha la 80 m (75/70): estimările sunt în intervalul din planul general (~12–15 ha per baterie). Diferențele se explică.
- [ ] KML-ul se deschide corect în Google Earth / QGIS.
- [ ] Simularea „poze din plan” (pasul 02, `mock photos --plan <mission.json>`) folosește punctele reale ale misiunii.

## Prompt de start

```
Ești expert în geometrie computațională și GIS. Implementezi pasul 14 din docs/dev-plan/14-mission-planner.md
respectând docs/dev-plan/00-contracts.md (calcule în UTM!). Bibliotecă pură, fără DB, cu teste hypothesis.
Propune întâi algoritmul pentru poligoane concave (segmente multiple pe aceeași linie) și ordonarea traseului.
```
