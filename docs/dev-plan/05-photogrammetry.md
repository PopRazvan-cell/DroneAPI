# 05: Fotogrametrie (mod mock + NodeODM real)

| | |
|---|---|
| **Scop** | Dintr-un zbor ingerat obținem ortomozaic + DSM + DTM ca COG |
| **Depinde de** | 04 |
| **Model AI** | Implementare: **mediu** · Review: **mare** |
| **Durată** | 2–4 zile |

## Ce se construiește

1. **Interfața comună:**
   ```python
   class PhotogrammetryEngine(Protocol):
       def process(self, flight_id: UUID, image_paths: list[Path], gcp_file: Path | None,
                   options: OdmOptions, out_dir: Path) -> PhotogrammetryResult: ...
   # PhotogrammetryResult: ortho_path, dsm_path, dtm_path | None, gsd_cm, crs, footprint (Polygon), report (dict)
   ```
2. **`MockEngine`** (`AGRIDRONE_PHOTOGRAMMETRY_MODE=mock`):
   - nu rulează ODM;
   - caută scena sintetică asociată zborului (`flight.notes` sau tabel de mapare) și copiază `orthophoto.cog.tif` și `dsm.cog.tif`;
   - produce rezultatul în secunde.
   - **Ăsta e modul implicit în dezvoltare.**
3. **`NodeOdmEngine`** (PyODM):
   - creează task-ul, urcă pozele și urmărește progresul (callback → Redis);
   - descarcă `odm_orthophoto.tif`, `dsm.tif`, `dtm.tif` și raportul;
   - opțiuni implicite:
     ```
     --dsm --dtm --orthophoto-resolution <gsd> --feature-quality high --pc-quality medium
     --rolling-shutter (când camera e Mini 2)
     --gcp (când există)
     ```
   - preset rapid: `--fast-orthophoto` pentru previzualizare.
4. **Conversia COG** se face în pasul 06 (`geo.cog.to_cog`). Aici doar se apelează.
5. **Raport de calitate:** GSD real, număr de poze folosite, RMSE pe GCP (dacă există), timp de procesare.

## Criterii de acceptanță

- [ ] Mod mock: zborul sintetic produce ortomozaic și DSM pe disc, la cheile din contracte §8, în mai puțin de 10 s.
- [ ] Mod NodeODM: setul public `odm_data_aukerman` (sau altul mic din 02B) se procesează complet și rezultatul se deschide în QGIS.
- [ ] Erorile ODM (ex. prea puține poze) apar ca status `failed` cu mesaj util, nu ca excepție netratată.

## Prompt de start

```
Implementezi pasul 05 din docs/dev-plan/05-photogrammetry.md respectând docs/dev-plan/00-contracts.md.
Întâi MockEngine + testele lui, apoi NodeOdmEngine cu PyODM.
NodeODM rulează în docker-compose profilul `odm` (imagine amd64; pe Mac arm64 e emulat și lent; e ok pentru un set mic).
```

## Capcane

- NodeODM pe Mac arm64 e foarte lent prin emulare. Pentru seturi mai mari folosește un VM Linux x86 sau procesează noaptea.
- Ortomozaicul ODM vine în UTM-ul detectat automat. Se verifică faptul că e același cu `utm_crs_for(parcel)`; dacă nu, se reproiectează.
