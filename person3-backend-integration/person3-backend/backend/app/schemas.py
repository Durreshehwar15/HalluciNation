"""Versioned JSON contracts shared with frontend and Switch adapters."""

import hashlib
import json
from pathlib import PurePosixPath
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class TicketCreate(StrictModel):
    ticket_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,64}$")
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=10000)
    repository: str = Field(
        pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$", max_length=200
    )
    branch: str = Field(default="main", min_length=1, max_length=200)
    priority: Literal["low", "medium", "high", "critical"] = "medium"

    @field_validator("branch")
    @classmethod
    def valid_branch(cls, value):
        if (
            value.startswith(("-", "/", "."))
            or any(
                c in value
                for c in ["..", "@{", "\\", " ", "~", "^", ":", "?", "*", "["]
            )
            or value.endswith(("/", ".", ".lock"))
        ):
            raise ValueError("Invalid Git branch name")
        return value


class TicketRead(TicketCreate):
    ticket_id: str
    status: str
    created_at: str
    updated_at: str


class TicketList(StrictModel):
    items: list[TicketRead]


class FileChange(StrictModel):
    path: str = Field(min_length=1, max_length=240)
    content: str = Field(max_length=100000)

    @field_validator("path")
    @classmethod
    def safe_path(cls, value):
        path = PurePosixPath(value)
        if (
            path.is_absolute()
            or ".." in path.parts
            or "\\" in value
            or any(p.startswith(".") for p in path.parts)
            or str(path) != value
            or not value.endswith(".py")
            or any(p in ("tests", "test") for p in path.parts)
            or path.name.startswith(("test_", "conftest"))
        ):
            raise ValueError(
                "Candidate must modify a regular Python source path, not tests or configuration"
            )
        return value


class Candidate(StrictModel):
    base_sha: str = Field(pattern=r"^[0-9a-f]{40}$")
    summary: str = Field(min_length=1, max_length=1000)
    files: list[FileChange] = Field(min_length=1, max_length=10)

    @field_validator("files")
    @classmethod
    def unique_paths(cls, files):
        if len({f.path for f in files}) != len(files):
            raise ValueError("Duplicate file paths")
        return files

    def digest(self):
        return hashlib.sha256(
            json.dumps(
                self.model_dump(), sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest()


class PatchRead(Candidate):
    patch_hash: str
    diff: str


class ApprovalRequest(StrictModel):
    patch_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    base_sha: str = Field(pattern=r"^[0-9a-f]{40}$")


class ApprovalRead(ApprovalRequest):
    approved_by: str
    approved_at: str


class EventRead(StrictModel):
    id: int
    ticket_id: str
    actor: str
    kind: str
    message: str
    created_at: str


class EventList(StrictModel):
    items: list[EventRead]


class PullRequestRead(StrictModel):
    url: str
    number: int
    head_sha: str
    branch: str
