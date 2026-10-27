"""Gemini latency controls reach the SDK without hidden retries or real API calls."""

from types import SimpleNamespace

import httpx
import pytest

from src.agent.contracts import DependencyFailure, ErrorCode
from src.agent.gemini import GeminiExaminer, GeminiSettings, load_gemini_settings


def test_load_latency_controls_without_exposing_key(tmp_path, monkeypatch):
    for name in ("GEMINI_API_KEY", "GEMINI_MODEL", "GEMINI_TIMEOUT_MS",
                 "GEMINI_MAX_OUTPUT_TOKENS", "GEMINI_THINKING_LEVEL"):
        monkeypatch.delenv(name, raising=False)
    path = tmp_path / ".env"
    path.write_text(
        'GEMINI_API_KEY="synthetic-test-key"\nGEMINI_MODEL="gemini-3.8-flash"\n'
        'GEMINI_TIMEOUT_MS="120000"\nGEMINI_MAX_OUTPUT_TOKENS="16384"\n'
        'GEMINI_THINKING_LEVEL="low"\n', encoding="utf-8",
    )
    settings = load_gemini_settings(path)
    assert settings.timeout_ms == 120000
    assert settings.max_output_tokens == 16384
    assert settings.thinking_level == "low"
    assert "synthetic-test-key" not in repr(settings)
    monkeypatch.setenv("GEMINI_THINKING_LEVEL", "medium")
    assert load_gemini_settings(path).thinking_level == "medium"


@pytest.mark.parametrize("thinking_level", [None, "low", "minimal"])
def test_generation_sends_latency_controls_and_does_not_retry(monkeypatch, thinking_level):
    calls = []

    def generate_content(**kwargs):
        calls.append(kwargs)
        raise httpx.ReadTimeout("synthetic timeout")

    monkeypatch.setattr("src.agent.gemini.build_examiner_payload", lambda data: "{}")
    examiner = GeminiExaminer(
        GeminiSettings(api_key="synthetic-test-key", model="gemini-3.8-flash",
                       max_output_tokens=16384, thinking_level=thinking_level),
        client=SimpleNamespace(models=SimpleNamespace(generate_content=generate_content)),
    )
    with pytest.raises(DependencyFailure) as failure:
        examiner.generate(None)
    assert failure.value.code == ErrorCode.LLM_TIMEOUT
    assert len(calls) == 1
    config = calls[0]["config"]
    assert config.max_output_tokens == 16384
    assert config.response_mime_type == "application/json"
    if thinking_level is None:
        assert config.thinking_config is None
    else:
        assert config.thinking_config.thinking_level.value == thinking_level.upper()


@pytest.mark.parametrize("status", [408, 504])
def test_provider_deadline_is_reported_as_timeout(status):
    class ProviderDeadline(Exception):
        code = status

    with pytest.raises(DependencyFailure) as failure:
        GeminiExaminer._raise_provider_failure(ProviderDeadline())
    assert failure.value.code == ErrorCode.LLM_TIMEOUT
