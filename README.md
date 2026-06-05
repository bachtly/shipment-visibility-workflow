# Shipment Visibility System

Demo app showcasing **DBOS durable workflows** and **Azure IaC** for a freight shipment portal. Vendor webhook events are simulated by buttons in the UI.

## Stack

| Layer    | Technology                                                        |
| -------- | ----------------------------------------------------------------- |
| Backend  | Python 3.12 · FastAPI · DBOS Transact 2.23                         |
| Frontend | React 18 · Vite · TypeScript                                       |
| Database | PostgreSQL 16 (DBOS system tables + app tables in one DB)          |
| IaC      | Terraform + Terragrunt · Azure Container Apps + Postgres Flexible  |
| CI/CD    | GitHub Actions (OIDC to Azure, no stored credentials)             |

## What it demonstrates

- **Durable workflows** — the full milestone chain (10 statuses across 3 legs) runs as one long-lived workflow. Kill the backend mid-flight, restart, and DBOS resumes exactly where it left off.
- **Customs gate child workflow** — export and import customs run as child workflows with a hold → respond → review loop, escalating after 3 failed attempts.
- **Durable messaging** — `DBOS.send` / `DBOS.recv` deliver vendor events to the right workflow; no event is lost across restarts.
- **Conductor observability** — running and finished workflows are visible in the managed DBOS Conductor console.
- **Best-practice Azure IaC** — Container Apps (scale-to-zero dev, always-on staging), private Postgres, managed identity for ACR/Key Vault, Log Analytics + App Insights, Terragrunt dev/staging split.

## Shipment journey

![Milestone chain — three legs: origin, main haul, destination](docs/milestone_chain.svg)

Each **customs gate** is a child workflow:

![Customs gate sub-state machine — declaration → review → released or held/query loop](docs/customs_gate_chain.svg)

## Quick start (Docker)

> **Requires:** Docker Desktop running. Nothing else.

```bash
git clone <repo> && cd shipment-visibility-system
cp .env.example .env          # DBOS_CONDUCTOR_KEY is pre-filled
docker compose up -d --build  # first build ~2 min, then cached
```

Open **http://localhost:5173**. Three containers come up:

| Container  | Port   | Role                                              |
| ---------- | ------ | ------------------------------------------------- |
| `postgres` | `5433` | PostgreSQL 16 — DBOS system tables + app tables   |
| `backend`  | `8080` | FastAPI + DBOS, hot-reload via uvicorn `--reload` |
| `frontend` | `5173` | Vite dev server, proxies `/api` → backend         |

**Drive a shipment:**
1. **New Shipment** → enter a reference (e.g. `PO-2025-001`).
2. Click event buttons to advance through the milestone chain.
3. At **Export Customs**, file the declaration, then **Customs Hold → Query Response → Customs Released** to see the loop. Three holds in a row triggers **Escalation**.

**Prove durability** — while a shipment is *In Transit*:
```bash
docker compose stop backend     # kill mid-flight
docker compose start backend    # DBOS resumes the workflow automatically
```

<details>
<summary><b>Tests, logs &amp; teardown</b></summary>

```bash
# Tests
docker compose exec backend pytest tests/test_domain.py -v                 # unit (no DB)
docker compose exec backend pytest tests/test_api.py -v -m integration     # integration (needs DB)

# Logs
docker compose logs -f backend     # backend + DBOS
docker compose logs -f frontend    # Vite
docker compose logs -f postgres    # Postgres

# Teardown
docker compose down                # stop, keep DB volume
docker compose down -v             # stop + delete DB volume (full reset)
```

Conductor console: open [conductor.dbos.dev](https://conductor.dbos.dev) and find app `shipment-visibility` for step-by-step workflow history.
</details>

## API reference

| Method | Path                         | Description                                               |
| ------ | ---------------------------- | --------------------------------------------------------- |
| `GET`  | `/api/healthz`               | Health check                                              |
| `GET`  | `/api/shipments`             | List all shipments                                        |
| `POST` | `/api/shipments`             | Create shipment + start workflow (`{"reference": "..."}`) |
| `GET`  | `/api/shipments/{id}`        | Full shipment detail (events, customs)                    |
| `POST` | `/api/shipments/{id}/events` | Fire a vendor event (`{"event_type": "..."}`)             |
| `GET`  | `/api/shipments/{id}/stream` | SSE stream — live status updates                          |

<details>
<summary><b>Allowed events per status</b></summary>

| Status                              | Allowed events                                        |
| ----------------------------------- | ----------------------------------------------------- |
| `created`                           | `cargo_picked_up`                                     |
| `picked_up`                         | `consolidated`                                        |
| `consolidated`                      | `at_port`                                             |
| `drayage`                           | `export_declaration_filed`                            |
| `export_customs` / `import_customs` | `customs_released`, `customs_held`, `query_responded` |
| `handover` / `in_transit`           | `transit_ping`, `arrived`                             |
| `inland_haul`                       | `delivered`                                           |
| `delivered`                         | `closed_out`                                          |
</details>

## Project structure

<details>
<summary>Tree</summary>

```
shipment-visibility-system/
├── docker-compose.yml          ← local dev (postgres + backend + frontend)
├── Dockerfile                  ← production multi-stage build
├── .env.example                ← copy to .env
├── docs/                       ← SVG state machine diagrams
├── backend/app/
│   ├── main.py                 ← FastAPI + DBOS init + Conductor connection
│   ├── domain.py               ← enums, state machine, allowed-events table
│   ├── models.py               ← SQLAlchemy ORM models
│   ├── workflows.py            ← shipment_workflow + customs_gate_workflow
│   ├── db.py                   ← @DBOS.step DB operations
│   ├── steps.py                ← @DBOS.step side-effects (notifications)
│   └── api.py                  ← FastAPI routes
├── frontend/src/
│   ├── components/             ← MilestoneChain, CustomsPanel, EventButtons, Timeline
│   ├── hooks/                  ← useShipmentStream (SSE + poll fallback)
│   ├── domain.ts               ← status labels, colours, allowed-events mirror
│   └── api.ts                  ← fetch-based API client
└── infra/
    ├── modules/azure-stack/    ← reusable Terraform module (Container App, Postgres, ACR, Key Vault, VNet, Logs)
    ├── root.hcl                ← Terragrunt remote state + provider generation
    └── live/
        ├── dev/terragrunt.hcl      ← scale-to-zero, B1ms Postgres
        └── staging/terragrunt.hcl  ← always-on, GP Postgres
```
</details>

## Infrastructure (Azure)

Deploy with Terragrunt (requires Azure CLI authenticated + OIDC in GitHub Actions):

```bash
# First time: create the remote-state storage account manually, then:
cd infra/live/dev
terragrunt init && terragrunt plan && terragrunt apply
```

The module provisions Container Apps (HTTP ingress, TLS, autoscale, managed identity), a **private** PostgreSQL Flexible Server (VNet + Private DNS), Container Registry (managed-identity pull), Key Vault (DB password + Conductor key), and Log Analytics + Application Insights. Dev scales to zero; staging is always-on, production-shaped.

## CI/CD

- **`ci.yml`** (every PR) — domain unit tests, frontend typecheck + build, Terragrunt plan for dev.
- **`deploy.yml`** (merge to main) — build image → push to ACR → `terragrunt apply` dev; staging needs manual approval.

Required secrets: `ARM_SUBSCRIPTION_ID`, `ARM_TENANT_ID`, `ARM_CLIENT_ID` (OIDC), `DBOS_CONDUCTOR_KEY`, `ACR_LOGIN_SERVER`.

## Environment variables

| Variable                   | Required | Description                                          |
| -------------------------- | -------- | ---------------------------------------------------- |
| `DBOS_SYSTEM_DATABASE_URL` | Yes      | `postgresql+psycopg://user:pass@host:5432/db`        |
| `DATABASE_URL`             | Yes      | Same value (app tables + DBOS share one DB)          |
| `DBOS_CONDUCTOR_KEY`       | No       | Connects app to managed Conductor for observability  |
