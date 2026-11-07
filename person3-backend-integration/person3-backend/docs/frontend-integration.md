# Person 1 — React API integration

Base URL: http://127.0.0.1:8000. OpenAPI: GET /openapi.json; interactive docs:
GET /docs. Set CORS_ORIGINS to exact frontend origins. These are illustrative
JSON examples, not a claim of successful live GitHub publishing. All nine routes
exist; requests reject unknown fields. Responses use the shapes below.

## Ticket JSON shared by create/list/details/analyze

Create request (ticket_id, branch and priority are optional):
```json
{"ticket_id":"TICKET-001","title":"Addition regression","description":"add(2,3) returns -1","repository":"owner/demo-repository","branch":"main","priority":"high"}
```

Ticket response; create defaults priority to medium and branch to main:
```json
{"ticket_id":"TICKET-001","title":"Addition regression","description":"add(2,3) returns -1","repository":"owner/demo-repository","branch":"main","priority":"high","status":"submitted","created_at":"2026-11-07T12:00:00+00:00","updated_at":"2026-11-07T12:00:00+00:00"}
```

- POST /tickets: body is Create above; 201 returns Ticket above. Duplicate ID: 409.
- GET /tickets?limit=100&offset=0: no body; 200 returns
  `{"items":[<Ticket objects>]}`. Limit 1–200; offset >= 0.
- GET /tickets/{ticket_id}: no body; 200 returns Ticket; unknown ID: 404.
- POST /tickets/{ticket_id}/analyze: no body; 200 returns Ticket with
  status=patch_ready on success. It is a synchronous request; it may take time.
  The adapter is currently a deterministic demo mock, not a real AI analysis.
  State conflicts return 409; integration failure returns 502 and persists
  analysis_failed so the analysis can be retried.

TicketRead does not expose approval, verification output, patch or PR records;
use the operation responses and GET /patch/events. After a UI reload, /verify
may be run again in allowed states, and /pull-request can return its saved result
if approval/verification and the human credential still match. Do not infer
successful verification from the displayed ticket status alone.

## GET /tickets/{ticket_id}/events

No body. Query after_id=0 and limit=100 (max 200). Response 200:
```json
{"items":[{"id":1,"ticket_id":"TICKET-001","actor":"switch:mock","kind":"agent_progress","message":"Demo investigation completed","created_at":"2026-11-07T12:00:00+00:00"}]}
```

IDs increase globally. Poll every 1.5–2 seconds using the greatest received ID
as after_id, append only unseen IDs and escape all messages as text. If a page
is full, fetch the next page immediately. Back off on network/503 errors; stop
on component unmount and after the relevant operation completes. Started events
are available while analysis runs; adapter progress strings are currently stored
as a batch when the adapter returns. This is polling JSON, not SSE/WebSockets.

## GET /tickets/{ticket_id}/patch

No body. Response 200 (example SHA/hash values are placeholders):
```json
{"base_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","summary":"Correct addition","files":[{"path":"app.py","content":"def add(a, b):\n    return a + b\n"}],"patch_hash":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","diff":"--- a/app.py\n+++ b/app.py\n@@ -1,2 +1,2 @@\n def add(a, b):\n-    return a - b\n+    return a + b\n"}
```

Before a candidate exists, returns 409. Render diff as escaped text. Files are
full UTF-8 replacement contents; no frontend patch upload endpoint exists. Retain
the exact server-returned patch_hash/base_sha for approval; never reconstruct them.

## POST /tickets/{ticket_id}/verify

No body. Can run before human approval. Response 200:
```json
{"status":"passed","exit_code":0,"output":"3 passed","patch_hash":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","base_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
```

status is passed, failed, timeout or unavailable; exit_code may be null. HTTP 200
means the attempt completed, not that tests passed. Inspect status and show the
captured output. Only passed for the current candidate/base permits publishing.
No shell command or Docker configuration is accepted from the browser.

## POST /tickets/{ticket_id}/approve

Requires `Authorization: Bearer <human-only credential>`. Body:
```json
{"patch_hash":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","base_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}
```

Response 200:
```json
{"patch_hash":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","base_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","approved_by":"hackathon-reviewer","approved_at":"2026-11-07T12:00:00+00:00"}
```

401 means missing/invalid credential; 503 means the backend has no approval
credential configured; 409 means stale candidate/base or an invalid state.
Approval can precede verification, but publication requires BOTH. Make approval
a deliberate human action after reviewing the displayed patch. Agent text never
counts as approval. The static bearer token is a hackathon single-reviewer
mechanism, not SSO. Keep it out of code, bundles, URLs, localStorage and agent
channels. A shared deployment should use a server-side authenticated human proxy.

## POST /tickets/{ticket_id}/pull-request

No body; same human-only bearer credential required. Response 200:
```json
{"url":"https://github.com/owner/demo-repository/pull/1","number":1,"head_sha":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","branch":"fix/TICKET-001-cccccccccccccccc"}
```

Requires exact stored approval and passed verification; otherwise 409 (these
state gates are evaluated before the credential check). If gates pass but auth
is missing/invalid, returns 401. Branch drift returns 409, GitHub failure 502.
A successful live operation creates a draft PR; it never merges. Saved results
are returned on repeated successful calls. Display the URL and current head for
human review. In the local HTTP validation harness this response is explicitly
fake and uses example.invalid; it is not proof that GitHub publishing works.

## States and errors

Ticket status values: submitted, analyzing, analysis_failed, patch_ready,
verifying, verified, verification_failed, approved, publishing, pr_created.
There is no queued, merged, done or completed state. Full transitions are in
api-contract.md. Disable duplicate actions during in-flight states. A crashed
synchronous operation may need operator recovery; this is not a durable queue.

Errors:
```json
{"error":{"code":"409","message":"Approval does not match the current candidate"}}
```
```json
{"error":{"code":"validation_error","message":"Request does not match the API contract","details":[{"location":["body","title"],"message":"Field required"}]}}
```

404 unknown ticket; 409 state/duplicate/stale conflicts; 401 human authentication;
422 validation; 502 integration error; 503 database unavailable (Retry-After: 1)
or approval credential unconfigured. Database error code is database_unavailable;
GitHub's direct integration handler uses integration_error. Preserve the server's
message; never report success based only on fetch completing.

## Example browser calls

```javascript
const BASE = 'http://127.0.0.1:8000';
async function api(path, {method = 'GET', body, humanToken, signal} = {}) {
  const response = await fetch(`${BASE}${path}`, {
    method, signal,
    headers: {
      ...(body !== undefined ? {'Content-Type': 'application/json'} : {}),
      ...(humanToken ? {'Authorization': `Bearer ${humanToken}`} : {}),
    },
    ...(body !== undefined ? {body: JSON.stringify(body)} : {}),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error?.message || `HTTP ${response.status}`);
  return data;
}
const id = encodeURIComponent('TICKET-001');
await api('/tickets', {method: 'POST', body: {
  ticket_id: 'TICKET-001', title: 'Addition regression', description: 'Wrong sum',
  repository: 'owner/demo-repository', branch: 'main', priority: 'high',
}});
const list = await api('/tickets?limit=100&offset=0');
const details = await api(`/tickets/${id}`);
await api(`/tickets/${id}/analyze`, {method: 'POST'});
const events = await api(`/tickets/${id}/events?after_id=0&limit=100`);
const patch = await api(`/tickets/${id}/patch`);
const verification = await api(`/tickets/${id}/verify`, {method: 'POST'});
// Later, in a separate explicit human click handler; token supplied securely:
async function approveAndPublish(humanToken) {
  if (verification.status !== 'passed') throw new Error('Verification did not pass');
  await api(`/tickets/${id}/approve`, {method: 'POST', humanToken, body: {
    patch_hash: patch.patch_hash, base_sha: patch.base_sha,
  }});
  return api(`/tickets/${id}/pull-request`, {method: 'POST', humanToken});
}
```

Start polling alongside the pending analyze request to display in-flight status,
using an AbortController and cleanup in the React effect. The sequential example
above illustrates payloads; it is not an orchestration implementation.
