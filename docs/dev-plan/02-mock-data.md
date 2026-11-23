# 02: Date mock (generator sintetic + seturi publice + poze/video de test)

| | |
|---|---|
| **Scop** | Date de dezvoltare **cu adevăr cunoscut**, ca să putem măsura fiecare algoritm de la prima zi |
| **Depinde de** | 01 |
| **Model AI** | Implementare: **mare** (generatorul e algoritmic) · Download-uri și fixture-uri: **mic** · Review: **mare** |
| **Durată** | 3–5 zile |

## De ce un generator sintetic

Pozele găsite pe internet nu au măști. Generatorul produce simultan:

- ortomozaicul;
- DSM-ul;
- **masca adevărată** (apă, sol ud, vegetație, goluri).

Așa fiecare algoritm (pașii 07 și 08) are un test automat cu metrică: IoU și eroarea de arie. Datele reale vin ulterior, pentru validare.

## Partea A: generator sintetic (`agridrone/mock/synthetic/`)

### Comandă

```bash
agridrone mock generate --preset water --seed 42 --out data/synthetic/water_s42
agridrone mock generate --preset gaps_rows --seed 7 --out data/synthetic/gaps_rows_s7
agridrone mock generate --preset gaps_dense --seed 3 --out data/synthetic/gaps_dense_s3
agridrone mock generate --preset tiny --seed 1 --out tests/fixtures/tiny   # 512x512, pentru teste unitare
```

### Ieșiri per scenă

```
orthophoto.cog.tif     RGB uint8, CRS UTM 35N, georeferențiat lângă (44.55N, 27.10E)
dsm.cog.tif            float32 metri
dsm_dry.cog.tif        DSM de referință „uscat” (fără apă)
truth_mask.cog.tif     uint8, coduri din contracte §5 (apă=3, sol ud=4, vegetație=2, buruiană=5, sol=1)
truth_gaps.geojson     poligoanele golurilor (preseturile gaps_*)
parcel.geojson         poligonul parcelei (EPSG:4326), ușor neregulat
scene.json             parametri, seed, GSD, metrici adevărate (water_pct, gap_pct etc.)
preview.jpg            imagine redusă pentru verificare vizuală
```

### Preseturi

| Preset | Suprafață | GSD | Conținut |
|---|---|---|---|
| `water` | 300 × 200 m | 5 cm | Sol arat cu textură, 3–8 depresiuni în DSM, apă în cele mai adânci, inel de sol ud, câteva urme de roți, o umbră de copac |
| `gaps_rows` | 120 × 80 m | 2 cm | Rânduri de porumb la 70 cm, plante la ~20 cm, 5–15 goluri pe rânduri, buruieni între rânduri, o zonă băltită veche (gol mare) |
| `gaps_dense` | 150 × 100 m | 3 cm | Cereală deasă (textură verde continuă), 5–10 petice rare sau goale, variație de nuanță |
| `tiny` | 512 × 512 px | 5 cm | Toate clasele, pentru teste unitare rapide |

### Algoritm (indicativ; asistentul AI propune detaliile)

1. **DSM:**
   - plan înclinat ușor;
   - zgomot fractal (sumă de octave Perlin/simplex sau zgomot gaussian filtrat la mai multe scări);
   - depresiuni gaussiene negative cu adâncimi de 3–25 cm.
2. **Apa:**
   - umple depresiunile până la un nivel (water level per depresiune) → `water = dsm < level`;
   - sol ud = inel de 0,3–1,5 m în jurul apei (dilatare) + pixeli cu `dsm < level + 2 cm`.
3. **Textura solului:**
   - culoare de bază brun (variații în spațiul Lab);
   - brazde / urme de arătură (sinusoidă pe o direcție);
   - zgomot de granulație.
4. **Vegetația:**
   - rânduri pe o direcție aleatoare;
   - plante = blob-uri verzi (elipse cu variație de nuanță), cu mică variație de poziție față de rând;
   - golurile = segmente de rând fără plante;
   - buruieni = blob-uri aleatoare între rânduri.
5. **Apa în RGB:** amestec între albastru-cer, gri închis și maro tulbure (aleator per zonă), plus un mic gradient de reflexie și margini „moi”.
6. **Umbre:** poligon întunecat (multiplicare 0,5–0,7) cu margine blurată. **Nu** schimbă clasa din masca adevărată. Rolul lor e să testeze robustețea.
7. **Lumină globală:** variație de temperatură de culoare și luminozitate între scene (parametru `--lighting`).
8. **Georeferențiere:** transformare afină în UTM 35N; poligonul parcelei în interior, cu buffer de 10 m.

> Generatorul trebuie să fie **determinist** pentru un seed dat. Testul verifică un hash al măștii.

### Mock de „zbor”: poze individuale cu EXIF GPS

```bash
agridrone mock photos --scene data/synthetic/water_s42 --altitude 80 --overlap 0.75 0.70 --out data/synthetic/water_s42/photos
```

- Taie ortomozaicul în „poze” 4000×3000 (redimensionate la GSD-ul altitudinii) pe un grid de zbor. Gridul se poate lua din pasul 14 când e gata; până atunci, un grid simplu.
- Scrie EXIF cu `piexif`:
  - `GPSLatitude`, `GPSLongitude`, `GPSAltitude`;
  - `DateTimeOriginal` (crescător, la 2 s);
  - `Make=DJI`, `Model=FC7303` (identificatorul de cameră al Mini 2), focala 4,49 mm.
- **Scop:** testează ingestia (pasul 04), nu fotogrametria. ODM nu va reconstrui bine din tăieturi plane, iar asta e acceptabil.

## Partea B: seturi publice (`agridrone/mock/public/`)

Scripturile de download descarcă în `data/public/<nume>/` și scriu un `MANIFEST.json` (sursă, licență, data descărcării, sha256).

| Set | Ce conține | La ce ne folosește | De verificat |
|---|---|---|---|
| **OpenDroneMap sample datasets** (repo-urile `OpenDroneMap/odm_data_*` pe GitHub, ex. `odm_data_aukerman`; catalog pe odmdata.com) | Poze reale de dronă cu EXIF GPS | Test real al ingestiei și al fotogrametriei (pasul 05) | Licența fiecărui set |
| **Agriculture-Vision** (CVPR 2020, Univ. Illinois) | Tile-uri aeriene RGB+NIR de terenuri agricole, cu etichete inclusiv `water`, `planter_skip`, `weed_cluster` | Pre-antrenare / validare pentru apă și goluri (pasul 09) | Licență (de regulă doar cercetare); cerere de acces |
| **DroneDeploy Segmentation Benchmark** (`dronedeploy/dd-ml-segmentation-benchmark`) | Ortomozaice de dronă + elevație + etichete (inclusiv `water`, `vegetation`, `ground`) | Test pentru apă cu DSM real; antrenare | Licență, dimensiune download |
| **Seturi crop/weed** (ex. WeedMap, CropAndWeed) | Imagini de culturi pe rânduri cu buruieni | Clasa `weed`, detecția rândurilor | Licență, rezoluție |

> Asistentul AI **verifică pe web** linkurile, dimensiunile și licențele la momentul implementării și le notează în `MANIFEST.json`. Nu presupune.

## Partea C: poze și video găsite de noi (`data/samples/`)

- **Video-uri:** clipuri de dronă peste câmpuri, de pe site-uri cu licență liberă (ex. Pexels, Pixabay). Se notează sursa și licența în `data/samples/SOURCES.md`.
- **Poze de la sol cu bălți și goluri:** pentru galerie și pentru ground truth fictiv în UI.
- **Poze proprii:** dacă există poze făcute cu telefonul pe câmp, se pun aici. Au EXIF GPS, deci sunt utile la testul de ingestie.
- **Seed DB:** `agridrone mock seed-db` creează o organizație, o fermă și 3 parcele (din `parcel.geojson` ale scenelor sintetice), plus 2–3 „zboruri” istorice cu date diferite. Așa dashboard-ul are evoluție în timp.

## Criterii de acceptanță

- [ ] Cele 4 preseturi se generează. `water` rulează în < 60 s pe un laptop.
- [ ] Același seed produce aceeași mască (testul compară hash-ul).
- [ ] Rasterele se deschid corect în QGIS, în poziția așteptată (verificare manuală o dată, cu captură în PR).
- [ ] `scene.json` conține metricile adevărate. Testul verifică dacă `water_pct` din json corespunde măștii.
- [ ] `agridrone mock photos` produce poze cu EXIF GPS valid (citit înapoi cu `exiftool` sau `piexif`).
- [ ] Scripturile de download funcționează sau dau un mesaj clar dacă setul cere acces manual.

## Prompt de start (generator)

```
Implementezi Partea A din docs/dev-plan/02-mock-data.md respectând docs/dev-plan/00-contracts.md.
Obiectiv: scene sintetice realiste vizual, deterministe, cu mască adevărată.
1) Propune designul (module, funcții, cum generezi DSM, apă, rânduri, textură) și cum testezi.
2) După confirmare implementează cu numpy/scipy/opencv/rasterio (fără dependențe grele noi).
3) Generează preview.jpg pentru fiecare preset și arată-mi-le.
4) Scrie teste pytest pe presetul `tiny`.
```

## Capcane

- Nu genera rastere uriașe în teste: `tiny` e pentru teste, celelalte doar pentru demo.
- Apa trebuie să fie **coerentă cu DSM-ul** (stă în depresiuni). Altfel algoritmii din 07 care folosesc terenul nu pot fi testați.
- Variația vizuală (lumină, nuanțe, umbre) e esențială. Altfel baseline-ul pare perfect pe sintetic și cade pe date reale.
