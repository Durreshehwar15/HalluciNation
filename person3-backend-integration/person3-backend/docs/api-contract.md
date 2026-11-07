# API contract v0.1

Base URL: http://127.0.0.1:8000. Content-Type: application/json.
Authoritative field definitions: `/openapi.json`. Additional request fields
are rejected with 422; timestamps are UTC ISO 8601. IDs are caller-supplied
`[A-Za-z0-9_-]{1,64}` or generated. List endpoints use `{ "items": [...] }`.

| Method | Endpoint | Request | Successful response |
|---|---|---|---|
| POST | /tickets | TicketCreate | 201 Ticket |
| GET | /tickets | query limit=100, offset=0 | 200 items of Ticket |
| GET | /tickets/{ticket_id} | — | 200 Ticket |
| POST | /tickets/{ticket_id}/analyze | no body | 200 Ticket |
| GET | /tickets/{ticket_id}/events | after_id=0, limit=100 | 200 items of Event |
| GET | /tickets/{ticket_id}/patch | — | 200 Patch |
| POST | /tickets/{ticket_id}/approve | Approval + human bearer | 200 Approval receipt |
| POST | /tickets/{ticket_id}/verify | no body | 200 Verification |
| POST | /tickets/{ticket_id}/pull-request | no body + human bearer | 200 PullRequest |

TicketCreate:
```json
{"ticket_id":"TICKET-001","title":"Login failure","description":"Correct password returns an error","repository":"owner/repository","branch":"main","priority":"high"}
```

`ticket_id` is optional; branch defaults to main, priority to medium. Priority:
low, medium, high, critical. Ticket responses add `status`, `created_at`,
`updated_at`; clients cannot set status or approval when creating a ticket.

Patch:
```json
{"base_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","summary":"Correct addition","files":[{"path":"app.py","content":"def add(a, b):\n    return a + b\n"}],"patch_hash":"<64 lowercase hex characters>","diff":"--- a/app.py\n+++ b/app.py\n..."}
```

`diff` is for display; files contain exact replacement UTF-8 content. No
agent-provided shell/apply command is executed. SHA256 covers canonical sorted
compact JSON of base_sha, summary and files. Candidates only replace existing
regular Python source files, not tests/configuration. Base file modes are
preserved. There is no client endpoint for uploading arbitrary patches.

Approval request (human Authorization: Bearer credential required):
```json
{"patch_hash":"<exact hash from Patch>","base_sha":"<exact base SHA from Patch>"}
```
Response adds `approved_by` (operator-configured identity) and `approved_at`.
The credential must be provisioned to the human outside agent channels. An
agent event saying “approved” has no effect on authorization.

Verification:
```json
{"status":"passed","exit_code":0,"output":"3 passed","patch_hash":"<candidate hash>","base_sha":"<pinned base>"}
```
`status`: passed, failed, timeout, unavailable. HTTP 200 means the verification
attempt completed; only `status=passed` permits publication. Missing image,
Docker failure or repository snapshot restrictions never produce a pass.
Approval is not required to test an isolated candidate.

Event:
```json
{"id":1,"ticket_id":"TICKET-001","actor":"switch:mock","kind":"agent_progress","message":"Demo investigation started","created_at":"2026-11-07T12:00:00+00:00"}
```
Events are polling JSON, not SSE. Use the largest received id as `after_id`.
Agent progress messages are untrusted display text; escape them in React.

PullRequest:
```json
{"url":"https://github.com/owner/repository/pull/1","number":1,"head_sha":"<published commit SHA>","branch":"fix/TICKET-001-<hash prefix>"}
```
The PR is a draft. Repeating successful publication returns the saved result;
retries after a partial GitHub failure validate exact parent and complete tree.
If the PR response shows a different head during creation, it is closed and the
operation fails. GitHub branches can change after creation; humans must review
the current PR head before merging. This backend never merges.

Transitions:
```text
submitted / analysis_failed -> analyzing -> patch_ready / analysis_failed
patch_ready / approved / verified / verification_failed -> verifying
verifying -> verified / verification_failed
patch_ready / verified / verification_failed / approved -> approved (human only)
approved / verified -> publishing -> pr_created
```
Publication requires matching persisted approval AND matching passed
verification regardless of displayed status. Base branch drift blocks publishing
with 409; submit a new ticket against the new base. Reanalysis of an already
prepared or published ticket is rejected. In-flight transitions reject concurrent
operations on the same ticket. A process crash needs operator recovery; see README.

Errors follow:
```json
{"error":{"code":"409","message":"Approval does not match the current candidate"}}
```
404 unknown ticket; 409 duplicate ID/invalid transition/stale approval or base;
401 absent/invalid human credential; 503 approval credential unconfigured;
422 schema error (includes location/message details); 502 external integration
failure. List limit is 1–200; event IDs are monotonically increasing globally.
