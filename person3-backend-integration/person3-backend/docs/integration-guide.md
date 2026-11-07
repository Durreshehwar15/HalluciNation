# Team integration guide

## Person 1 — React

Run the backend on localhost:8000; set the frontend API base URL accordingly.
Set CORS_ORIGINS to exact frontend origins (default localhost:5173). Generate
TypeScript types from `/openapi.json`, or use docs/api-contract.md.
Create a ticket, POST analyze, poll events and ticket status, show patch.diff
and verification.output as escaped text. POST verify before or after review.
Check verification.status, not just HTTP success. Disable duplicate in-flight
buttons and display structured error.message. Lists wrap records in items.

Human review must be a distinct authenticated action. Submit the exact
patch_hash and base_sha being displayed. Keep the human credential outside
agent access and outside bundled frontend source. For the local hackathon,
a reviewer may supply their token at runtime without persisting it; a shared
app should use an authenticated server-side proxy/session. Publishing also
requires the human credential. Link to the returned draft PR; no merge button
is implemented in this backend.

## Person 2 — Switch / Mattermost

Boundary: backend/app/services/switch_adapter.py. No Switch endpoint, network
payload, Mattermost webhook or agent orchestration is assumed.

Implement this synchronous Python protocol behind your own transport:
```python
class SwitchAdapter(Protocol):
    def analyze(self, ticket: TicketRead, base_sha: str) -> AnalysisResult: ...
```

AnalysisResult contains a Pydantic Candidate and a list of progress strings.
Candidate: base_sha (40 hex chars), summary (1–1000 chars), files (1–10
FileChange objects with path and full replacement UTF-8 content). Paths must
be relative existing .py source files, without traversal, hidden components,
tests or configuration. Duplicate paths are rejected; content max 100,000 characters/file.
The adapter must target the supplied immutable base SHA. Backend reads base
files, constructs the diff, hashes/stores the candidate, and records progress.
Return IntegrationError for transport failure or ValueError for invalid results;
never include transport secrets in exceptions or events. Adapter calls must have
a bounded deadline. The default mock deterministically fixes the demo addition
bug; it does not investigate real tickets or call AI.

Inject with `create_app(switch=YourAdapter(...))` from your composition module.
No route implementation should depend on your transport details. Agent progress
must never alter approval, credentials, verification results, DB status directly,
or call human endpoints using a human token. The backend accepts progress only
as event text. Async jobs/callback authentication should be agreed as a later
contract; there is currently no invented callback endpoint.

## Person 3 — verification and GitHub

GitHubService uses GitHub REST, a fine-grained GITHUB_TOKEN, pinned branch SHAs,
base-file contents and trees, atomic multi-file commits, deterministic fix
branches and draft PRs. It preserves original file modes and validates full
commit trees on retries. GitHub write methods are covered by MockTransport tests;
see verification.md for exactly which live calls were exercised.

DockerRunner gets the pinned snapshot and overlays the candidate in a temporary
workspace. It uses an operator-built image, a fixed `python -m pytest ... tests`
command, no shell, and no candidate Dockerfile/dependency installs. Operator
VERIFIER_PROJECT_DIR selects a standalone directory such as demo-repo. Snapshot
configuration rejects custom pytest config rather than silently changing test
discovery. Only .py files are copied; fixtures/package dependencies require a
future trusted verification profile. A successful verification binds to the
candidate digest/base and is independent of approval. Failed or unavailable
verification blocks PR creation.

## Move into the shared repository

1. Review/merge the personal feature PR first, or copy backend/, demo-repo/,
   scripts/demo.py and docs/ onto a NEW integration feature branch in the team
   repository. Do not push directly to the team's main branch.
2. Merge requirements and pytest configuration with the team's existing files;
   add backend to PYTHONPATH and backend/tests to test discovery. Do not replace
   the team's README or existing test configuration wholesale.
3. Keep `app` package and route prefix intact, or update imports consistently if
   the team already has a top-level app package. In a new entry point use
   `create_app(...)` and inject Person 2's adapter.
4. Provision environment variables separately. Never copy `.env`, PATs, human
   credentials, virtualenvs or SQLite runtime files into Git. Start with a fresh
   database or stop writers and back up/copy SQLite to persistent storage.
5. Build the trusted verifier image on the verifier host. Set MOCK_PATCH_PATH
   and VERIFIER_PROJECT_DIR to the agreed demo location. Set GITHUB_TOKEN access
   to the team/demo repository and CORS_ORIGINS to the actual frontend origin.
6. Run backend tests, opt-in Docker tests, and the failing/fixed trusted demo.
   Person 2 replaces only the adapter; Person 1 consumes the documented JSON.
   Exercise a real human review and draft PR against a demo feature branch
   before granting access to any important repository.

No automatic merge or team-main mutation is part of this integration.

The tested transfer checklist and portable backend test commands are in
[integration-checklist.md](integration-checklist.md). Current execution evidence,
including the exact mocked/live boundary for all nine endpoints, is in
[verification.md](verification.md).

Detailed handoffs: [frontend-integration.md](frontend-integration.md) and
[switch-integration.md](switch-integration.md). Use root INTEGRATION.md for the
clean package/manual transfer procedure.
