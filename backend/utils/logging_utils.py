"""Structured logging with automatic secret redaction."""

import logging
import re
from typing import Iterable


_SECRET_PATTERNS: Iterable[re.Pattern[str]] = (
    re.compile(r"(Bearer\s+)[A-Za-z0-9._\-]+", re.IGNORECASE),
    re.compile(r"((?:api[-_]?key|api[-_]?subscription[-_]?key|token|secret|password|appid)\s*[=:]\s*)[^\s&,\"']+", re.IGNORECASE),
)


class SecretRedactionFilter(logging.Filter):
    """Masks bearer tokens, query API keys, and sensitive credentials in log lines."""

    def __init__(self, explicit_secrets: Iterable[str] = ()):
        super().__init__()
        self._explicit = [s for s in explicit_secrets if s and len(s) >= 6]

    def _redact(self, value: str) -> str:
        masked = value
        for secret in self._explicit:
            if secret in masked:
                masked = masked.replace(secret, "***REDACTED***")
        for pattern in _SECRET_PATTERNS:
            masked = pattern.sub(r"\1***REDACTED***", masked)
        return masked

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._redact(record.msg)
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    self._redact(a) if isinstance(a, str) else a for a in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    k: self._redact(v) if isinstance(v, str) else v
                    for k, v in record.args.items()
                }
        return True


def configure_logging(secrets_to_mask: Iterable[str] = ()) -> logging.Logger:
    """Configure root logger with redaction filter once."""
    root = logging.getLogger("raitha_mitra")
    if not root.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)
    root.setLevel(logging.INFO)
    redactor = SecretRedactionFilter(secrets_to_mask)
    for handler in root.handlers:
        if not any(isinstance(f, SecretRedactionFilter) for f in handler.filters):
            handler.addFilter(redactor)
    return root
