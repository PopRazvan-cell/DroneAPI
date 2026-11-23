# agridrone-api

Backend Python pentru AgriDrone CV: detecția zonelor cu băltire și a golurilor din culturi, din imagini de dronă. Frontend-ul e în repo-ul separat `agridrone-web`.

- Contracte obligatorii (structură, CRS, coduri de clase, interfețe, contractul cu web-ul): [docs/dev-plan/00-contracts.md](docs/dev-plan/00-contracts.md)
- Planul de implementare pe faze A0–A8 (DoD + teste de gate): [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)
- Planul pe pași: [docs/dev-plan/00-README.md](docs/dev-plan/00-README.md)
- Planul general al proiectului: [docs/Plan_Proiect_AgriDrone.pdf](docs/Plan_Proiect_AgriDrone.pdf). Structura de repo din PDF e înlocuită de cea din contracte §2, partea de deploy de pasul 16 (Docker Compose pe un server Linux), iar MinIO/S3 din PDF de stocarea pe disc local (contracte §8).

Faza curentă: dezvoltare pe date mock. Fără integrare cu drona.

Orice schimbare de API regenerează `openapi/openapi.json` (`make openapi`) și îl comite în același PR.

Comenzi:
- teste și lint: `uv run pytest && uv run ruff check`
- deploy producție: `deploy/` (vezi [16-deploy.md](docs/dev-plan/16-deploy.md))
- servicii locale: `make up` (`docker compose -f infra/docker-compose.yml up -d`)
