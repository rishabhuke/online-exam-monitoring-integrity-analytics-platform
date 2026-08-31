"""
Test runner wrapper (Milestone 5).

Why this exists: onnxruntime (a transitive dependency of insightface,
added for face identity verification) registers an atexit cleanup hook
for its internal thread pool. On this macOS/Python 3.13 combination, that
cleanup crashes with a native libc++abi abort ("recursive_mutex lock
failed") whenever the process's stdout/stderr is not an interactive TTY
(i.e. whenever output is redirected to a file or piped) - which is exactly
how CI and most local test runs work. The crash happens strictly *after*
pytest has already finished running and reporting results, so it does not
affect test correctness or the pass/fail count - only the process's exit
code (134/SIGABRT instead of 0), which would otherwise cause CI or any
script checking $? to falsely report failure.

Fix: skip Python's normal interpreter teardown (which is where onnxruntime's
crashing cleanup runs) via os._exit() immediately after pytest reports its
result, using pytest's own real exit code.

Usage:
    python3 scripts/run_tests.py [any pytest args, e.g. -k identity -v]
"""

import os
import sys

import pytest

if __name__ == "__main__":
    exit_code = pytest.main(sys.argv[1:] or ["-q"])
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exit_code)
