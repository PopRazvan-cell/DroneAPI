# 08: CV B, golurile din cultură (baseline clasic)

| | |
|---|---|
| **Scop** | Unde nu s-a dezvoltat cultura și ce % din parcelă reprezintă |
| **Depinde de** | 02, 06 (și `cv/eval.py` din 07; dacă 07 nu e gata, se scrie aici și se mută) |
| **Model AI** | Implementare: **mare** · Review: **mare** |
| **Durată** | 4–6 zile |

## Ce se construiește (`agridrone/cv/gaps/`)

### Comun: masca de vegetație (`vegetation.py`)

- Indice `ExG − ExR` (sau `ExG`) + prag Otsu (`params.veg_method`).
- Normalizare de lumină. Umbrele se tratează cu un prag adaptiv local.
- Ieșire: masca binară de vegetație și `veg_cover_pct`.

### Modul 1: culturi pe rânduri (`rows.py`), `params.mode = "rows"`

1. **Direcția rândurilor:** FFT 2D pe masca de vegetație (vârful dominant) sau Hough pe skeleton. Ieșiri: unghiul și distanța medie dintre rânduri (comparată cu `row_spacing_m` din `season_crop`, dacă există).
2. **Liniile rândurilor:** proiecție perpendiculară pe direcție, maxime locale → centrele rândurilor → linii (LineString UTM) tăiate pe parcelă.
3. **Profil pe rând:** se eșantionează masca într-o bandă de ± 10 cm în jurul fiecărei linii. Rezultatul e un semnal 1D de vegetație.
4. **Goluri:** segmente fără vegetație mai lungi de `min_gap_m` (implicit 0,5 m) → `gap` segments.
5. **Agregare:** segmentele vecine (pe rânduri adiacente, distanță < `merge_m`) se unesc în poligoane `gap` prin buffer + union.
6. **Buruieni:** vegetație în afara benzilor de rând → clasa `weed` + `weed_pct`.
7. **Opțional:** `plants_per_ha` din componentele conexe pe rânduri (aproximare).

### Modul 2: culturi dese (`dense.py`), `params.mode = "dense"`

1. Grila `geo.make_grid(cell_m=2)`.
2. Acoperirea per celulă = % pixeli de vegetație.
3. Celula e „gol” dacă `cover < abs_thr` sau `cover < rel_thr × mediana parcelei`.
4. Celulele gol adiacente → poligoane; se filtrează după `min_area_m2`.

### Mod automat

`params.mode = "auto"` alege `rows` dacă FFT-ul are un vârf clar (raport semnal/zgomot peste prag), altfel `dense`.

### Ieșiri

- Masca: `vegetation` / `soil` / `weed` + stratul `gap` (cod 6) peste.
- Poligoane `gap` și `weed`.
- Statistici: `gap_pct`, `gap_area_m2`, `gap_zones`, `gap_max_zone_m2`, `veg_cover_pct`, `weed_pct`, `rows_detected`.
- Atribute de corelare pe fiecare poligon (dacă există date): `overlaps_water_history`, `mean_depth_in_sink`, `distance_to_edge_m`.

### CLI și benchmark

```bash
agridrone analyze gaps --ortho ... --parcel ... --mode auto --out ...
agridrone bench gaps --preset gaps_rows --seeds 1..20
agridrone bench gaps --preset gaps_dense --seeds 1..20
```

## Criterii de acceptanță

- [ ] `gaps_rows`: unghiul rândurilor e estimat cu ± 1°, iar distanța dintre rânduri cu ± 5%.
- [ ] `gaps_rows`: recall ≥ 0,85 pe golurile adevărate de peste 1 m, eroarea `gap_pct` ≤ 15% relativ.
- [ ] `gaps_dense`: IoU(gap) ≥ 0,70, comparat pe grilă.
- [ ] Buruienile dintre rânduri nu „astupă” golurile (test dedicat: gol + buruiană în apropiere).
- [ ] Modul `auto` alege corect pe ambele preseturi.

## Prompt de start

```
Ești expert în computer vision pentru agricultură de precizie. Implementezi pasul 08 din
docs/dev-plan/08-cv-gaps-baseline.md, respectând docs/dev-plan/00-contracts.md.
Ordinea: vegetation.py → dense.py (mai simplu) → rows.py → auto.
Pentru fiecare modul: teste pe sintetic + benchmark. Propune întâi algoritmul pentru detecția rândurilor (FFT vs Hough) cu argumente.
```

## Capcane

- La GSD peste 3 cm, plantele mici (BBCH 12) au 2–4 pixeli. Detecția pe rânduri devine nesigură, așa că modulul trebuie să raporteze o încredere scăzută, nu rezultate false sigure.
- Rândurile curbe (la capătul parcelei) se exclud cu un buffer intern sau se tratează pe segmente.
