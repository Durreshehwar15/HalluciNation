# Shared repository handoff

The backend is ready for a review/integration feature branch. This is not a
claim that real Switch orchestration or the live human-approved GitHub publishing
workflow has been validated. Those remain explicit integration acceptance steps.

## Files to transfer

Copy these directories into a NEW team feature branch, preserving their relative
locations: `backend/`, `demo-repo/`, `scripts/`, `docs/`. The supplied integration
ZIP contains only Git-tracked files from these directories. It intentionally
omits this personal repository's root README, root pytest.ini and Git history.
It contains `.env.example`, not real credentials, runtime databases or caches.

`backend/pytest.ini` makes the service tests independent of team root settings.
The demo must remain a sibling of backend for the opt-in Docker fixtures. Do not
point the team's general test discovery at demo-repo: its regression is
intentionally failing. Run scripts/demo.py to validate its red/green behavior.

## Acceptance commands (from copied repository root)

```sh
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
docker build -t support-fix-verifier:local demo-repo
# In a managed HTTPS proxy environment, add:
# --secret id=proxy_ca,src=/etc/ssl/certs/ca-certificates.crt
(cd backend && RUN_DOCKER_TESTS=1 ../.venv/bin/pytest -v)
.venv/bin/python scripts/demo.py
.venv/bin/python scripts/smoke_api.py
```

Expected suite: 40 passed when Docker/image access is available. Without
RUN_DOCKER_TESTS=1 the four live Docker tests skip explicitly; skips are not
successful Docker verification. CI that promises Docker coverage must enable
that flag and build the trusted image first.

For the optional nine-endpoint live read/verification check, provision
GITHUB_TOKEN outside Git, then run:

```sh
.venv/bin/python scripts/validate_live_api.py \
  --repository TEAM/DEMO_REPOSITORY --branch DEMO_FEATURE_BRANCH
```

That branch must contain demo-repo/app.py and its tests. The script uses real
HTTP, SQLite, GitHub reads and Docker; Switch is the documented mock. It checks
401 for missing human credentials and 409 for unapproved publication. It never
authorizes a human approval, creates a candidate branch or publishes a candidate
PR. A missing token fails explicitly; it never substitutes fake success.

## Team responsibilities

- Person 1: use docs/api-contract.md or /openapi.json; configure CORS_ORIGINS;
  escape event/diff/test output; keep human credentials out of agent channels
  and shipped JavaScript. Test the review experience with a real human.
- Person 2: implement SwitchAdapter.analyze(ticket, base_sha), inject it using
  create_app(switch=...), and establish deadlines. No Switch HTTP endpoint or
  Mattermost configuration has been assumed. Agent messages cannot authorize
  approval or replace persisted verification results.
- Person 3: configure fresh persistent SQLite, repository-scoped GITHUB_TOKEN,
  separately provisioned HUMAN_APPROVAL_TOKEN, VERIFIER_IMAGE,
  MOCK_PATCH_PATH and VERIFIER_PROJECT_DIR. Run FastAPI on the Docker-enabled
  host or provide a separately designed runner service. The backend image
  itself intentionally has no Docker CLI/socket.

If the team already uses an `app` package, run this backend as a separate service
with --app-dir backend, or rename the package and imports consistently on the
integration branch. Do not overwrite existing team entry points or pytest config.

After integration, a human must review an exact candidate hash/base SHA, submit
approval through the authenticated flow, and verify creation of a draft PR in a
disposable demo branch. GitHub write paths currently have mocked REST tests;
that complete live publishing acceptance step remains outstanding. Never merge
this work or candidate fixes automatically.

For a credential-free nine-route HTTP check use scripts/validate_local_api.py.
It runs real Docker/SQLite but uses explicit GitHub and Switch fixtures. The
clean package is produced by scripts/package_integration.py; root INTEGRATION.md
is the authoritative manual transfer guide. Temporary outputs are not included.
