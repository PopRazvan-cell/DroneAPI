# 09: ML, modele de segmentare (antrenare, export ONNX, integrare)

| | |
|---|---|
| **Scop** | Modele care depășesc baseline-urile clasice și generalizează pe date reale |
| **Depinde de** | 02 (date), 07 și 08 (eval + baseline de comparat) |
| **Model AI** | Design și debugging antrenare: **mare** (eventual cel mai mare disponibil) · Scripturi de date și configuri: **mediu** · Review: **mare** |
| **Durată** | 2–3 săptămâni (în mare parte rulări) |

## Strategie de date (fără dronă)

| Sursă | Rol |
|---|---|
| Sintetic (02A), mii de tile-uri | Pre-antrenare, teste de pipeline, sanity checks |
| DroneDeploy benchmark (02B) | Antrenare și validare `water` / `vegetation` / `soil` pe dronă reală, cu elevație |
| Agriculture-Vision (02B) | `water`, `planter_skip` (≈ gol), `weed_cluster`. Atenție: e imagine aeriană, cu altă rezoluție. Se folosește la pre-antrenare sau pentru validare de domeniu |
| Date proprii (mai târziu) | Fine-tuning final; setul de test „adevărat” |

> **Split pe scene sau ortomozaice, niciodată pe tile-uri aleatoare.** Altfel apar scurgeri între antrenare și test, iar metricile sunt false.

## Ce se construiește (`ml/`, proiect uv separat)

1. **`ml/data/`:**
   - convertoare din fiecare set în formatul comun: tile-uri 512×512 PNG/NPY, cu mască în codurile §5 și `255 = ignore` pentru clasele inexistente în setul respectiv;
   - `manifest.parquet` cu sursă, scenă, split, GSD și clasele prezente.
2. **`ml/train.py`:**
   - PyTorch Lightning + `segmentation-models-pytorch`;
   - configurare cu Hydra (`ml/configs/`).
   - **Modele de comparat:**
     - `Unet(resnet34)`: baseline ML;
     - `DeepLabV3Plus(efficientnet-b3)`;
     - `Segformer` (mit-b2, din smp sau Hugging Face).
   - **Intrări:** RGB (3 canale) sau RGB + `depth_in_sink` + `slope` (5 canale) pentru apă. Primul strat se adaptează.
   - **Loss:** `Dice + CE` (ignore_index=255); opțional Focal.
   - **Augmentări** (albumentations): flip/rot90, scale 0,75–1,25, color jitter, gamma, blur, umbre sintetice.
3. **`ml/eval.py`:** reutilizează `agridrone.cv.eval` (aceleași metrici ca baseline-ul). Raport pe fiecare set și pe sintetic.
4. **Tracking cu MLflow** (container local sau fișier `mlruns/`): parametri, metrici, imagini de validare.
5. **`ml/export.py`:**
   - export ONNX (opset ≥ 17, axe dinamice H/W);
   - verificare numerică PyTorch vs ONNX (diferență maximă < 1e-3);
   - `model_card.json`: clase, canale, normalizare, metrici, date de antrenare.
6. **Integrare în backend:** `agridrone/cv/water/ml.py` și `agridrone/cv/gaps/ml.py` implementează `Analyzer`:
   - inferență pe tile-uri cu overlap și îmbinare ponderată (fereastră Hann);
   - ONNX Runtime pe CPU;
   - modelul se citește din stocare (`models/{name}/{version}/model.onnx`, contracte §8).
7. **Compute:**
   - local: Mac cu MPS, pentru experimente mici;
   - serios: GPU cloud la oră (instanțe spot), cu scripturile pregătite să ruleze în container.

## Criterii de acceptanță

- [ ] Pipeline-ul de date produce tile-uri corecte (vizualizare a 20 de exemple aleatoare cu masca suprapusă, inclusă în PR).
- [ ] Un model antrenat doar pe sintetic depășește baseline-ul pe testul sintetic. Pe datele reale se raportează rezultatul, chiar dacă e slab: asta măsoară decalajul de domeniu.
- [ ] Modelul antrenat pe DroneDeploy (+ sintetic) are IoU(water) pe testul DroneDeploy mai mare decât baseline-ul clasic (din pasul 07) pe același test.
- [ ] ONNX-ul exportat rulează în backend prin `agridrone analyze water --analyzer ml --model <path>` și dă aceleași metrici ca în `ml/eval.py`, cu ± 0,01.
- [ ] `model_card.json` complet. Rezultatele sunt în MLflow.

## Prompt de start

```
Ești ML engineer senior (segmentare semantică, teledetecție). Implementezi pasul 09 din docs/dev-plan/09-ml-training.md,
respectând docs/dev-plan/00-contracts.md (clase §5, interfața Analyzer §6).
Pas 1: convertoarele de date + manifest + vizualizare; arată-mi exemplele înainte de antrenare.
Pas 2: antrenare U-Net baseline pe sintetic, apoi pe DroneDeploy. Pas 3: comparație modele. Pas 4: export ONNX + integrare.
Verifică pe web licențele seturilor și notează-le în manifest. Raportează onest unde modelul e slab.
```

## Capcane

- Clase diferite în seturi diferite: se folosește `ignore` (255) pentru ce setul nu etichetează. Nu se presupune „soil” acolo unde lipsește eticheta.
- GSD diferit între seturi: se resamplează la un GSD țintă (ex. 5 cm pentru apă) sau se adaugă augmentare de scară.
