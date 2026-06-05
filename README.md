# Shipment Visibility System

Demo app showcasing **DBOS durable workflows** and **Azure IaC** for a freight shipment portal. Vendor webhook events are simulated by buttons in the UI.

## Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12 · FastAPI · DBOS Transact 2.23 |
| Frontend | React 18 · Vite · TypeScript |
| Database | PostgreSQL 16 (DBOS system tables + app tables in one DB) |
| IaC | Terraform + Terragrunt · Azure Container Apps + Postgres Flexible |
| CI/CD | GitHub Actions (OIDC to Azure, no stored credentials) |

## What it demonstrates

- **DBOS durable workflows** — the full shipment milestone chain (10 statuses across 3 legs) runs as one long-lived workflow. Kill the backend mid-flight, restart, and DBOS resumes exactly where it left off.
- **Customs gate child workflow** — export and import customs run as separate child workflows with a hold → respond → review loop and escalation after 3 failed attempts.
- **Durable messaging** — `DBOS.send` / `DBOS.recv` deliver vendor events to the right workflow. No event is ever lost, even across restarts.
- **Conductor observability** — the app connects to the managed DBOS Conductor so all running/finished workflows are visible in the console.
- **Azure best-practice IaC** — Container Apps (scale-to-zero dev, always-on staging), private Postgres, managed identity for ACR pull and Key Vault, Log Analytics / App Insights, Terragrunt dev/staging split.

## Shipment journey

```
Origin leg:     CREATED → Picked Up → Consolidated → Drayage → [Export Customs gate]
Main haul:      Handover → In Transit (ping loop) →
Destination:    [Import Customs gate] → Inland Haul → Delivered → Closed Out
```

Each **customs gate** is a child workflow:
```
Declaration Filed → Under Review → Released  (proceed)
                               ↘ Held/Query → Respond → back to Under Review
                                              (after 3 holds → Escalated)
```

## Local development (Docker)

> **Requirements:** Docker Desktop running. Nothing else needed.

### 1 — First-time setup

```bash
git clone <repo>
cd shipment-visibility-system
cp .env.example .env          # DBOS_CONDUCTOR_KEY is pre-filled from README
```

### 2 — Build images

```bash
docker compose build
```

First build takes ~2 min (pulls Python/Node base images, installs deps). Subsequent builds are cached.

### 3 — Start everything

```bash
docker compose up -d
```

Three containers start:

| Container | Port | What |
|---|---|---|
| `postgres` | `5433` (host) | PostgreSQL 16 — DBOS system tables + app tables |
| `backend` | `8080` | FastAPI + DBOS, hot-reload via uvicorn `--reload` |
| `frontend` | `5173` | Vite dev server, proxies `/api` → backend |

### 4 — Open the app

```
http://localhost:5173
```

1. Click **New Shipment**, enter a reference (e.g. `PO-2025-001`).
2. Click the event buttons to advance the shipment through the milestone chain.
3. When you reach **Export Customs**, file the declaration then try **Customs Hold** → **Query Response** → **Customs Released** to see the loop.
4. Hit 3 holds in a row to trigger **Escalation**.

### 5 — Verify DBOS durability

```bash
# While a shipment is In Transit, kill the backend
docker compose stop backend

# Restart — DBOS resumes the workflow automatically
docker compose start backend
```

The shipment status is preserved and the workflow continues accepting events.

### 6 — Check Conductor

Open [conductor.dbos.dev](https://conductor.dbos.dev) and look for app `shipment-visibility` to see all running/finished workflows and their step-by-step history.

### 7 — View logs

```bash
docker compose logs -f backend     # backend + DBOS logs
docker compose logs -f frontend    # Vite dev server
docker compose logs -f postgres    # Postgres
```

### 8 — Stop / tear down

```bash
docker compose down           # stop containers, keep DB volume
docker compose down -v        # stop and delete DB volume (full reset)
```

### 9 — Run unit tests (domain logic, no DB required)

```bash
docker compose exec backend pytest tests/test_domain.py -v
```

### 10 — Run integration tests (needs running DB)

```bash
docker compose exec backend pytest tests/test_api.py -v -m integration
```

## API reference

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/healthz` | Health check |
| `GET` | `/api/shipments` | List all shipments |
| `POST` | `/api/shipments` | Create shipment + start workflow (`{"reference": "..."}`) |
| `GET` | `/api/shipments/{id}` | Full shipment detail (events, customs) |
| `POST` | `/api/shipments/{id}/events` | Fire a vendor event (`{"event_type": "..."}`) |
| `GET` | `/api/shipments/{id}/stream` | SSE stream — pushes status updates live |

**Allowed events per status:**

| Status | Allowed events |
|---|---|
| `created` | `cargo_picked_up` |
| `picked_up` | `consolidated` |
| `consolidated` | `at_port` |
| `drayage` | `export_declaration_filed` |
| `export_customs` / `import_customs` | `customs_released`, `customs_held`, `query_responded` |
| `handover` / `in_transit` | `transit_ping`, `arrived` |
| `inland_haul` | `delivered` |
| `delivered` | `closed_out` |

## Project structure

```
shipment-visibility-system/
├── docker-compose.yml          ← local dev (postgres + backend + frontend)
├── Dockerfile                  ← production multi-stage build
├── .env.example                ← copy to .env
├── docs/                       ← SVG state machine diagrams
├── backend/
│   ├── Dockerfile.dev
│   ├── pyproject.toml
│   └── app/
│       ├── main.py             ← FastAPI + DBOS init + Conductor connection
│       ├── domain.py           ← enums, state machine, allowed-events table
│       ├── models.py           ← SQLAlchemy ORM models
│       ├── workflows.py        ← shipment_workflow + customs_gate_workflow
│       ├── db.py               ← @DBOS.step DB operations
│       ├── steps.py            ← @DBOS.step side-effects (notifications)
│       └── api.py              ← FastAPI routes
├── frontend/
│   └── src/
│       ├── components/         ← MilestoneChain, CustomsPanel, EventButtons, Timeline
│       ├── hooks/              ← useShipmentStream (SSE + poll fallback)
│       ├── domain.ts           ← status labels, colours, allowed-events mirror
│       └── api.ts              ← fetch-based API client
└── infra/
    ├── modules/azure-stack/    ← reusable Terraform module
    │   ├── main.tf             ← Container App, Postgres, ACR, Key Vault, VNet, Logs
    │   ├── variables.tf
    │   └── outputs.tf
    ├── root.hcl                ← Terragrunt remote state + provider generation
    └── live/
        ├── dev/terragrunt.hcl      ← scale-to-zero, B1ms Postgres
        └── staging/terragrunt.hcl  ← always-on, GP Postgres
```

## Infrastructure (Azure)

Deploy to Azure with Terragrunt (requires Azure CLI authenticated + OIDC set up in GitHub Actions):

```bash
# First time: create the remote state storage account manually, then:
cd infra/live/dev
terragrunt init
terragrunt plan
terragrunt apply
```

The module provisions:
- **Azure Container Apps** — HTTP ingress, TLS, autoscale, managed identity
- **PostgreSQL Flexible Server** — private via VNet + Private DNS
- **Container Registry** — managed-identity pull (no stored credentials)
- **Key Vault** — stores DB password and Conductor key
- **Log Analytics + Application Insights** — Container App log streaming
- **VNet** — delegated subnets for Container Apps and Postgres

Dev environment scales to zero; staging is always-on production-shaped.

## CI/CD

- `ci.yml` — runs on every PR: domain unit tests, frontend typecheck + build, Terragrunt plan for dev
- `deploy.yml` — runs on merge to main: build Docker image → push to ACR → `terragrunt apply` dev; staging requires manual approval

Required GitHub secrets: `ARM_SUBSCRIPTION_ID`, `ARM_TENANT_ID`, `ARM_CLIENT_ID` (OIDC), `DBOS_CONDUCTOR_KEY`, `ACR_LOGIN_SERVER`.

## Environment variables

| Variable | Required | Description |
|---|---|---|
| `DBOS_SYSTEM_DATABASE_URL` | Yes | `postgresql+psycopg://user:pass@host:5432/db` |
| `DATABASE_URL` | Yes | Same value (app tables + DBOS share one DB) |
| `DBOS_CONDUCTOR_KEY` | No | Connects app to managed Conductor for observability |
