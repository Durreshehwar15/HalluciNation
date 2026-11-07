# Backend MVP

Python 3.11+; commands below run from repository root. SQLite creates its schema
on startup. No external database, frontend, or Switch server is needed.

## Start

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cp backend/.env.example .env
# Edit .env locally: set GITHUB_TOKEN and HUMAN_APPROVAL_TOKEN.
set -a
. ./.env
set +a
.venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000/docs for interactive OpenAPI documentation and
http://127.0.0.1:8000/openapi.json for the machine-readable schema.
Use a dedicated fine-grained GitHub token restricted to the demo repository,
with Contents and Pull requests read/write permissions. Never commit `.env`.
Only the human review client receives HUMAN_APPROVAL_TOKEN. An agent message,
actor string, ticket title or JSON status cannot authorize publication.

## Tests and reproducible demo

```sh
.venv/bin/python -m pytest
.venv/bin/python scripts/demo.py
# Trusted image: build once, independently of candidate code.
docker build -t support-fix-verifier:local demo-repo
RUN_DOCKER_TESTS=1 .venv/bin/python -m pytest
```

For a managed cloud HTTPS proxy, add
`--secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt` to Docker builds.
The optional CA is mounted only during pip installation and is not baked into
the image. TLS verification remains enabled.

`demo-repo/app.py` intentionally subtracts rather than adds. The demo helper
runs its trusted tests in a temporary copy: two failures before, three passes
after the known fix. It leaves the original bug intact. It is not a fallback
for production verification; candidate fixes always go through DockerRunner.

## API demo against this repository

Set MOCK_PATCH_PATH=demo-repo/app.py and VERIFIER_PROJECT_DIR=demo-repo, as in
`.env.example`. Set `branch` to the implementation feature branch until this
backend has been reviewed and merged into your personal repository. The base
branch must actually contain demo-repo/app.py and its tests.

```sh
curl -sS -X POST http://127.0.0.1:8000/tickets \
  -H 'Content-Type: application/json' \
  -d '{"ticket_id":"TICKET-001","title":"Addition regression","description":"add(2,3) returns -1","repository":"guizongzi/support-to-fix-backend","branch":"feat/backend-mvp","priority":"high"}'
curl -sS -X POST http://127.0.0.1:8000/tickets/TICKET-001/analyze
curl -sS http://127.0.0.1:8000/tickets/TICKET-001/patch
curl -sS -X POST http://127.0.0.1:8000/tickets/TICKET-001/verify
```

A human must inspect the diff and verification output, then POST `/approve`
with the exact `patch_hash` and `base_sha` returned by GET `/patch` and their
human-only Authorization bearer credential. POST `/pull-request` with the same
human credential afterwards. The backend creates a **draft PR**; no merge API
exists. Approval before verification is also supported; both must match.
For a separate repository containing only demo-repo's contents, use
MOCK_PATCH_PATH=app.py and VERIFIER_PROJECT_DIR= (empty).

## Docker deployment

```sh
docker build -t support-ticket-backend backend
docker volume create support-ticket-data
docker run --rm -p 127.0.0.1:8000:8000 --env-file .env \
  -e DATABASE_URL=sqlite:////data/tickets.db \
  --mount source=support-ticket-data,target=/data support-ticket-backend
```

The backend image persists SQLite in `/data` and runs as UID 65534. It does not
contain the Docker CLI or daemon access. Its ordinary ticket APIs work, but
verification returns unavailable unless deployed with a separately provisioned
runner. For the hackathon, run FastAPI on the Docker-enabled host. Do not mount
the Docker socket into candidate containers. A future remote verification
service can implement the same `verify(repository, candidate)` boundary.

## Operational scope

- One backend worker is recommended. Short BEGIN IMMEDIATE transactions claim
  transitions; external calls release the global writer lock. Other tickets
  remain writable during analysis and verification.
- Synchronous analyze/verify/publish requests return their completed result;
  another request can poll events while they run. This is an MVP, not a durable
  distributed job queue. Person 2 owns future asynchronous orchestration.
- An interrupted process can leave `analyzing`, `verifying`, or `publishing`.
  Stop workers before operator recovery: reset to `analysis_failed`,
  `verification_failed` (clear verification), or `verified`, respectively.
  Publishing retries validate the existing remote branch/tree/PR. Never edit
  approval hashes or manufacture a successful verification to recover.
- Snapshot verification supports at most 100 Python files / 2 MB in an
  operator-selected project directory, standard `tests/` pytest discovery,
  and the trusted pytest-only image. Custom pytest configuration, symlinks,
  submodules and package installation are rejected or unsupported. Non-Python
  fixtures are not copied. Use the supplied standalone demo for the hackathon;
  add a trusted project profile before verifying other applications.
- Network requests and Docker execution have deadlines. Captured test output is
  capped at 16 KB. Containers have no network, read-only root/source mounts,
  non-root UID, dropped capabilities, no-new-privileges, limited CPU/memory/PIDs
  and tmpfs. Docker containers are not a VM security boundary; use a dedicated
  verifier host for hostile public submissions.
- API reads and ticket/analysis/verification actions are intended for a trusted
  local/private demo network. CORS is not authentication. Protect the whole API
  at an authenticated gateway before exposing it publicly.
- The static human bearer token is a minimal single-reviewer credential, not an
  identity provider. Replace it with server-validated human sessions for a team
  deployment. Do not embed the token in a distributed React bundle or give it
  to Switch. The operator-configured reviewer identity is logged on approvals.
- SQLite create_all is appropriate for a fresh MVP database, not schema upgrades;
  introduce migrations when evolving existing tables. Back up the DB before
  moving it. Running containers and PR branches can be inspected after failures;
  no main-branch writes or automatic merges are performed.

## Portable team handoff

The backend now includes its own pytest.ini. After copying backend and its sibling
demo-repo into the team feature branch, test without changing team root settings:

```sh
(cd backend && RUN_DOCKER_TESTS=1 ../.venv/bin/pytest -v)
```

See docs/integration-checklist.md for the tested transfer layout and the optional
nine-route live HTTP validator. That validator never grants human approval or
publishes a candidate PR; its protected-route checks expect 401 and 409.

Current credential-free validation and clean packaging:

```sh
.venv/bin/python scripts/validate_local_api.py
.venv/bin/python scripts/package_integration.py --output /tmp/person3-backend-integration.zip
```

The first command uses real HTTP/SQLite/Docker with explicitly mocked GitHub and
Switch, never real credentials or remote publication. The second creates a
source-only handoff with root INTEGRATION.md, blank .env.example and a hash
manifest. It excludes raw test outputs and rejects populated credential examples.
Detailed contracts: docs/frontend-integration.md and docs/switch-integration.md.
