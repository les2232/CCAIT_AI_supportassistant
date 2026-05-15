#!/usr/bin/env python3
import os
import subprocess
import sys


CHECKS = [
    ("Knowledge Base Validation", ["./venv/bin/python", "scripts/validate_kb.py"]),
    ("Logging Privacy Evaluation", ["./venv/bin/python", "evaluations/evaluate_logging_privacy.py"]),
    ("Phase 1 Production Readiness Evaluation", ["./venv/bin/python", "evaluations/evaluate_phase1_production.py"]),
    ("Security Controls Evaluation", ["./venv/bin/python", "evaluations/evaluate_security_controls.py"]),
    ("KB Scope Evaluation", ["./venv/bin/python", "evaluations/evaluate_kb_scope.py"]),
    ("Agent Service Evaluation", ["./venv/bin/python", "evaluations/evaluate_agent_service.py"]),
    ("Disambiguation Evaluation", ["./venv/bin/python", "evaluations/evaluate_disambiguation.py"]),
    ("Routing Evaluation", ["./venv/bin/python", "evaluations/evaluate_routing.py", "--strict"]),
    ("Retrieval Evaluation", ["./venv/bin/python", "evaluations/evaluate_retrieval.py", "--strict"]),
    ("Rendered Response Evaluation", ["./venv/bin/python", "evaluations/evaluate_rendered_responses.py"]),
]

DETERMINISTIC_ENV_OVERRIDES = {
    "IT_SUPPORT_LOCAL_ONLY": "1",
    "OPENAI_API_KEY": "",
    "IT_SUPPORT_CLASSIFIER_ENABLED": "0",
    "IT_SUPPORT_LLM_ENABLED": "0",
    "IT_SUPPORT_EMBEDDINGS_ENABLED": "0",
    "ENABLE_REALTIME_SUPPORT": "0",
    "ENABLE_AGENTS": "0",
}


def run_check(title, command):
    print(title)
    print("=" * 72)
    env = os.environ.copy()
    env.update(DETERMINISTIC_ENV_OVERRIDES)
    result = subprocess.run(command, env=env)
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
