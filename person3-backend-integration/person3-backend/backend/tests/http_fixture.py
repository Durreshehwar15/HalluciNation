"""Test-only HTTP composition. Never use this factory for deployment.

GitHub is a local fixture; Switch is MockSwitchAdapter; Docker and SQLite are real.
No network credentials or external GitHub calls are used.
"""

from pathlib import Path

from app.main import create_app
from app.services.docker_runner import DockerRunner
from app.services.switch_adapter import MockSwitchAdapter


class LocalGitHubFixture:
    base_sha = "a" * 40  # Fixture identifier, not an actual Git commit.

    def branch_sha(self, repository, branch):
        return self.base_sha

    def read_file(self, repository, path, sha):
        assert path == "app.py" and sha == self.base_sha
        return (Path(__file__).resolve().parents[2] / "demo-repo/app.py").read_text()

    def snapshot(self, repository, sha, **kwargs):
        assert sha == self.base_sha
        demo = Path(__file__).resolve().parents[2] / "demo-repo"
        return {
            "app.py": (demo / "app.py").read_bytes(),
            "tests/test_app.py": (demo / "tests/test_app.py").read_bytes(),
        }

    def publish(self, ticket, patch):
        return {
            "url": "https://example.invalid/MOCK-pull-request/1",
            "number": 1,
            "head_sha": "b" * 40,
            "branch": "fix/local-test-fixture",
        }


def create_test_app():
    github = LocalGitHubFixture()
    return create_app(
        github=github,
        runner=DockerRunner(github),
        switch=MockSwitchAdapter("app.py"),
        human_identity="test-fixture",
    )
