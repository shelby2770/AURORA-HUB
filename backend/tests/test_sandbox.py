"""Phase 4: execution-verify sandbox."""
from __future__ import annotations

from app.verify.check import Verdict, verify_computable
from app.verify.sandbox import run_check


def test_runs_and_returns_value():
    res = run_check("correct_index = 2 + 0")
    assert res.ok
    assert res.value == 2


def test_computes_not_hardcodes():
    # FIFO page faults for a small reference string, then map to an option.
    code = """
frames, ref = [], [1, 2, 3, 1, 2, 4]
faults = 0
for p in ref:
    if p not in frames:
        faults += 1
        if len(frames) >= 3:
            frames.pop(0)
        frames.append(p)
options = [4, 5, 6, 7]
correct_index = options.index(faults)
"""
    res = run_check(code)
    assert res.ok
    assert res.value == 0  # FIFO yields 4 faults -> options.index(4) == 0


def test_missing_variable_is_error():
    res = run_check("x = 1")
    assert not res.ok
    assert res.value is None
    assert res.error


def test_timeout():
    res = run_check("while True:\n    pass", timeout=1)
    assert not res.ok
    assert res.timed_out


def test_verify_match_and_mismatch():
    verdict, res = verify_computable("correct_index = 2", claimed_index=2)
    assert verdict is Verdict.match

    verdict, res = verify_computable("correct_index = 0", claimed_index=2)
    assert verdict is Verdict.mismatch
    assert res.value == 0


def test_verify_unverifiable_paths():
    assert verify_computable(None, 1)[0] is Verdict.unverifiable
    assert verify_computable("", 1)[0] is Verdict.unverifiable
    assert verify_computable("raise ValueError('boom')", 1)[0] is Verdict.unverifiable
