import difflib
import secrets
import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from sqlalchemy import select, text

from ..models import Event, Ticket, now
from ..schemas import (
    ApprovalRead,
    ApprovalRequest,
    Candidate,
    EventList,
    PatchRead,
    PullRequestRead,
    TicketCreate,
    TicketList,
    TicketRead,
)
from ..services.docker_runner import VerificationResult
from ..services.github_service import IntegrationError

router = APIRouter(prefix="/tickets", tags=["tickets"])


def session(request: Request):
    with request.app.state.sessions() as db:
        yield db


def write_session(request: Request):
    # Short SQLite write transactions claim each operation before external calls.
    with request.app.state.sessions() as db:
        db.execute(text("BEGIN IMMEDIATE"))
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise


def get_ticket(db, ticket_id):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "Ticket not found")
    return ticket


def event(db, ticket, kind, message, actor="backend"):
    ticket.updated_at = now()
    db.add(Event(ticket_id=ticket.ticket_id, kind=kind, message=message, actor=actor))


def human(request: Request, authorization: str | None = Header(default=None)):
    token = request.app.state.human_token
    if not token:
        raise HTTPException(503, "Human approval credential is not configured")
    if not authorization or not secrets.compare_digest(
        authorization.encode("utf-8"), ("Bearer " + token).encode("utf-8")
    ):
        raise HTTPException(
            401,
            "Authenticated human credential required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return request.app.state.human_identity


def candidate(ticket):
    if not ticket.patch:
        raise HTTPException(409, "Analysis has not produced a candidate")
    return Candidate.model_validate(
        {k: v for k, v in ticket.patch.items() if k not in ("patch_hash", "diff")}
    )


@router.post("", response_model=TicketRead, status_code=201)
def create(body: TicketCreate, db=Depends(write_session)):
    data = body.model_dump()
    data["ticket_id"] = data["ticket_id"] or "TICKET-" + uuid.uuid4().hex[:12].upper()
    if db.get(Ticket, data["ticket_id"]):
        raise HTTPException(409, "Ticket ID already exists")
    ticket = Ticket(**data)
    db.add(ticket)
    db.flush()
    event(db, ticket, "submitted", "Ticket created")
    return ticket


@router.get("", response_model=TicketList)
def list_tickets(
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db=Depends(session),
):
    return {
        "items": db.scalars(
            select(Ticket)
            .order_by(Ticket.created_at, Ticket.ticket_id)
            .offset(offset)
            .limit(limit)
        ).all()
    }


@router.get("/{ticket_id}", response_model=TicketRead)
def details(ticket_id: str, db=Depends(session)):
    return get_ticket(db, ticket_id)


@router.post("/{ticket_id}/analyze", response_model=TicketRead)
def analyze(ticket_id: str, request: Request, db=Depends(write_session)):
    ticket = get_ticket(db, ticket_id)
    if ticket.status not in ("submitted", "analysis_failed"):
        raise HTTPException(
            409, "Analysis requires submitted or analysis_failed status"
        )
    ticket.status = "analyzing"
    event(db, ticket, "analyzing", "Analysis started")
    db.commit()
    try:
        base = request.app.state.github.branch_sha(ticket.repository, ticket.branch)
        result = request.app.state.switch.analyze(
            TicketRead.model_validate(ticket), base
        )
        patch = Candidate.model_validate(result.candidate.model_dump())
        if patch.base_sha != base:
            raise IntegrationError("Adapter returned a different base commit")
        diffs = []
        for change in patch.files:
            old = request.app.state.github.read_file(
                ticket.repository, change.path, base
            )
            diffs.extend(
                difflib.unified_diff(
                    old.splitlines(keepends=True),
                    change.content.splitlines(keepends=True),
                    fromfile="a/" + change.path,
                    tofile="b/" + change.path,
                )
            )
        if not diffs:
            raise IntegrationError("Adapter returned an empty patch")
        ticket.patch = {
            **patch.model_dump(),
            "patch_hash": patch.digest(),
            "diff": "".join(diffs),
        }
        ticket.status = "patch_ready"
        ticket.approval = ticket.verification = None
        actor = (
            "switch:mock"
            if type(request.app.state.switch).__name__ == "MockSwitchAdapter"
            else "switch:adapter"
        )
        for message in result.events:
            event(db, ticket, "agent_progress", str(message)[:2000], actor)
        event(
            db, ticket, "patch_ready", "Candidate saved; no human authorization implied"
        )
    except Exception:
        ticket.status = "analysis_failed"
        event(
            db,
            ticket,
            "analysis_failed",
            "Analysis integration failed; no candidate was authorized",
        )
        db.commit()
        raise HTTPException(502, "Analysis failed; inspect ticket events") from None
    return ticket


@router.get("/{ticket_id}/events", response_model=EventList)
def events(
    ticket_id: str,
    after_id: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db=Depends(session),
):
    get_ticket(db, ticket_id)
    return {
        "items": db.scalars(
            select(Event)
            .where(Event.ticket_id == ticket_id, Event.id > after_id)
            .order_by(Event.id)
            .limit(limit)
        ).all()
    }


@router.get("/{ticket_id}/patch", response_model=PatchRead)
def patch(ticket_id: str, db=Depends(session)):
    ticket = get_ticket(db, ticket_id)
    candidate(ticket)
    return ticket.patch


@router.post("/{ticket_id}/approve", response_model=ApprovalRead)
def approve(
    ticket_id: str,
    body: ApprovalRequest,
    identity=Depends(human),
    db=Depends(write_session),
):
    ticket = get_ticket(db, ticket_id)
    patch = candidate(ticket)
    if ticket.status not in (
        "patch_ready",
        "verified",
        "verification_failed",
        "approved",
    ):
        raise HTTPException(409, "Ticket cannot be approved in its current state")
    if body.patch_hash != patch.digest() or body.base_sha != patch.base_sha:
        raise HTTPException(409, "Approval does not match the current candidate")
    ticket.approval = {
        **body.model_dump(),
        "approved_by": identity,
        "approved_at": now(),
    }
    ticket.status = "approved"
    event(
        db,
        ticket,
        "approved",
        f"Approved candidate {patch.digest()}",
        "human:" + identity,
    )
    return ticket.approval


@router.post("/{ticket_id}/verify", response_model=VerificationResult)
def verify(ticket_id: str, request: Request, db=Depends(write_session)):
    ticket = get_ticket(db, ticket_id)
    patch = candidate(ticket)
    if ticket.status not in (
        "patch_ready",
        "approved",
        "verified",
        "verification_failed",
    ):
        raise HTTPException(409, "Ticket cannot be verified in its current state")
    ticket.status = "verifying"
    ticket.verification = None
    event(db, ticket, "verifying", "Isolated verification started")
    db.commit()
    try:
        result = request.app.state.runner.verify(ticket.repository, patch)
    except Exception:
        result = VerificationResult(
            status="unavailable",
            output="Verification runner or repository snapshot unavailable",
        )
    result.patch_hash, result.base_sha = patch.digest(), patch.base_sha
    ticket.verification = result.model_dump()
    ticket.status = "verified" if result.status == "passed" else "verification_failed"
    event(db, ticket, "verification", result.status)
    return result


@router.post("/{ticket_id}/pull-request", response_model=PullRequestRead)
def pull_request(
    ticket_id: str,
    request: Request,
    authorization: str | None = Header(default=None),
    db=Depends(write_session),
):
    ticket = get_ticket(db, ticket_id)
    patch = candidate(ticket)
    approval, verification = ticket.approval or {}, ticket.verification or {}
    if (
        approval.get("patch_hash") != patch.digest()
        or approval.get("base_sha") != patch.base_sha
        or verification.get("status") != "passed"
        or verification.get("patch_hash") != patch.digest()
        or verification.get("base_sha") != patch.base_sha
    ):
        raise HTTPException(
            409, "Publishing requires matching human approval and passed verification"
        )
    human(request, authorization)
    if ticket.pull_request:
        return ticket.pull_request
    if ticket.status not in ("approved", "verified"):
        raise HTTPException(409, "Ticket cannot publish in its current state")
    if (
        request.app.state.github.branch_sha(ticket.repository, ticket.branch)
        != patch.base_sha
    ):
        raise HTTPException(
            409, "Base branch changed; create a new ticket and analyze again"
        )
    ticket.status = "publishing"
    event(db, ticket, "publishing", "Publishing approved candidate")
    db.commit()
    try:
        ticket.pull_request = request.app.state.github.publish(ticket, patch)
    except Exception:
        ticket.status = "verified"
        event(
            db, ticket, "publication_failed", "GitHub publication failed; retry safely"
        )
        db.commit()
        raise IntegrationError(
            "GitHub publication failed; retry safely or inspect the remote draft"
        ) from None
    ticket.status = "pr_created"
    event(db, ticket, "pr_created", ticket.pull_request["url"])
    return ticket.pull_request
