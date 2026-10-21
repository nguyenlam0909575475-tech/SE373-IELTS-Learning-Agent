"""Verify staged/history checks using disposable repositories and fake values."""

import subprocess
import sys
from pathlib import Path

import pytest

from scripts.check_repository import blocked_path, scan_text

CHECK_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "check_repository.py"


@pytest.mark.parametrize("path", [
    ".env", "config/.env.local", "src/__pycache__/word_counter.pyc",
    ".venv/pyvenv.cfg", ".pytest_cache/README.md", "data/private/essay.json",
    "data/chroma_db/chroma.sqlite3", "traces/raw/run.jsonl", "logs/run.jsonl",
    "credentials.json", "private.pem", "dist/app.js", "node_modules/pkg/index.js",
    "data/private/README.md",
])
def test_block_generated_and_private_paths(path: str) -> None:
    assert blocked_path(path)


@pytest.mark.parametrize("path", [
    ".env.example", "src/__init__.py", "src/tools/__init__.py", "uv.lock",
    "docs/data_sources.md", "data/bank/README.md", "traces/samples/README.md",
    "data/chroma_db/README.md",
])
def test_allow_source_templates_and_documentation(path: str) -> None:
    assert not blocked_path(path)


def test_detect_provider_token_without_reporting_value() -> None:
    fake_token = "sk-" + "FAKE" * 10
    findings = scan_text("example.py", f'client = Client("{fake_token}")')
    assert findings
    assert fake_token not in repr(findings)


def test_detect_generic_hardcoded_credential() -> None:
    assert scan_text("config.py", 'API_KEY = "a-fake-value-for-testing"')


@pytest.mark.parametrize("content", [
    "OPENAI_API_KEY=\n",
    'API_KEY = os.getenv("OPENAI_API_KEY")',
    'API_KEY = "your_api_key_here"',
    'OPENAI_API_KEY=your-openai-key-here',
    "LANGCHAIN_TRACING_V2=false",
    '"OPENAI_API_KEY=\\n",',
])
def test_allow_empty_templates_and_environment_lookups(content: str) -> None:
    assert scan_text("example.py", content) == []


@pytest.fixture
def disposable_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True, capture_output=True)
    return tmp_path


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def run_check(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-B", str(CHECK_SCRIPT), *args], cwd=repo,
        text=True, encoding="utf-8", capture_output=True, check=False,
    )


def test_staged_check_reads_index_instead_of_clean_worktree(disposable_repo: Path) -> None:
    target = disposable_repo / "config.py"
    fake_token = "sk-" + "FAKE" * 10
    target.write_text(f'client = Client("{fake_token}")', encoding="utf-8")
    run_git(disposable_repo, "add", "config.py")
    target.write_text("# Clean working copy, but the staged copy still has a token.\n", encoding="utf-8")
    result = run_check(disposable_repo, "--staged")
    assert result.returncode == 1
    assert fake_token not in result.stdout + result.stderr


def test_forced_add_of_ignored_env_is_blocked(disposable_repo: Path) -> None:
    (disposable_repo / ".gitignore").write_text(".env\n", encoding="utf-8")
    (disposable_repo / ".env").write_text("# Fake local config\n", encoding="utf-8")
    run_git(disposable_repo, "add", "-f", ".env")
    assert run_check(disposable_repo, "--staged").returncode == 1


def test_history_detects_secret_removed_in_later_commit(disposable_repo: Path) -> None:
    target = disposable_repo / "config.py"
    fake_token = "sk-" + "FAKE" * 10
    target.write_text(f'client = Client("{fake_token}")', encoding="utf-8")
    run_git(disposable_repo, "add", "config.py")
    identity = ("-c", "user.name=Repository Check Test", "-c", "user.email=test@example.invalid")
    run_git(disposable_repo, *identity, "commit", "-q", "-m", "Synthetic fixture")
    target.write_text("# Token removed from the latest version.\n", encoding="utf-8")
    run_git(disposable_repo, "add", "config.py")
    run_git(disposable_repo, *identity, "commit", "-q", "-m", "Clean fixture")
    result = run_check(disposable_repo, "--history")
    assert result.returncode == 1
    assert fake_token not in result.stdout + result.stderr
