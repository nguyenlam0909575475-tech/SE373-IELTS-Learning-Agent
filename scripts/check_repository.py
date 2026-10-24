"""Reject generated/private files and common secret patterns in Git content.

Default: check tracked and non-ignored untracked files on disk.
--staged: check the Git index, including files added with git add -f.
--history: check all commits reachable from local refs, including deleted files.
Findings contain paths and line numbers, never matching secret values.
"""

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

GENERATED_DIRS = {
    "__pycache__", ".pytest_cache", ".uv-cache", ".venv", "venv",
    ".ruff_cache", ".mypy_cache", ".tox", ".nox", ".ipynb_checkpoints",
    "node_modules", ".next", ".idea", ".vscode", "htmlcov",
}
PRIVATE_PREFIXES = (
    "data/private/", "data/chroma_db/", "traces/raw/", "logs/",
    "secrets/", ".secrets/",
)
BLOCKED_SUFFIXES = (
    ".pyc", ".pyo", ".pyd", ".log", ".db", ".sqlite", ".sqlite3",
    ".db-journal", ".db-wal", ".db-shm", ".sqlite-wal", ".sqlite-shm",
    ".sqlite3-wal", ".sqlite3-shm", ".pem", ".key", ".p12", ".pfx",
    ".swp", ".swo", ".bak", ".tmp", "~",
)
TOKEN_PATTERN = re.compile(
    r"\b(?:sk-[A-Za-z0-9_-]{20,}|AIza[A-Za-z0-9_-]{30,}|"
    r"(?:gh[pousr]_|github_pat_)[A-Za-z0-9_]{20,}|"
    r"(?:AKIA|ASIA)[A-Z0-9]{16}|hf_[A-Za-z0-9]{30,}|"
    r"xox[baprs]-[A-Za-z0-9-]{20,})\b"
)
PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"
)
_CREDENTIAL_NAME = r"[A-Z0-9_]*(?:API_KEY|API_TOKEN|ACCESS_TOKEN|SECRET_KEY|CLIENT_SECRET|PASSWORD)"
ASSIGNMENT_PATTERN = re.compile(
    r'''(?im)^[ \t]*(?:export[ \t]+)?(?:const[ \t]+|let[ \t]+|var[ \t]+)?'''
    + rf'''(?:["']{_CREDENTIAL_NAME}["']|{_CREDENTIAL_NAME})'''
    + r'''[ \t]*[:=][ \t]*(?:["']([^\r\n"']*)["']|([^\s"'#;,]+))'''
)
PLACEHOLDERS = {"", "none", "null", "placeholder", "changeme", "your_api_key_here"}


@dataclass(frozen=True)
class Finding:
    path: str
    reason: str
    line: int | None = None


def blocked_path(path: str) -> bool:
    """Check names independently of .gitignore to catch forced additions."""
    normalized = path.replace("\\", "/").lower()
    parts = PurePosixPath(normalized).parts
    name = parts[-1]
    return (
        any(part in GENERATED_DIRS or part.endswith(".egg-info") for part in parts[:-1])
        or any(part in {"secrets", ".secrets"} for part in parts[:-1])
        or parts[0] in {"build", "dist"}
        # Historical setup instructions are documentation, not a generated DB.
        # Their contents still pass through the secret scanner below.
        or (normalized.startswith(PRIVATE_PREFIXES) and normalized != "data/chroma_db/readme.md")
        or name == ".env"
        or (name.startswith(".env.") and name != ".env.example")
        or name in {"credentials.json", ".ds_store", "thumbs.db", "desktop.ini", ".coverage", "coverage.xml"}
        or name.startswith(("client_secret", "service-account", "~$", ".coverage."))
        or name.endswith(BLOCKED_SUFFIXES)
    )


def scan_text(path: str, content: str) -> list[Finding]:
    findings = []
    for pattern, reason in (
        (TOKEN_PATTERN, "possible provider token"),
        (PRIVATE_KEY_PATTERN, "private key material"),
    ):
        for match in pattern.finditer(content):
            findings.append(Finding(path, reason, content.count("\n", 0, match.start()) + 1))
    for match in ASSIGNMENT_PATTERN.finditer(content):
        value = match.group(1) if match.group(1) is not None else match.group(2)
        if value.lower() in PLACEHOLDERS or value.startswith(("your_", "your-", "<", "${")):
            continue
        # Environment lookups and function calls are not hardcoded credentials.
        if match.group(1) is None and any(char in value for char in "(["):
            continue
        findings.append(Finding(path, "hardcoded credential value", content.count("\n", 0, match.start()) + 1))
    return findings


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(root), *args], check=True, capture_output=True
    ).stdout


def git_paths(data: bytes) -> list[str]:
    return [path for path in data.decode("utf-8").split("\0") if path]


def inspect(root: Path, mode: str) -> tuple[list[Finding], int]:
    findings = []
    checked = 0
    snapshots = git(root, "rev-list", "--all").decode().splitlines() if mode == "history" else [None]
    # The same blob may appear in many commits; inspect each path/blob pair once.
    seen = set()
    for revision in snapshots:
        if revision is not None:
            tree_blobs = {}
            for record in git(root, "ls-tree", "-rz", revision).split(b"\0"):
                if record:
                    metadata, path = record.split(b"\t", 1)
                    tree_blobs[path.decode("utf-8")] = metadata.split()[2]
            paths = list(tree_blobs)
        elif mode == "staged":
            paths = git_paths(git(root, "ls-files", "-z", "--cached"))
        else:
            paths = git_paths(git(root, "ls-files", "-z", "--cached", "--others", "--exclude-standard"))
        for path in sorted(set(paths)):
            label = f"{revision[:8]}:{path}" if revision is not None else path
            if blocked_path(path):
                findings.append(Finding(label, "generated or private file must not be committed"))
                continue
            if revision is not None or mode == "staged":
                spec = f"{revision}:{path}" if revision is not None else f":{path}"
                blob_id = tree_blobs[path] if revision is not None else git(root, "rev-parse", spec).strip()
                identity = (path, blob_id)
                if identity in seen:
                    continue
                seen.add(identity)
                content = git(root, "show", spec)
            else:
                candidate = root / path
                if candidate.is_symlink():
                    findings.append(Finding(label, "review symbolic link before committing"))
                    continue
                if not candidate.is_file():
                    continue
                content = candidate.read_bytes()
            checked += 1
            if b"\0" not in content:
                findings.extend(scan_text(label, content.decode("utf-8", errors="replace")))
    return findings, checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--staged", action="store_true")
    group.add_argument("--history", action="store_true")
    args = parser.parse_args()
    mode = "staged" if args.staged else "history" if args.history else "worktree"
    try:
        root = Path(subprocess.run(
            ["git", "rev-parse", "--show-toplevel"], check=True,
            capture_output=True, text=True, encoding="utf-8",
        ).stdout.strip())
        findings, checked = inspect(root, mode)
    except (OSError, subprocess.CalledProcessError, UnicodeError):
        print("Repository check could not finish. Resolve the Git/file error before continuing.", file=sys.stderr)
        return 2
    if findings:
        for finding in findings:
            location = f"{finding.path}:{finding.line}" if finding.line else finding.path
            print(f"BLOCKED {location!r}: {finding.reason} (content redacted)", file=sys.stderr)
        return 1
    print(f"Repository check passed: {checked} file version(s), mode={mode}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
