"""Optional Gemini examiner; importing this module never imports the SDK or calls APIs."""

import os
from pathlib import Path
from typing import Annotated, Any, NoReturn, Self

from pydantic import Field, SecretStr, ValidationError, model_validator

from .contracts import (
    DependencyFailure,
    ErrorCode,
    ExaminerInput,
    ExaminerUsage,
    Identifier,
    LLMGradingDraft,
)
from .prompts import SYSTEM_INSTRUCTION, build_examiner_payload
from .schemas import PublicModel


class GeminiSettings(PublicModel):
    api_key: Annotated[SecretStr, Field(min_length=1)]
    model: Identifier
    timeout_ms: int = Field(default=45000, ge=1000, le=120000)
    max_output_tokens: int = Field(default=4096, ge=512, le=16384)

    @model_validator(mode="after")
    def configured_values(self) -> Self:
        if not self.api_key.get_secret_value().strip() or not self.model.startswith("gemini-"):
            raise ValueError("explicit Gemini API key and model required")
        return self


def load_gemini_settings(dotenv_path: Path | None = None) -> GeminiSettings:
    """Read only the explicit dotenv path; environment takes precedence; no env mutation."""
    try:
        from dotenv import dotenv_values

        values = dotenv_values(dotenv_path, interpolate=False) if dotenv_path else {}

        def setting(name: str, default: Any = None) -> Any:
            return os.environ.get(name, values.get(name, default))

        return GeminiSettings(
            api_key=setting("GEMINI_API_KEY"),
            model=setting("GEMINI_MODEL"),
            timeout_ms=setting("GEMINI_TIMEOUT_MS", 45000),
            max_output_tokens=setting("GEMINI_MAX_OUTPUT_TOKENS", 4096),
        )
    except (ImportError, OSError, ValidationError):
        raise DependencyFailure(ErrorCode.LLM_CONFIGURATION_ERROR) from None


class GeminiExaminer:
    """One SDK generation per generate(), no hidden retries, no raw payload/response logging.

    A demo instance is used for one graph invocation at a time. Optional last_usage reports
    metadata for that call; do not share the same instance across concurrent invocations.
    """

    def __init__(self, settings: GeminiSettings, *, client: Any = None):
        self.settings = settings
        self.last_usage: ExaminerUsage | None = None
        self._owns_client = client is None
        self._client = client if client is not None else self._new_client()

    def _new_client(self) -> Any:
        try:
            from google import genai
            from google.genai import types

            return genai.Client(
                api_key=self.settings.api_key.get_secret_value(),
                vertexai=False,
                http_options=types.HttpOptions(
                    base_url="https://generativelanguage.googleapis.com",
                    timeout=self.settings.timeout_ms,
                    retry_options=types.HttpRetryOptions(attempts=1),
                ),
            )
        except Exception:
            raise DependencyFailure(ErrorCode.LLM_CONFIGURATION_ERROR) from None

    def generate(self, data: ExaminerInput) -> LLMGradingDraft:
        self.last_usage = None
        try:
            from google.genai import types

            result = self._client.models.generate_content(
                model=self.settings.model,
                contents=build_examiner_payload(data),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_json_schema=LLMGradingDraft.model_json_schema(),
                    temperature=0,
                    max_output_tokens=self.settings.max_output_tokens,
                ),
            )
        except Exception as exc:
            self._raise_provider_failure(exc)
        usage = getattr(result, "usage_metadata", None)
        if usage is not None:
            try:
                self.last_usage = ExaminerUsage(
                    input_tokens=usage.prompt_token_count,
                    output_tokens=usage.candidates_token_count,
                )
            except (AttributeError, ValidationError):
                self.last_usage = None  # Usage may be unavailable; never invent counts.
        candidates = getattr(result, "candidates", None) or []
        finish = str(getattr(candidates[0], "finish_reason", "")) if candidates else ""
        feedback = getattr(result, "prompt_feedback", None)
        block_reason = str(getattr(feedback, "block_reason", "")) if feedback else ""
        if any(
            code in finish for code in ("SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED", "SPII")
        ):
            raise DependencyFailure(ErrorCode.LLM_RESPONSE_BLOCKED)
        if block_reason and "UNSPECIFIED" not in block_reason and block_reason != "None":
            raise DependencyFailure(ErrorCode.LLM_RESPONSE_BLOCKED)
        if "MAX_TOKENS" in finish:
            raise DependencyFailure(ErrorCode.LLM_RESPONSE_INCOMPLETE)
        text = getattr(result, "text", None)
        if not isinstance(text, str) or not text.strip():
            raise DependencyFailure(ErrorCode.LLM_EMPTY_RESPONSE)
        # Preserve ValidationError for the existing bounded schema-repair branch.
        # Never print its input/errors or the raw response, which may contain private data.
        return LLMGradingDraft.model_validate_json(text)

    @staticmethod
    def _raise_provider_failure(exc: Exception) -> NoReturn:
        import httpx

        if isinstance(exc, (httpx.TimeoutException, TimeoutError)):
            code = ErrorCode.LLM_TIMEOUT
        else:
            status = getattr(exc, "code", None)
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
        raise DependencyFailure(code) from None

    def close(self) -> None:
        if self._owns_client:
            try:
                self._client.close()
            except Exception:
                # Cleanup must not leak raw SDK errors after an already sanitized result.
                pass
