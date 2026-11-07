"""Local Python boundary only. No undocumented Switch HTTP API is assumed."""

from typing import Protocol

from ..schemas import Candidate, FileChange, TicketRead


class AnalysisResult:
    def __init__(self, candidate: Candidate, events: list[str]):
        self.candidate, self.events = candidate, events


class SwitchAdapter(Protocol):
    def analyze(self, ticket: TicketRead, base_sha: str) -> AnalysisResult: ...


class MockSwitchAdapter:
    """Deterministic demo fixture. This is not AI analysis."""

    def __init__(self, path="app.py"):
        self.path = path

    def analyze(self, ticket, base_sha):
        return AnalysisResult(
            Candidate(
                base_sha=base_sha,
                summary="Correct addition: return the sum instead of the difference.",
                files=[
                    FileChange(
                        path=self.path, content="def add(a, b):\n    return a + b\n"
                    )
                ],
            ),
            [
                "Mock investigation started; no real agents called.",
                "Demo arithmetic regression identified; candidate ready.",
            ],
        )
