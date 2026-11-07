# Person 2 — Switch / Mattermost integration contract

Current capability: a mockable synchronous Python adapter. Real Switch transport,
Mattermost wiring, credentials and agent coordination are owned by Person 2 and
are not implemented/configured here. No undocumented Switch HTTP API is assumed.

## How analysis is triggered

A frontend or your coordinator calls POST /tickets to persist a ticket, then
POST /tickets/{ticket_id}/analyze with no body. FastAPI claims analyzing state,
reads the target branch's immutable base SHA via GitHubService, then invokes:

```python
class SwitchAdapter(Protocol):
    def analyze(self, ticket: TicketRead, base_sha: str) -> AnalysisResult: ...
```

The adapter receives ticket fields (ticket_id/title/description/repository/branch/
priority/status/timestamps) and a 40-hex base SHA. During this call the ticket
status is analyzing. Implement your adapter using a verified Switch SDK/transport,
with a bounded deadline, then inject it into create_app(switch=your_adapter).
The backend does not POST to an invented Switch URL and does not independently
orchestrate agents. The endpoint waits for the adapter's result; it is not an
accepted/asynchronous job endpoint and there is no callback/webhook route.

## Returning agent output

Return the existing AnalysisResult object, not an HTTP response. Example local
Python construction (sample data; no external integration implied):

```python
from app.schemas import Candidate, FileChange
from app.services.switch_adapter import AnalysisResult

result = AnalysisResult(
    candidate=Candidate(
        base_sha=base_sha,
        summary='Correct addition',
        files=[FileChange(path='app.py', content='def add(a, b):\n    return a + b\n')],
    ),
    events=['Investigation completed', 'Candidate prepared'],
)
```

If your transport uses JSON internally, map this shape to those Python objects:
```json
{"candidate":{"base_sha":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","summary":"Correct addition","files":[{"path":"app.py","content":"def add(a, b):\n    return a + b\n"}]},"events":["Investigation completed","Candidate prepared"]}
```

This JSON is an adapter mapping contract, NOT a new supported Switch endpoint.
Return exactly the supplied base SHA. Candidates allow 1–10 distinct existing
relative .py source paths and <=100,000 characters of content per file. Full replacement content
is required; traversal, hidden components, tests and configuration are forbidden.
Backend validates the candidate, reads the original files, computes the display
diff and SHA256, and saves it as patch_ready. Hash input is canonical sorted
compact JSON of base_sha, summary and files; clients should use the returned hash
rather than reimplementing it. No POST /patch or arbitrary shell-command field
exists. Raise IntegrationError or ValueError for failures without secrets; the
backend also catches unexpected adapter failures, records analysis_failed and
returns a safe 502. Retrying analysis_failed is allowed.

## Events and agent statuses

AnalysisResult.events is currently a list of strings, not event/status objects.
The backend creates event JSON for GET /tickets/{id}/events:
```json
{"items":[{"id":1,"ticket_id":"TICKET-001","actor":"switch:adapter","kind":"agent_progress","message":"Candidate prepared","created_at":"2026-11-07T12:00:00+00:00"}]}
```

IDs/ticket_id/actor/kind/timestamps are backend-assigned. Mock actor is
switch:mock; an injected real adapter is labelled switch:adapter. Messages are
untrusted display text, truncated to 2000 characters. They never authorize a
state transition or human approval. Poll after_id/limit; see frontend guide.

There is NO separate per-agent status enum or status mutation endpoint. Do not
invent statuses such as agent_approved or merged. Current ticket statuses are:
submitted, analyzing, analysis_failed, patch_ready, verifying, verified,
verification_failed, approved, publishing, pr_created. Agent messages are
informational progress only. Backend events additionally use submitted,
analyzing, patch_ready, analysis_failed, verifying, verification, approved,
publishing, publication_failed and pr_created kinds. These are events, not a
separate agent workflow. Started state is observable during the call, but agent
progress is stored in a batch after analyze returns. Incremental streaming,
callbacks and asynchronous reconciliation need a separately agreed future
contract; none has been fabricated or deployed.

## Verification, approval and GitHub

POST /tickets/{id}/verify (no body) tests the stored candidate in restricted
Docker before or after approval. Agents do not upload Dockerfiles, dependency
commands or verification outcomes. The backend uses its own trusted image,
immutable source snapshot and fixed pytest invocation, and binds results to the
candidate hash/base. failed/timeout/unavailable never permit publishing.

Only a real human review client may POST /approve with exact patch_hash/base_sha
and the separately provisioned HUMAN_APPROVAL_TOKEN bearer credential. Switch,
Mattermost and agents must never receive that token. A message containing
“approved” is not human authorization. A human client subsequently POSTs
/pull-request with the same credential. Backend checks approval, verification
and base drift, creates a draft PR and never merges it. External PR write paths
are implemented and mock-tested; a live authorized publishing acceptance check
is still required. Automated fixture approval checks use disposable test tokens
and mock GitHub, and must not be presented as a real human approval.

## What Person 2 must supply

- Confirm the actual Switch SDK/API, transport/authentication and deadlines.
- Implement/validate the adapter mapping against the pinned repository/base.
- Configure Mattermost on your side; no webhook or messaging integration exists
  in this backend and none was called during validation.
- Agree how your actual orchestration returns a single candidate within the
  synchronous boundary. If long-running jobs are required, agree an authenticated
  async contract with Person 3 before changing routes or adding callbacks.
- Run local adapter/API tests, then conduct a separately authorized disposable
  repository test with a real human reviewer. Keep results distinguishable from
  the default mock adapter and the test-only http_fixture factory.
