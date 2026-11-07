"""GitHub REST implementation. No merge operation is exposed."""

import base64
import time
from pathlib import PurePosixPath
from urllib.parse import quote

import httpx

from ..schemas import Candidate


class IntegrationError(Exception):
    pass


class GitHubService:
    def __init__(self, token, client=None):
        self.token = token
        self.client = client or httpx.Client(timeout=20)

    def request(self, method, path, *, missing_ok=False, **kwargs):
        if not self.token:
            raise IntegrationError("GITHUB_TOKEN is not configured")
        try:
            response = self.client.request(
                method,
                "https://api.github.com" + path,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                **kwargs,
            )
        except httpx.HTTPError:
            raise IntegrationError("GitHub request failed or timed out") from None
        if missing_ok and response.status_code == 404:
            return None
        if response.status_code >= 300:
            raise IntegrationError(f"GitHub API returned HTTP {response.status_code}")
        return response.json()

    def branch_sha(self, repository, branch):
        result = self.request(
            "GET", f"/repos/{repository}/branches/{quote(branch, safe='')}"
        )
        return result["commit"]["sha"]

    def read_file(self, repository, path, sha):
        result = self.request(
            "GET",
            f"/repos/{repository}/contents/{quote(path, safe='/')}",
            params={"ref": sha},
        )
        if result.get("type") != "file" or result.get("encoding") != "base64":
            raise IntegrationError("Candidate source is not a supported regular file")
        try:
            return base64.b64decode(result["content"]).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            raise IntegrationError("Candidate source must be UTF-8") from None

    def snapshot(self, repository, sha, timeout=20, root=""):
        deadline = time.monotonic() + timeout

        def bounded_get(path, **kwargs):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise IntegrationError("Snapshot deadline exceeded")
            return self.request("GET", path, timeout=remaining, **kwargs)

        tree = bounded_get(
            f"/repos/{repository}/git/trees/{sha}", params={"recursive": "1"}
        )
        if tree.get("truncated") or len(tree["tree"]) > 2000:
            raise IntegrationError("Repository exceeds MVP snapshot limit")
        files, total = {}, 0
        for entry in tree["tree"]:
            path = entry["path"]
            if root and not path.startswith(root + "/"):
                continue
            pure = PurePosixPath(path)
            if (
                pure.is_absolute()
                or ".." in pure.parts
                or "\\" in path
                or str(pure) != path
            ):
                raise IntegrationError("Unsafe repository path")
            if entry.get("mode") in ("120000", "160000"):
                raise IntegrationError(
                    "Symlinks and submodules are unsupported by verification"
                )
            if pure.name in (
                "pytest.ini",
                ".pytest.ini",
                "pyproject.toml",
                "setup.cfg",
                "tox.ini",
            ):
                raise IntegrationError(
                    "Custom test configuration is unsupported; use a standalone Python demo directory"
                )
            if len(files) >= 100:
                raise IntegrationError("Snapshot exceeds 100 Python files")
            # MVP verifier supports dependency-free Python repositories only.
            if entry["type"] != "blob" or not path.endswith(".py"):
                continue
            total += entry.get("size", 0)
            if total > 2_000_000:
                raise IntegrationError("Python snapshot exceeds 2 MB limit")
            blob = bounded_get(f"/repos/{repository}/git/blobs/{entry['sha']}")
            data = base64.b64decode(blob["content"])
            if len(data) > 200_000:
                raise IntegrationError("Source file exceeds 200 KB limit")
            files[path] = data
        if not files:
            raise IntegrationError("Repository contains no Python source")
        return files

    def publish(self, ticket, patch: Candidate):
        repo, base = ticket.repository, patch.base_sha
        if self.branch_sha(repo, ticket.branch) != base:
            raise IntegrationError(
                "Base branch changed; create a new ticket and analyze again"
            )
        branch = f"fix/{ticket.ticket_id}-{patch.digest()[:16]}"
        prefix = f"/repos/{repo}"
        existing = self.request(
            "GET",
            prefix + "/pulls",
            params={
                "state": "all",
                "head": repo.split("/")[0] + ":" + branch,
                "base": ticket.branch,
            },
        )
        if existing:
            pr = existing[0]
            head = pr["head"]["sha"]
            self._validate_commit(repo, head, patch)
            return {
                "url": pr["html_url"],
                "number": pr["number"],
                "head_sha": head,
                "branch": branch,
            }
        ref = self.request(
            "GET", prefix + "/git/ref/heads/" + quote(branch, safe=""), missing_ok=True
        )
        if ref:
            head = ref["object"]["sha"]
            self._validate_commit(repo, head, patch)
        else:
            tree = self._candidate_tree(repo, patch)
            commit = self.request(
                "POST",
                prefix + "/git/commits",
                json={
                    "message": f"{ticket.ticket_id}: {patch.summary}",
                    "tree": tree["sha"],
                    "parents": [base],
                },
            )
            head = commit["sha"]
            self.request(
                "POST",
                prefix + "/git/refs",
                json={"ref": "refs/heads/" + branch, "sha": head},
            )
        # Fail safely if base moved during publication. The branch may exist for retry/inspection.
        if self.branch_sha(repo, ticket.branch) != base:
            raise IntegrationError(
                "Base branch changed during publication; PR not created"
            )
        pr = self.request(
            "POST",
            prefix + "/pulls",
            json={
                "title": f"[{ticket.ticket_id}] {ticket.title}",
                "head": branch,
                "base": ticket.branch,
                "body": f"{patch.summary}\n\nHuman-approved patch: `{patch.digest()}`\nBase: `{base}`\nVerification passed in isolated Docker.\n\nNo automatic merge.",
                "draft": True,
            },
        )
        actual_head = pr.get("head", {}).get("sha")
        if actual_head != head:
            self.request(
                "PATCH",
                prefix + "/pulls/" + str(pr["number"]),
                json={"state": "closed"},
            )
            raise IntegrationError(
                "PR head changed during publication; draft was closed"
            )
        return {
            "url": pr["html_url"],
            "number": pr["number"],
            "head_sha": actual_head,
            "branch": branch,
        }

    def _candidate_tree(self, repository, patch):
        prefix = f"/repos/{repository}"
        base_commit = self.request("GET", prefix + "/git/commits/" + patch.base_sha)
        base_tree = base_commit["tree"]["sha"]
        tree = self.request(
            "GET", prefix + "/git/trees/" + base_tree, params={"recursive": "1"}
        )
        if tree.get("truncated"):
            raise IntegrationError("Base tree is too large to validate")
        entries = {entry["path"]: entry for entry in tree["tree"]}
        changes = []
        for f in patch.files:
            entry = entries.get(f.path, {})
            if entry.get("type") != "blob" or entry.get("mode") not in (
                "100644",
                "100755",
            ):
                raise IntegrationError(
                    "Candidate may only replace existing regular Python files"
                )
            changes.append(
                {
                    "path": f.path,
                    "mode": entry["mode"],
                    "type": "blob",
                    "content": f.content,
                }
            )
        return self.request(
            "POST",
            prefix + "/git/trees",
            json={"base_tree": base_tree, "tree": changes},
        )

    def _validate_commit(self, repository, head, patch):
        commit = self.request("GET", f"/repos/{repository}/git/commits/{head}")
        if [p["sha"] for p in commit.get("parents", [])] != [patch.base_sha]:
            raise IntegrationError(
                "Existing publication parent differs from approved base"
            )
        expected = self._candidate_tree(repository, patch)
        if commit["tree"]["sha"] != expected["sha"]:
            raise IntegrationError(
                "Existing publication tree differs from approved candidate"
            )
