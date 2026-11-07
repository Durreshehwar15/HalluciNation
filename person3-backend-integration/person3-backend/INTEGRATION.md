# Person 3 backend — manual team integration

This package is a local handoff, not a deployment or merge. No team repository
was accessed, and no code was pushed or published during this validation pass.

## Contents

- backend/: FastAPI/SQLite implementation, tests, requirements.txt, pytest.ini,
  Dockerfile and .env.example.
- demo-repo/: intentionally buggy Python application, tests and trusted verifier
  Dockerfile. Keep it beside backend/ so local Docker fixtures can find it.
- scripts/: demo, startup/HTTP checks and the reproducible local ZIP builder.
- docs/: API contract, frontend/Switch guides, validation summary and checklist.
- .env.example: convenience copy of backend/.env.example, with empty secrets.
- MANIFEST.json: SHA256 for every packaged source/configuration/documentation file.

Git history, virtualenvs, caches, runtime databases, real .env files and raw or
temporary test outputs are excluded. Test code contains visibly fictional test
credentials and mocked GitHub responses; those are not real integrations/secrets.

## Transfer without overwriting the team's work

1. Download the ZIP and its .sha256 file. In that directory run
   `sha256sum -c person3-backend-integration.zip.sha256` (or use your platform's
   SHA256 tool). Extract the person3-backend/ directory outside the team checkout.
2. In YOUR local team checkout, create a feature branch:
   `git switch -c integration/person3-backend`.
3. Inspect existing backend/, demo-repo/, scripts/ and docs/ first. Copy the
   matching extracted directories selectively. If a destination exists, merge
   its files manually; do not overwrite the team's entry point, root README,
   dependency files, existing tests or pytest configuration wholesale.
4. Keep backend/pytest.ini. It allows the backend's tests to run independently
   of the team's root pytest configuration. If the team already owns an `app`
   package, run this as a separate service with --app-dir backend or rename all
   imports consistently on the integration branch.
5. Install and validate from the team root:

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
docker build -t support-fix-verifier:local demo-repo
# If a managed HTTPS proxy requires its CA, add to docker build:
# --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt
(cd backend && RUN_DOCKER_TESTS=1 ../.venv/bin/python -m pytest)
.venv/bin/python scripts/demo.py
.venv/bin/python scripts/smoke_api.py
.venv/bin/python scripts/validate_local_api.py
```

The local HTTP validator requires Docker but uses no real GitHub credentials.
Its GitHub PR response is explicitly mocked. A missing verifier image/daemon
fails the check; it never silently substitutes success.

6. Copy .env.example to your local .env, configure it outside Git, then load it:

```sh
cp backend/.env.example .env
# Edit .env privately. Never add it to Git.
set -a
. ./.env
set +a
.venv/bin/uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Use a fresh persistent SQLite database; do not transfer runtime DB files from
this package. Only provision a GitHub token after explicit authorization for a
disposable demo repository. Keep the human approval credential separate from
Switch, Mattermost, agents and shipped React code. Confirm exact CORS origins.

7. Person 1 follows docs/frontend-integration.md. Person 2 implements the existing
   adapter per docs/switch-integration.md; there are no assumed Switch URLs.
8. A real human must review an exact candidate/base, approve it through the API,
   and verify a draft PR against an authorized disposable demo branch before
   claiming live end-to-end GitHub publishing works. This step was not performed.
9. Review `git diff` and `git status` for secrets/unrelated files. Only when YOU
   are ready, commit/push this integration branch and open a team review PR.
   Never push directly to main, merge automatically, or transfer the personal
   repository's Git history just to copy this service.

Raw execution evidence is delivered beside the ZIP, not bundled into source.
See docs/verification.md for exact tested/mock/configuration boundaries. Remaining
MVP limitations include synchronous operations, a single-reviewer bearer token,
manual recovery after interrupted work, no migrations, and a Python-only trusted
verification profile. The production backend image lacks Docker CLI/socket access;
run verification from the Docker-enabled host or later inject a reviewed remote
runner implementation. Never mount Docker's socket into candidate containers.
