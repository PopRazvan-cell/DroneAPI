# 07: CV A, detecția zonelor cu apă (baseline clasic)

| | |
|---|---|
| **Scop** | Primul analizor funcțional: unde e apă, ce % din parcelă, câte zone |
| **Depinde de** | 02, 06 |
| **Model AI** | Implementare: **mare** · Review: **mare** · Experimente de parametri și notebook: **mediu** |
| **Durată** | 4–6 zile |

## Ce se construiește (`agridrone/cv/water/baseline.py`)

Clasa `WaterBaselineAnalyzer` implementează `Analyzer` din contracte §6. Pașii pipeline-ului:

1. **Pregătire:** decupare pe parcelă (`geo.clip`), normalizare de lumină (gray-world sau CLAHE pe L din Lab), opțional pe tile-uri.
2. **Caracteristici per pixel:**
   - `V`, `S` (HSV), `L`, `a`, `b` (Lab);
   - `ExG = 2g − r − b` (pe cromaticitate normalizată), `VARI`;
   - textură: `local_std(gray, 7)`;
   - opțional, entropie locală.
3. **Candidați spectrali:**
   - praguri adaptive per scenă (Otsu sau percentile) pe întunecime, saturație și netezime, cu `ExG < 0`;
   - toate pragurile sunt în `params`, cu valori implicite documentate.
4. **Prior de teren** (dacă există DSM):
   - `depth_in_sink > d_min` sau `TWI > t_min`;
   - candidații se păstrează doar dacă ating o zonă de prior dilatată cu `prior_dilate_m`.
5. **Sol ud:** pixeli întunecați, nesaturați, adiacenți apei, dar cu textură → clasa `wet_soil`.
6. **Post-procesare:** open/close, `remove_small_objects(min_area_m2)`, umplerea găurilor mici.
7. **Ieșiri:**
   - masca (coduri §5);
   - poligoane (`geo.vectorize`);
   - statisticile din §7: `water_pct`, `water_area_m2`, `water_zones`, `water_max_zone_m2`, `wet_soil_pct`;
   - `debug/`: hărțile intermediare (candidați, prior, final) ca PNG.

### CLI

```bash
agridrone analyze water --ortho data/synthetic/water_s42/orthophoto.cog.tif \
  --dsm data/synthetic/water_s42/dsm.cog.tif --parcel data/synthetic/water_s42/parcel.geojson \
  --out data/work/water_s42 [--params params.yaml]
```

### Evaluare (`agridrone/cv/eval.py`, reutilizat la pasul 08)

```bash
agridrone eval --pred data/work/water_s42/mask.cog.tif --truth data/synthetic/water_s42/truth_mask.cog.tif
```

- Raportează IoU per clasă, precizie, recall, eroarea relativă de arie pentru `water` și matricea de confuzie.
- Scrie `eval.json` și un PNG cu suprapunerea erorilor: FP roșu, FN albastru.

### Benchmark

`agridrone bench water --seeds 1..20` generează 20 de scene, rulează analizorul, evaluează și raportează media și deviația. **Ăsta e testul de regresie** pentru orice modificare.

## Criterii de acceptanță

- [ ] Pe benchmark-ul sintetic (20 de seed-uri), cu DSM: **IoU(water) ≥ 0,80**, eroare de arie ≤ 10%.
- [ ] Fără DSM (doar RGB): rulează și raportează. Ținta e mai mică (≥ 0,60) și e documentată.
- [ ] Umbrele sintetice nu sunt detectate ca apă în mai mult de 20% din aria lor.
- [ ] Rulează pe un ortomozaic real din 02B (DroneDeploy, care are apă și elevație). Rezultatul e evaluat vizual și, unde există etichete, cu IoU.
- [ ] Timp: < 30 s pentru scena `water` (300 × 200 m, 5 cm) pe laptop.

## Prompt de start

```
Ești expert în computer vision și teledetecție. Implementezi pasul 07 din
docs/dev-plan/07-cv-water-baseline.md, respectând docs/dev-plan/00-contracts.md (interfața Analyzer §6, clase §5, metrici §7).
Folosește doar numpy/opencv/scikit-image și agridrone.geo.
1) Propune pipeline-ul și pragurile implicite, explicând de ce.
2) Implementează analizorul + `agridrone/cv/eval.py` + CLI.
3) Rulează benchmark-ul pe 20 de seed-uri și raportează metricile. Iterează până la criteriile de acceptanță,
   dar NU supraantrena pe sintetic: orice prag nou trebuie să aibă o justificare fizică.
```

## Capcane

- Dacă baseline-ul ajunge la IoU 0,99 pe sintetic, **datele sintetice sunt prea ușoare**. Se revine la pasul 02 și se adaugă variație.
- Reflexiile cerului fac apa luminoasă și albastră. Pragul doar pe „întunecat” nu e suficient, de aceea textura și prior-ul de teren sunt esențiale.
