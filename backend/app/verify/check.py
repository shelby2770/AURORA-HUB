"""Map a sandbox run against a claimed answer key to a verdict."""
from __future__ import annotations

from enum import Enum

from app.verify.sandbox import SandboxResult, run_check


class Verdict(str, Enum):
    match = "match"  # executed and agreed with the claimed key
    mismatch = "mismatch"  # executed and DISAGREED — flag / discard
    unverifiable = "unverifiable"  # could not run (error/timeout/no code)


def verify_computable(
    verification_code: str | None, claimed_index: int, *, timeout: int = 5
) -> tuple[Verdict, SandboxResult | None]:
    if not verification_code or not verification_code.strip():
        return Verdict.unverifiable, None
    result = run_check(verification_code, timeout=timeout)
    if not result.ok or result.value is None:
        return Verdict.unverifiable, result
    if result.value == claimed_index:
        return Verdict.match, result
    return Verdict.mismatch, result
