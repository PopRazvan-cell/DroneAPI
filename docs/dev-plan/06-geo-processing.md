# 06: Procesare geo (COG, CRS, decupare, analiză de teren)

| | |
|---|---|
| **Scop** | Bibliotecă geo reutilizabilă și corectă: toți pașii CV se bazează pe ea |
| **Depinde de** | 02 (date de test) |
| **Model AI** | Implementare: **mare** · Review: **mare** (bug-urile geo sunt tăcute) |
| **Durată** | 3–4 zile |

## Ce se construiește (`agridrone/geo/`)

| Modul | Funcții |
|---|---|
| `crs.py` | `utm_crs_for(geom_4326) -> CRS`, `to_utm(geom)`, `to_4326(geom, crs)`, `area_m2(geom_4326)` |
| `cog.py` | `to_cog(src, dst, kind: "rgb"\|"dem"\|"mask"\|"prob")`: compresie și overview-uri corecte per tip (`mask` → resampling `nearest`!) |
| `raster.py` | `open_aligned(paths)`: aduce rasterele pe aceeași grilă (CRS, rezoluție, extent); `read_window_tiles(path, tile=512, overlap=64)` ca iterator; `write_like(ref, arr, dst)` |
| `clip.py` | `clip_to_parcel(raster, parcel_geom_utm, inner_buffer_m=0)` → raster decupat + mască validă |
| `terrain.py` | `fill_depressions(dsm)`, `depth_in_sink(dsm)`, `slope(dsm)`, `flow_accumulation(dsm)`, `twi(dsm)` cu WhiteboxTools (pachetul `whitebox`); fallback numpy pentru teste mici |
| `vectorize.py` | `mask_to_polygons(mask, transform, classes, min_area_m2, simplify_m)` → GeoDataFrame UTM cu `area_m2` |
| `grid.py` | `make_grid(parcel_utm, cell_m)` → celule pătrate tăiate pe parcelă (pentru pasul 08) |
| `coregister.py` | `coregister(src_ortho, ref_ortho)`: ORB/AKAZE + RANSAC pe versiuni reduse → transformare afină aplicată; returnează și eroarea estimată (px și m) |

## Criterii de acceptanță

- [ ] `area_m2` pe un pătrat de 100 × 100 m generat în UTM și convertit în 4326 dă 10 000 ± 5 m².
- [ ] `to_cog` produce fișiere care trec `rio cogeo validate`.
- [ ] Măștile reduse în overview-uri păstrează valorile de clasă: niciun cod care nu există în original.
- [ ] `depth_in_sink` pe scena sintetică `water` găsește depresiunile generate (centrele lor sunt în zonele cu adâncime > 0).
- [ ] `vectorize` pe masca adevărată reproduce aria apei din `scene.json` cu ± 1%.
- [ ] `coregister`: o scenă deplasată artificial cu 2,5 m și rotită 1° e realiniată la < 0,2 m eroare.
- [ ] Teste hypothesis pentru `crs` (dus-întors 4326 → UTM → 4326 cu eroare < 1 mm).

## Prompt de start

```
Implementezi pasul 06 din docs/dev-plan/06-geo-processing.md respectând docs/dev-plan/00-contracts.md.
Ești expert GIS (rasterio, GDAL, pyproj, shapely 2, WhiteboxTools).
Fiecare funcție: semnătură tipată, docstring scurt, test pe date sintetice (preset `tiny` sau generate în fixture).
Atenție la: CRS, nodata, resampling nearest pentru măști, transform-ul după decupare.
```

## Capcane

- WhiteboxTools descarcă un binar la prima rulare. În Docker binarul se pune în imagine, ca să nu fie descărcat la runtime.
- DSM-ul din ODM are „găuri” (nodata) peste apă și peste zone uniforme. Se interpolează (`fillnodata`) înainte de analiza de teren.
