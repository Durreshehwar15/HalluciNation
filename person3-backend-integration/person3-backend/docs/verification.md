# Current Person 3 validation results

This pass continued the existing implementation and virtualenv. No project
rebuild, GitHub credential use, repository probe, push, PR publication or merge
was performed. The team's repository was not accessed. Earlier live GitHub logs
in this personal checkout are historical and were not repeated under this task's
credential restriction; raw logs are excluded from the clean transfer package.

## Actually executed

| Check | Actual result |
|---|---|
| .venv/bin/python -m pytest | 36 passed, 0 failed, 4 skipped |
| RUN_DOCKER_TESTS=1 .venv/bin/python -m pytest -v | 40 passed, 0 failed, 0 skipped |
| scripts/demo.py original copy | 2 failed, 1 passed (intentional bug) |
| scripts/demo.py fixed temporary copy | 3 passed |
| scripts/smoke_api.py | Real Uvicorn startup, OpenAPI, SQLite restart persistence passed |
| scripts/validate_local_api.py | Nine routes exercised over real HTTP; 16 expected checks passed |
| ruff check backend scripts --select F,I | Passed |

The four default skips are explicitly opted-in Docker tests, not simulated
success. Docker daemon 29.9.2 and the existing trusted Python 3.11/pytest 8.3.5
verifier image were actually used. The backend suite ran on Python 3.12.14.
One upstream Starlette/AnyIO deprecation warning remains, without test failures.
Raw execution logs are delivered separately from the portable source ZIP.

The Docker tests execute the failing and fixed demo, time out an infinite loop,
and assert UID 65534, no outbound TCP, read-only source/root filesystems, no
Docker socket or GitHub token and zero effective capabilities. Unit tests also
mock subprocess to check fixed commands, resource limits, bounded output and
cleanup. Real Docker snapshots in this pass come from local fixtures, not GitHub.
The real demo source remains buggy; the script prints the exact -/+ source diff
and applies the known fix only in a temporary directory.

## Endpoint observations and boundaries

| Route | HTTP observed in local harness |
|---|---|
| POST /tickets | 201 |
| GET /tickets | 200 |
| GET /tickets/{id} | 200 |
| POST /tickets/{id}/analyze | 200; repeat after publication rejected with 409 |
| GET /tickets/{id}/events | 200; progress explicitly labelled switch:mock |
| GET /tickets/{id}/patch | 200; candidate/diff/hash/base checked |
| POST /tickets/{id}/approve | 401 missing auth; 409 wrong hash; 200 test credential |
| POST /tickets/{id}/verify | 200 with actual Docker status=passed and 3 passing tests |
| POST /tickets/{id}/pull-request | 409 without approval; 200 MOCK GitHub response |

FastAPI, Uvicorn HTTP, SQLite persistence, diff/hash construction, authentication
checks and Docker are real in that harness. Its GitHub branch/file/snapshot/PR
service is a visibly named local fixture; its SHA is a fixture ID, not a commit.
The PR URL is example.invalid/MOCK-pull-request/1. Successful automated approval
uses a disposable TEST credential and actor test-fixture; it is not a real human
approval. No external GitHub write happens. Switch is the deterministic mock.

Additional API tests cover request/response validation, duplicate/missing IDs,
forbidden client status/approval fields, authentication failure/absence, exact
patch/base binding, failed verification, base drift, safe integration errors,
publication idempotency and other-ticket writes during verification. The actual
startup smoke also verifies a safe 502 with GITHUB_TOKEN explicitly empty.

## Changes made and verified

- Fixed a real malformed-header bug: non-ASCII Authorization previously raised
  TypeError in secrets.compare_digest. Comparing encoded bytes now returns a
  proper 401. A regression test was observed failing before the fix and passing
  afterwards; valid credentials still pass the workflow tests.
- Made the trusted demo print an actual source diff and fail if its expected bug
  cannot be replaced. Its regression test checks relevant failures, actual source
  change, passing fixed tests and preservation of the original tracked source.
- Added credential-free nine-route HTTP validation using test-only composition,
  keeping all mock/live labels explicit and real credentials out of its server.
- Added a portable ZIP builder and tests for preserved layout, blank template
  duplication, exclusion of env files/databases/caches/links/raw outputs and
  refusing populated example credentials without printing their values.
- Added root INTEGRATION.md and frontend/Switch guides matching current code.

## Integration classification

| Capability | Status |
|---|---|
| FastAPI/SQLite APIs, statuses, validation, human credential gates | Implemented and actually executed locally |
| Source diff/hash validation and patch/base binding | Implemented and actually executed locally |
| Docker isolation/results/timeouts | Implemented and actually executed with local source fixtures |
| GitHub REST branch/file/tree/commit/draft-PR code | Implemented; write/read boundary tests use httpx.MockTransport in this pass |
| Live access to a configured demo repository | Requires explicit authorization and a scoped token; not re-probed in this pass |
| Live human-approved candidate-to-draft-PR workflow | Not executed; requires an authorized demo repository and an actual human reviewer |
| Actual Switch SDK/transport and Mattermost | Not implemented/configured; Person 2 supplies them |
| Asynchronous jobs, streaming callbacks, per-agent status mutation | Not implemented; not assumed |
| Team repository integration | Manual transfer prepared; team repo not accessed |

Known MVP boundaries: single-reviewer static bearer token, private/local API
network, synchronous operations with operator recovery after interruption,
Python-only trusted verifier with standard tests/ and .py snapshots, no schema
migrations. GitHub heads remain mutable and must be reviewed manually before
merging. There is no merge operation. See root INTEGRATION.md for manual transfer,
frontend-integration.md for React, and switch-integration.md for the adapter.
