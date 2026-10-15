"""Truthful, short-lived verification evidence; configuration is not connectivity."""
import hashlib
import os
import time
from dataclasses import dataclass
from threading import RLock
from typing import Literal

ProviderState = Literal[
    "NOT_CONFIGURED", "CONFIGURED", "VERIFICATION_PENDING",
    "VERIFIED_CONNECTED", "UNAVAILABLE", "ERROR",
]


@dataclass(frozen=True)
class Verification:
    fingerprint: str
    state: ProviderState
    expires_at: float


_records: dict[str, Verification] = {}
_lock = RLock()
VERIFICATION_TTL_SECONDS = 300


def _fingerprint(keys):
    # Kept only in process, never returned or logged. Credential rotation invalidates evidence.
    return hashlib.sha256("\0".join(os.getenv(key, "") for key in keys).encode()).hexdigest()


def record_verification(key, credential_keys, state: ProviderState, *, successful=False):
    if state == "VERIFIED_CONNECTED" and not successful:
        raise ValueError("Successful provider evidence is required")
    if state not in ("VERIFICATION_PENDING", "VERIFIED_CONNECTED", "ERROR", "UNAVAILABLE"):
        raise ValueError("Unsupported verification outcome")
    with _lock:
        _records[key] = Verification(
            _fingerprint(credential_keys), state, time.monotonic() + VERIFICATION_TTL_SECONDS,
        )


def status(key, credential_keys):
    missing = [name for name in credential_keys if not os.getenv(name)]
    if missing:
        return {"state": "NOT_CONFIGURED", "missing": missing, "verified": False,
                "legacy_state": "NEEDS_CONNECTION"}
    with _lock:
        record = _records.get(key)
        valid = record and record.expires_at > time.monotonic() and record.fingerprint == _fingerprint(credential_keys)
        state = record.state if valid else "CONFIGURED"
    return {"state": state, "missing": [], "verified": state == "VERIFIED_CONNECTED",
            "legacy_state": "CONNECTED" if state == "VERIFIED_CONNECTED" else "NEEDS_CONNECTION"}
