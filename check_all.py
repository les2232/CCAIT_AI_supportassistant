#!/usr/bin/env python3
import subprocess
import sys


CHECKS = [
    ("Knowledge Base Validation", ["./venv/bin/python", "validate_kb.py"]),
    ("Logging Privacy Evaluation", ["./venv/bin/python", "evaluate_logging_privacy.py"]),
    ("Phase 1 Production Readiness Evaluation", ["./venv/bin/python", "evaluate_phase1_production.py"]),
    ("KB Scope Evaluation", ["./venv/bin/python", "evaluate_kb_scope.py"]),
    ("Agent Service Evaluation", ["./venv/bin/python", "evaluate_agent_service.py"]),
    ("Disambiguation Evaluation", ["./venv/bin/python", "evaluate_disambiguation.py"]),
    ("Routing Evaluation", ["./venv/bin/python", "evaluate_routing.py", "--strict"]),
    ("Retrieval Evaluation", ["./venv/bin/python", "evaluate_retrieval.py", "--strict"]),
    ("Rendered Response Evaluation", ["./venv/bin/python", "evaluate_rendered_responses.py"]),
]


def run_check(title, command):
    print(title)
    print("=" * 72)
    result = subprocess.run(command)
    print()
    return result.returncode


def main():
    for title, command in CHECKS:
        code = run_check(title, command)
        if code != 0:
            print(f"Check failed: {title}")
            sys.exit(1)

    print("All checks passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
