# TP Bot — Card Management & PDS Assisted RPA

Production-oriented MVP for Telegram-based support automation:
- `ISSUE_NEW`
- `REPLACE_DAMAGED`
- `TOPUP`

Stack:
- Python 3.12
- FastAPI
- aiogram v3
- async SQLAlchemy 2.x
- PostgreSQL + Alembic
- Docker / docker-compose

## Architecture

- `Control Bot` (group): task management, status actions, PDS copy actions.
- `Intake Bot` (DM): one-time token intake forms for guest-related flows.
- `API`: health and task retrieval endpoints.
- `Services`: state machine, invite token lifecycle, payload generation, audit.

## Project Structure

- `/Users/andrejeliseev/Documents/TelegramBotForSupport/app` — app code
- `/Users/andrejeliseev/Documents/TelegramBotForSupport/migrations` — Alembic
- `/Users/andrejeliseev/Documents/TelegramBotForSupport/tests` — pytest suite

## Environment

Create `.env` from `.env.example`.

Required vars:
- `DATABASE_URL=postgresql+asyncpg://tp_user:tp_pass@db:5432/tp_bot`
- `CONTROL_BOT_TOKEN=<telegram token>`
- `INTAKE_BOT_TOKEN=<telegram token>`
- `CONTROL_GROUP_ID=<telegram group id>`
- `INTAKE_BOT_USERNAME=<intake bot username without @>`
- `INVITE_EXPIRES_HOURS=24`

## How to Create Telegram Bots

1. Open `@BotFather`.
2. Create 2 bots:
   - control bot (for operators group)
   - intake bot (for guest private chat)
3. Put tokens into `.env`.
4. Add control bot to operator group and grant rights to send messages.

## Local Run (without Docker)

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run migrations:

```bash
alembic upgrade head
```

Run API:

```bash
uvicorn app.main:app --reload
```

Run Control Bot:

```bash
python -m app.bots.control_bot
```

Run Intake Bot:

```bash
python -m app.bots.intake_bot
```

## Docker Compose

```bash
docker-compose up --build
```

Migrate DB in container:

```bash
docker-compose exec api alembic upgrade head
```

## Production Deploy Checklist

```bash
cd /opt/tpbot
docker compose pull
docker compose up -d --build
docker compose exec api alembic upgrade head
docker compose ps
curl -sv http://127.0.0.1:8000/health
curl -sv http://127.0.0.1:8000/tasks/active
```

Expected:
- `/health` -> `200` with `{"status":"ok","db":"up"}`
- `/tasks/active` -> `200` (empty list `[]` is valid)

## Production Recovery (DB/Auth/Migrations)

If `/health` is `503` or `/tasks/active` is `500`:

```bash
cd /opt/tpbot
docker logs --tail=300 tpbot-api-1
docker inspect tpbot-api-1 --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E 'DATABASE_URL|POSTGRES_'
docker inspect tpbot-db-1 --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -E 'POSTGRES_|PGDATA'
docker exec tpbot-api-1 alembic current
docker exec tpbot-api-1 alembic upgrade head
curl -sv http://127.0.0.1:8000/health
curl -sv http://127.0.0.1:8000/tasks/active
```

## Task Lifecycle

Statuses:
- `CREATED`
- `DATA_COLLECTED`
- `IN_PROGRESS`
- `DONE_BY_SYSADMIN`
- `CONFIRMED`
- `CLOSED`
- `CANCELLED`

Allowed transitions enforced in `/Users/andrejeliseev/Documents/TelegramBotForSupport/app/services/state_machine.py`.

## One-Time Invite Tokens

For `ISSUE_NEW` and `REPLACE_DAMAGED`:
- unique UUID token
- token has `expires_at`
- token can be used only once (`used_at`)
- deep-link: `https://t.me/<intake_bot>?start=<token>`

## API

- `GET /health`
- `GET /tasks/{id}`
- `GET /tasks/active`

## PDS Assist Contract

Schema version: `pds-assist-v1`

Implemented in `/Users/andrejeliseev/Documents/TelegramBotForSupport/app/services/pds_payload_service.py`:
- deterministic clean JSON
- no null fields
- card numbers preserved as strings
- phone normalization to `+7XXXXXXXXXX` where possible
- operation-specific payload blocks
- optional hardening fields:
  - `ui_hints`
  - `operator_confirm_required`
  - `helper_target`

## Tests

Run:

```bash
pytest -q
```

Included:
- `test_issue_new_creation.py`
- `test_invite_token_usage.py`
- `test_status_transitions.py`
- `test_pds_payload_generation.py`
- `test_task_transition_idempotency.py`
- `test_permissions.py`
- `test_validation_service.py`
