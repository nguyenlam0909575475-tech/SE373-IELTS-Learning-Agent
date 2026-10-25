"""Optional OpenAI-compatible examiner, configured for Groq by default."""

import json
import os
from pathlib import Path
from typing import Annotated, Any, Literal, NoReturn, Self
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, ValidationError, model_validator

from .contracts import (
    DependencyFailure,
    DraftGenerationFailure,
    ErrorCode,
    ExaminerInput,
    ExaminerUsage,
    LLMGradingDraft,
)
from .prompts import SYSTEM_INSTRUCTION, build_examiner_payload
from .provider_errors import safe_provider_diagnostics
from .schemas import PublicModel


class OpenAICompatibleSettings(PublicModel):
    api_key: Annotated[SecretStr, Field(min_length=1)]
    model: Annotated[str, Field(pattern=r"^[A-Za-z0-9_./:-]{1,100}$")] = "openai/gpt-oss-20b"
    base_url: str = "https://api.groq.com/openai/v1"
    response_format: Literal["json_object", "json_schema"] = "json_object"
    timeout_ms: int = Field(default=45000, ge=1000, le=120000)
    max_output_tokens: int = Field(default=4096, ge=512, le=16384)

    @model_validator(mode="after")
    def valid_configuration(self) -> Self:
        url = urlsplit(self.base_url)
        if (
            not self.api_key.get_secret_value().strip()
            or url.scheme != "https"
            or not url.hostname
            or url.username
            or url.password
            or url.query
            or url.fragment
        ):
            raise ValueError("explicit key and HTTPS API base URL required")
        return self

    @property
    def trace_model_version(self) -> str:
        return self.model.replace("/", "_")


def load_openai_settings(dotenv_path: Path | None = None) -> OpenAICompatibleSettings:
    try:
        from dotenv import dotenv_values

        values = dotenv_values(dotenv_path, interpolate=False) if dotenv_path else {}

        def setting(name: str, default: Any = None) -> Any:
            return os.environ.get(name, values.get(name, default))

        return OpenAICompatibleSettings(
            api_key=setting("OPENAI_API_KEY") or setting("GROQ_API_KEY"),
            model=setting("OPENAI_MODEL", "openai/gpt-oss-20b"),
            base_url=setting("OPENAI_BASE_URL", "https://api.groq.com/openai/v1"),
            response_format=setting("OPENAI_RESPONSE_FORMAT", "json_object"),
            timeout_ms=setting("OPENAI_TIMEOUT_MS", 45000),
            max_output_tokens=setting("OPENAI_MAX_OUTPUT_TOKENS", 4096),
        )
    except (ImportError, OSError, ValidationError, ValueError):
        raise DependencyFailure(ErrorCode.LLM_CONFIGURATION_ERROR) from None


class OpenAICompatibleExaminer:
    def __init__(self, settings: OpenAICompatibleSettings, *, client: Any = None):
        self.settings = settings
        self.last_usage: ExaminerUsage | None = None
        self._owns_client = client is None
        if client is not None:
            self._client = client
        else:
            try:
                from openai import OpenAI

                self._client = OpenAI(
                    api_key=settings.api_key.get_secret_value(),
                    base_url=settings.base_url,
                    timeout=settings.timeout_ms / 1000,
                    max_retries=0,
                )
            except Exception:
                raise DependencyFailure(ErrorCode.LLM_CONFIGURATION_ERROR) from None

    def generate(self, data: ExaminerInput) -> LLMGradingDraft:
        self.last_usage = None
        payload = json.loads(build_examiner_payload(data))
        payload["response_schema"] = LLMGradingDraft.model_json_schema()
        output_format: dict[str, Any] = {"type": "json_object"}
        if self.settings.response_format == "json_schema":
            output_format = {
                "type": "json_schema",
                "json_schema": {
                    "name": "writing_grading_draft",
                    "strict": True,
                    "schema": LLMGradingDraft.model_json_schema(),
                },
            }
        try:
            response = self._client.chat.completions.create(
                model=self.settings.model,
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTION},
                    {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
                ],
                response_format=output_format,
                max_completion_tokens=self.settings.max_output_tokens,
                temperature=0,
            )
        except Exception as exc:
            self._raise_provider_failure(exc)
        usage = getattr(response, "usage", None)
        if usage is not None:
            try:
                self.last_usage = ExaminerUsage(
                    input_tokens=usage.prompt_tokens, output_tokens=usage.completion_tokens
                )
            except (AttributeError, ValidationError):
                pass
        choices = getattr(response, "choices", None) or []
        if not choices:
            raise DependencyFailure(ErrorCode.LLM_EMPTY_RESPONSE)
        choice = choices[0]
        if choice.finish_reason == "length":
            raise DependencyFailure(ErrorCode.LLM_RESPONSE_INCOMPLETE)
        if choice.finish_reason == "content_filter" or getattr(choice.message, "refusal", None):
            raise DependencyFailure(ErrorCode.LLM_RESPONSE_BLOCKED)
        text = choice.message.content
        if not isinstance(text, str) or not text.strip():
            raise DependencyFailure(ErrorCode.LLM_EMPTY_RESPONSE)
        return LLMGradingDraft.model_validate_json(text)

    @staticmethod
    def _raise_provider_failure(exc: Exception) -> NoReturn:
        import httpx
        from openai import APIConnectionError, APITimeoutError

        if isinstance(exc, (httpx.TimeoutException, APITimeoutError, TimeoutError)):
            code = ErrorCode.LLM_TIMEOUT
            diagnostics = safe_provider_diagnostics(exc, failure_kind="timeout")
        elif isinstance(exc, APIConnectionError):
            code = ErrorCode.LLM_REQUEST_FAILED
            diagnostics = safe_provider_diagnostics(exc, failure_kind="connection")
        else:
            diagnostics = safe_provider_diagnostics(exc)
            status = diagnostics.http_status
            if status == 400 and diagnostics.provider_code == "json_validate_failed":
                diagnostics.failure_kind = "invalid_output"
                raise DraftGenerationFailure(diagnostics) from None
            if status is None:
                diagnostics.failure_kind = "unknown"
            code = (
                {
                    401: ErrorCode.LLM_AUTH_ERROR,
                    403: ErrorCode.LLM_AUTH_ERROR,
                    404: ErrorCode.LLM_MODEL_UNAVAILABLE,
                    429: ErrorCode.LLM_RATE_LIMITED,
                }.get(status, ErrorCode.LLM_REQUEST_FAILED)
                if isinstance(status, int)
                else ErrorCode.LLM_REQUEST_FAILED
            )
        raise DependencyFailure(code, diagnostics=diagnostics) from None

    def close(self) -> None:
        if self._owns_client:
            try:
                self._client.close()
            except Exception:
                pass
