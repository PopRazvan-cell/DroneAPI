# 13: Media, galerie de poze și video

| | |
|---|---|
| **Scop** | Pozele și video-urile zborurilor, vizibile în dashboard și legate de hartă |
| **Depinde de** | 04 |
| **Model AI** | Implementare: **mediu** · Review: **mediu** |
| **Durată** | 3–4 zile |

## Ce se construiește

1. **Transcodare video** (task Celery, coada `cpu`, cu `ffmpeg`):
   - HLS cu 2 trepte (1080p și 540p), segmente de 4 s;
   - poster (frame la 10%);
   - durată, rezoluție și codec în `media_asset`.
2. **Traseu video (opțional):** dacă video-ul are fișierul `.SRT` DJI cu coordonate, se parsează într-un LineString cu timp. Asta permite sincronizarea „poziție pe hartă ↔ moment din video”. Dacă SRT-ul lipsește, video-ul se leagă doar de zbor.
3. **Extragere de cadre:** `POST /media/{id}/frames?every_s=5` → JPEG-uri pentru inspecție sau etichetare.
4. **Galerie:**
   - `GET /flights/{id}/media?type=photo&bbox=` cu thumbnail-uri;
   - `GET /media/{id}/stream.m3u8`: playlist-ul și segmentele se servesc prin URL-uri semnate (contracte §9), de pe disc.
5. **Blurare persoane (opțional, GDPR):** detecție de persoane (model mic, ex. YOLO-n ONNX) pe poze înainte de afișarea în galerie; originalul rămâne privat.

## Date mock

- Video-urile din `data/samples/` (pasul 02C), cu sursa și licența notate.
- Un `.SRT` fals generat pentru un video, ca să fie testat parserul.

## Criterii de acceptanță

- [ ] Un MP4 de test ajunge HLS și rulează în frontend (hls.js), cu poster.
- [ ] Parserul SRT are test pe un fișier fals și pe un fragment real, dacă găsim unul.
- [ ] Galeria cu 300 de poze se încarcă fluent (paginare și thumbnail-uri).

## Prompt de start

```
Implementezi pasul 13 din docs/dev-plan/13-media-video.md respectând docs/dev-plan/00-contracts.md.
ffmpeg rulează în containerul worker; nu folosi servicii externe de transcodare.
```
