"""Execute model-emitted Python checks in a constrained subprocess.

The model emits code that *computes* the answer and assigns the matching option
index to a variable `correct_index` (0-3). We run it isolated and read that
value back, then compare to the stated key.

Threat model: this runs our own LLM's code, not adversarial user input. The
sandbox is defense-in-depth, not a hard jail — isolated interpreter (`-I`, no
env/user-site), CPU + address-space rlimits, wall-clock timeout, no stdin. For
untrusted code you would add nsjail/containers; that's out of scope here.
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass

try:
    import resource  # POSIX only
except ImportError:  # pragma: no cover - non-POSIX
    resource = None  # type: ignore[assignment]

RESULT_MARKER = "__AURORA_RESULT__="
DEFAULT_TIMEOUT = 5
_MEM_LIMIT_BYTES = 512 * 1024 * 1024  # 512 MB address space
_CPU_LIMIT_SECONDS = 5


@dataclass
class SandboxResult:
    ok: bool  # ran cleanly and produced an integer
    value: int | None  # the computed correct index, if any
    timed_out: bool = False
    error: str | None = None


def _wrap(code: str) -> str:
    return (
        f"{code}\n\n"
        f"print('{RESULT_MARKER}' + str(int(correct_index)))\n"
    )


def _set_limits() -> None:  # pragma: no cover - runs in child process
    if resource is None:
        return
    resource.setrlimit(resource.RLIMIT_CPU, (_CPU_LIMIT_SECONDS, _CPU_LIMIT_SECONDS))
    try:
        resource.setrlimit(resource.RLIMIT_AS, (_MEM_LIMIT_BYTES, _MEM_LIMIT_BYTES))
    except (ValueError, OSError):
        pass


def run_check(code: str, *, timeout: int = DEFAULT_TIMEOUT) -> SandboxResult:
    """Run `code` and return the `correct_index` it computes."""
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-c", _wrap(code)],
            capture_output=True,
            text=True,
            timeout=timeout,
            stdin=subprocess.DEVNULL,
            preexec_fn=_set_limits if resource is not None else None,
            env={"PYTHONHASHSEED": "0"},
        )
    except subprocess.TimeoutExpired:
        return SandboxResult(ok=False, value=None, timed_out=True, error="timeout")

    if proc.returncode != 0:
        return SandboxResult(
            ok=False, value=None, error=(proc.stderr or "nonzero exit").strip()[-500:]
        )

    for line in reversed(proc.stdout.splitlines()):
        if line.startswith(RESULT_MARKER):
            try:
                return SandboxResult(ok=True, value=int(line[len(RESULT_MARKER):]))
            except ValueError:
                return SandboxResult(ok=False, value=None, error="non-integer result")

    return SandboxResult(ok=False, value=None, error="no result emitted")
