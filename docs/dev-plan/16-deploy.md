# 16: Deploy cu Docker Compose pe un server Linux

| | |
|---|---|
| **Scop** | Aplicația (api + web) rulează pe un server Linux cu `docker compose`, cu HTTPS, backup și deploy reproductibil |
| **Repo** | `agridrone-api` (folderul `deploy/`); `agridrone-web` publică doar imaginea sa |
| **Depinde de** | 01 (Dockerfile api), 12 pasul 0 (imaginea web), 03 (autentificare). Un server de staging poate porni după 11, pentru demo |
| **Model AI** | Implementare: **mediu** · Review (securitate, backup): **mare** |
| **Durată** | 2–3 zile |

## Arhitectura pe server

```
Internet ─► Caddy :443 (TLS automat Let's Encrypt)
              ├── /            → web     (nginx, fișiere statice)
              ├── /api/*       → api     (FastAPI + tile-uri + fișiere prin URL-uri semnate)
              └── /uploads/*   → tusd    (upload reluabil al pozelor și video-urilor)
Rețea internă Docker (neexpusă): mysql · redis · worker (Celery) · nodeodm (profil `odm`)

Disc: /srv/agridrone/files     ← montat în api, worker și tusd (același sistem de fișiere)
      /srv/agridrone/mysql
```

- Web și API sunt pe **același domeniu**, așa că în producție nu e nevoie de CORS.
- Porturi publice: **numai 80 și 443**. SSH (22) e restricționat la IP-uri cunoscute sau prin VPN (ex. Tailscale).

## Server

| | Faza mock (fără ODM) | Cu ODM real (zboruri reale) |
|---|---|---|
| Arhitectură | x86_64 (imaginea NodeODM e doar amd64) | x86_64 |
| CPU / RAM | 4 vCPU / 8 GB | 8+ vCPU / 32 GB (≈ 300–500 poze per zbor) |
| Disc | 100 GB SSD | 1 TB+ SSD; ideal **2 discuri în RAID 1** (un zbor de 20 ha ≈ 3–5 GB brut + 1–2 GB rezultate) |
| OS | Ubuntu 24.04 LTS (sau Debian 12) | la fel |

- Docker Engine + pluginul `docker compose` (din repo-ul oficial Docker, nu pachetul vechi din distribuție).
- `unattended-upgrades` activ; firewall `ufw` cu 80/443 deschise și 22 restricționat.
- Un utilizator `deploy` fără sudo, membru al grupului `docker`. Fără login SSH cu parolă.

## Ce se construiește (`deploy/`)

1. **`deploy/compose.prod.yml`:**
   - imaginile vin din registry (GHCR), cu tag fix: `agridrone-api:${API_TAG}` (folosită de `api`, `worker` și `migrate`), `agridrone-web:${WEB_TAG}`;
   - `migrate`: serviciu one-shot (`alembic upgrade head`); `api` și `worker` pornesc numai după ce se termină cu succes (`depends_on: condition: service_completed_successfully`);
   - healthcheck pe fiecare serviciu și `restart: unless-stopped`;
   - bind mount-uri în `/srv/agridrone/` pentru fișiere și mysql (ușor de găsit și de salvat); volume denumite pentru redis și Caddy (certificatele);
   - `api`, `worker` și `tusd` rulează cu același UID/GID și montează `/srv/agridrone/files`;
   - `tusd` are hook-urile HTTP spre `http://api:8000/internal/tus-hooks` (rețea internă), iar Caddy blochează `/api/internal/*` din exterior;
   - rotația logurilor: driver `json-file` cu `max-size: 10m`, `max-file: 5`;
   - limite de memorie pentru `worker` și `nodeodm`, ca un job ODM să nu oprească baza de date.
2. **`deploy/Caddyfile`**, cu rutele de mai sus și headere de securitate (HSTS etc.). Pe `/uploads/*`, fără limită mică de body și cu timeout-uri lungi (upload-uri de pe internet mobil, la fermă).
3. **`deploy/.env.example`:** toate variabilele de producție, fără valori secrete. Pe server, `.env` are permisiuni `600` și nu intră niciodată în git.
4. **Imagini în CI (pe tag `vX.Y.Z`):**
   - api: build `linux/amd64`, push `ghcr.io/<org>/agridrone-api:vX.Y.Z`;
   - web: build static + nginx, push `ghcr.io/<org>/agridrone-web:vX.Y.Z`;
   - build-ul se face în CI, nu pe Mac-ul arm64, ca imaginea să fie sigur amd64.
5. **Deploy (`deploy/deploy.sh`, rulat de GitHub Actions prin SSH sau manual):**
   - setează `API_TAG` / `WEB_TAG` în `.env`;
   - `docker compose pull && docker compose up -d`;
   - așteaptă `GET /api/v1/healthz` = 200;
   - la eșec, revine la tag-urile anterioare (salvate în `.env.previous`).
   - Jobul de deploy în GitHub folosește un environment `production` cu aprobare manuală.
6. **Backup (`deploy/backup.sh`, cron zilnic):**
   - `mysqldump` comprimat (MySQL 8.4);
   - `restic` pe `/srv/agridrone/files` și pe dump-uri, către **altă mașină** prin SFTP (alt server, un NAS sau un disc extern). Nu e nevoie de S3; contează doar să nu fie același disc;
   - se pot exclude `_uploads/` și fișierele regenerabile (thumbnail-uri, HLS);
   - retenție 7 zilnice / 4 săptămânale / 6 lunare;
   - **restaurarea se testează** pe un server gol înainte de go-live, și apoi trimestrial (`docs/restore.md`).
7. **Monitorizare minimă:**
   - un check extern de uptime pe `/api/v1/healthz` (ex. Uptime Kuma pe alt host, sau un serviciu extern);
   - alertă la disc > 80% (`/api/v1/healthz` raportează și spațiul liber);
   - `smartd` pentru sănătatea discurilor și alertă la degradarea RAID-ului.

## Configurare de producție (adăugată în `00-contracts.md` §10)

- `AGRIDRONE_ENV=prod`: în prod, `dev-token` e **refuzat** și pornirea pică dacă lipsește un secret obligatoriu.
- `AGRIDRONE_PUBLIC_URL=https://<domeniu>`.
- `AGRIDRONE_STORAGE_DIR=/srv/agridrone/files` (calea din container).
- `AGRIDRONE_SECRET_KEY`: generat o dată (`openssl rand -hex 32`). Dacă se schimbă, URL-urile semnate vechi expiră imediat, ceea ce e acceptabil.
- `AGRIDRONE_TUS_URL=/uploads/`.

## Criterii de acceptanță

- [ ] Pe un server Ubuntu gol, `docs/deploy.md` duce de la zero la aplicația funcțională, cu HTTPS, în < 1 oră.
- [ ] `docker compose ps`: toate serviciile `healthy`; numai Caddy are porturi publice (verificat cu `ss -tlnp` și o scanare externă).
- [ ] Un deploy cu tag nou și un rollback la tag-ul vechi funcționează, cu downtime de cel mult câteva secunde.
- [ ] Un upload de 300 de poze din browser prin `/uploads/` merge, iar unul întrerupt (rețea oprită) se reia.
- [ ] `/api/internal/tus-hooks` nu e accesibil din exterior.
- [ ] Backup-ul rulează automat, iar o restaurare pe alt server a fost testată și documentată.
- [ ] Cu `AGRIDRONE_ENV=prod`, un request cu `dev-token` primește 401.

## Prompt de start

```
Ești inginer DevOps. Implementezi pasul 16 din docs/dev-plan/16-deploy.md respectând docs/dev-plan/00-contracts.md.
Țintă: un singur server Linux (Ubuntu 24.04, x86_64) cu docker compose; fără Kubernetes, fără Terraform.
Întâi propune compose.prod.yml + Caddyfile și lista de secrete; apoi scripturile de deploy și backup.
Nimic secret în git. Fiecare port expus trebuie justificat.
```

## Capcane

- **Autentificarea:** cât timp există doar `dev-token`, aplicația **nu se expune public**. Fie se adaugă login real (OIDC sau utilizator/parolă) înainte, fie serverul e accesibil numai prin VPN sau cu basic auth în Caddy.
- **Un singur disc = un singur punct de eșec.** Fără RAID și fără backup pe altă mașină, un disc mort înseamnă toate zborurile pierdute.
- **Mutarea din `_uploads/` în `raw/`** trebuie să fie pe același sistem de fișiere. Pe discuri diferite, `rename` devine copiere lentă și poate eșua la jumătate.
- **Hook-urile tus** sunt singura poartă de autorizare pentru upload. `pre-create` respinge tot ce nu are un `upload_token` valid.
- **Discul:** pozele brute și ortomozaicele umplu discul. Se stabilește o politică de retenție pentru `raw/` după procesare (ex. mutare în stocare rece după 90 de zile).
- **ODM pe același server** poate consuma toată memoria. Rulează cu limite, iar mai târziu poate trece pe un server separat (NodeODM e un API HTTP, deci se mută ușor).
