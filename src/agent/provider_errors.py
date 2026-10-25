"""Extract only bounded, allowlisted metadata from OpenAI-compatible provider exceptions."""

import re
from typing import cast, get_args

from .contracts import ProviderCode, ProviderDiagnostics, ProviderFailureKind


def safe_provider_diagnostics(
    exc: Exception, *, failure_kind: ProviderFailureKind = "http"
) -> ProviderDiagnostics:
    status = getattr(exc, "status_code", None)
    if type(status) is not int or not 100 <= status <= 599:
        status = None
    body = getattr(exc, "body", None)
    if isinstance(body, dict) and isinstance(body.get("error"), dict):
        body = body["error"]
    raw_code = (body.get("code") or body.get("type")) if isinstance(body, dict) else None
    code = (
        cast(ProviderCode, raw_code)
        if isinstance(raw_code, str) and raw_code in get_args(ProviderCode)
        else None
    )
    request_id = getattr(exc, "request_id", None)
    if not isinstance(request_id, str) or not re.fullmatch(r"req_[A-Za-z0-9-]{8,100}", request_id):
        request_id = None
    response = getattr(exc, "response", None)
    headers = getattr(response, "headers", {})
    raw_wait = headers.get("retry-after")
    retry_after = None
    if isinstance(raw_wait, str) and re.fullmatch(r"[0-9]{1,6}(?:\.[0-9]{1,6})?", raw_wait):
        seconds = float(raw_wait)
        if seconds <= 86400:
            retry_after = seconds
    return ProviderDiagnostics(
        http_status=status,
        provider_code=code,
        request_id=request_id,
        retry_after_seconds=retry_after,
        failure_kind=failure_kind,
    )
