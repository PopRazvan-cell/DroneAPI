# 04: Stocare + ingestie media (upload, EXIF, asociere cu zborul)

| | |
|---|---|
| **Scop** | Poze și video ajung pe discul serverului, validate, deduplicate și legate de zbor și parcelă |
| **Depinde de** | 03 |
| **Model AI** | Implementare: **mediu** · Review: **mare** |
| **Durată** | 3–4 zile |

## Ce se construiește

1. **`agridrone/storage/`:**
   - interfața `FileStore` cu metodele `path(key)`, `open`, `write_atomic`, `exists`, `move`, `list`, `delete`, `usage()`;
   - o singură implementare, `LocalFileStore`, peste `AGRIDRONE_STORAGE_DIR`;
   - protecție la path traversal: orice cheie se normalizează și trebuie să rămână sub rădăcină (test cu `../`);
   - `signed_url(key, ttl)` și verificarea semnăturii (contracte §9);
   - `GET /api/v1/files/...`: servește fișierul cu `FileResponse`, cu suport `Range`, `ETag` și cache.
2. **Upload reluabil cu tus** (pozele nu trec prin API, merg direct în `tusd`):
   - `POST /flights/{id}/upload-session` → `{tus_endpoint, upload_token, max_file_size}`;
   - clientul (Uppy în web, sau CLI-ul) trimite fiecare fișier la `tusd`, cu metadatele `flight_id`, `filename`, `upload_token`;
   - **hook `pre-create`** (`POST /internal/tus-hooks`, accesibil numai din rețeaua Docker): verifică token-ul, zborul, organizația, tipul și dimensiunea; respinge altfel;
   - **hook `post-finish`**: mută fișierul din `_uploads/` în `raw/` sau `video/` (rename, §8), creează `media_asset` și pornește task-ul de ingestie;
   - o curățare periodică șterge upload-urile neterminate mai vechi de 48 h.
3. **Ingestie** (`agridrone/ingest/`). Funcții pure, testate fără DB:
   - EXIF cu `piexif` / `exifread`: GPS, altitudine, timp, cameră; pentru video, metadate prin `ffprobe`;
   - `sha256` → deduplicare (`media_asset.sha256` unic per zbor);
   - scor de claritate (varianța Laplacianului) → `quality_score`, plus flag `blurry` sub prag;
   - verificare dacă GPS-ul e în parcelă (cu buffer de 50 m) → avertizare pentru pozele din afară;
   - **sumar de captură:** număr de poze, interval de timp, altitudine medie, acoperire estimată (convex hull al punctelor față de parcelă), poze respinse și de ce.
4. **Fallback fără browser:** comanda `agridrone ingest folder <path> --flight <id>` urcă un folder local. E utilă pentru datele mock și pentru cardul SD.
5. **Thumbnail-uri** (512 px) pentru galerie, generate la ingestie.
6. **Endpoint-uri:**
   - `GET /flights/{id}/media` (cu filtre `type`, `bbox`, paginare);
   - `GET /media/{id}` (metadate + URL semnat pentru fișier și thumbnail);
   - `GET /flights/{id}/capture-summary`.

## Criterii de acceptanță

- [ ] `agridrone ingest folder data/synthetic/water_s42/photos --flight <id>` urcă toate pozele, cu EXIF citit corect.
- [ ] Re-upload-ul acelorași fișiere nu creează duplicate.
- [ ] O poză fără GPS e acceptată cu avertizare. Un fișier care nu e imagine sau video e respins cu un motiv clar.
- [ ] Merge și pe un set ODM public din pasul 02, partea B (poze reale de dronă).
- [ ] Teste unitare pentru EXIF, claritate și asociere, pe fixture-uri mici.
- [ ] Un upload tus întrerupt la jumătate se reia de unde a rămas.
- [ ] Un URL semnat expirat sau modificat primește 403. O cheie cu `../` e respinsă.

## Prompt de start

```
Implementezi pasul 04 din docs/dev-plan/04-ingest-storage.md respectând docs/dev-plan/00-contracts.md.
Separă strict logica pură (agridrone/ingest, testabilă fără DB și fără disc real) de API și persistență.
Stocarea e numai pe disc local (FileStore), upload-urile prin tusd cu hook-uri HTTP. Fără S3.
Folosește pozele generate de `agridrone mock photos` ca fixture de integrare.
```

## Capcane

- Pozele DJI pot avea altitudinea relativă în XMP (`drone-dji:RelativeAltitude`), nu doar în EXIF. Se citește XMP dacă există.
- Ora din EXIF e locală, fără fus orar. Se stochează cu fusul configurat al organizației (implicit `Europe/Bucharest`).
