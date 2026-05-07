# AGENTS.md

## Project Identity

This repository is a retrieval-first internal IT support assistant for Community College of Aurora. It is not a general chatbot.

Approved local knowledge base files in `content/public/` and `content/internal/` are the source of truth. OpenAI-backed features are optional and secondary: query classification, answer polishing, and Realtime voice support only. Do not add behavior that invents policy, support procedures, URLs, contact details, institutional claims, or escalation instructions that are not grounded in the local KB.

Keep the product focused on a clean, pilot-ready support experience. Avoid broad abstractions, multi-agent conversation state, or platform rewrites unless explicitly requested.

## Architecture Overview

- `app.py` is the Flask entry point. It owns login/logout, session protection, the main question form, guided follow-up handling, feedback submission, and Realtime endpoints.
- `support_service.py` coordinates the retrieval-first question resolution flow.
- `retriever.py` performs primary heuristic section retrieval over public KB articles in `content/public/` and optional staff-only SOP retrieval from `content/internal/`.
- `semantic_retriever.py` is an optional conservative fallback when embeddings are enabled.
- `router.py` provides fallback article selection when direct section retrieval is not confident.
- `response_builder.py` turns retrieved KB content into guided UI data: summaries, context, steps, additional troubleshooting, escalation, and ticket-help text.
- `llm_answer.py` may polish retrieved text only when enabled. It must not become an independent answer source.
- `query_classifier.py` may use OpenAI for a small intent/topic schema, with deterministic local fallback.
- `auth.py` handles LDAP authentication and the development-only fallback login.
- `logging_store.py` writes request and feedback logs to SQLite.
- `realtime_tools.py` exposes structured support tools for the Realtime voice interface.
- `kb_scope.py` classifies KB files as public/student-safe or internal-only before retrieval.
- `templates/` and `static/` contain the Flask UI.
- `evaluate_*.py`, `validate_kb.py`, and `check_all.py` are part of the quality gate and should be kept working.

## Running Locally

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Run the app:

```bash
./venv/bin/python app.py
```

Open:

```txt
http://127.0.0.1:5000
```

Useful environment variables:

- `FLASK_SECRET_KEY`
- `LDAP_SERVER`
- `LDAP_PORT`
- `LDAP_DOMAIN`
- `LDAP_USE_SSL`
- `LDAP_REQUIRED_GROUP_DN`
- `ALLOW_DEV_LOGIN`
- `OPENAI_API_KEY`
- `IT_SUPPORT_LLM_ENABLED`
- `IT_SUPPORT_LLM_MODEL`
- `IT_SUPPORT_EMBEDDINGS_ENABLED`
- `IT_SUPPORT_SEMANTIC_MIN_SCORE`
- `ENABLE_AGENTS`
- `IT_SUPPORT_AGENT_MODEL`
- `IT_SUPPORT_AGENT_TIMEOUT_SECONDS`
- `OPENAI_REALTIME_PROMPT_ID`
- `OPENAI_REALTIME_MODEL`
- `OPENAI_REALTIME_VOICE`
- `ENABLE_INTERNAL_KB`
- `INTERNAL_KB_ALLOWED_USERS`
- `INTERNAL_KB_DEFAULT`

Production-like runs must not rely on the default Flask secret or development fallback login.

`ENABLE_AGENTS` defaults to off. When enabled with `OPENAI_API_KEY`, the Campus IT Triage Agent may add metadata such as missing-info suggestions or a ticket summary after deterministic KB retrieval. Agent output is additive metadata only; local KB retrieval and deterministic response fields remain authoritative.

`ENABLE_INTERNAL_KB` defaults to off. When enabled, internal SOP retrieval is available only to logged-in users listed in comma-separated `INTERNAL_KB_ALLOWED_USERS`. Authorized users can request explicit internal mode (`internal_mode=1`), or `INTERNAL_KB_DEFAULT=1` can enable it by default for that allowlisted staff audience. Internal SOP matches render only in an "Internal IT Notes" section and must not replace the student-facing answer.

## Validation And Checks

Before changing retrieval, routing, response rendering, or KB content, run the focused checks that match the change. Before handing off a broader change, prefer the full gate:

```bash
./venv/bin/python check_all.py
```

Individual checks:

```bash
./venv/bin/python validate_kb.py
./venv/bin/python evaluate_agent_service.py
./venv/bin/python evaluate_kb_scope.py
./venv/bin/python evaluate_disambiguation.py
./venv/bin/python evaluate_routing.py --strict
./venv/bin/python evaluate_retrieval.py --strict
./venv/bin/python evaluate_pilot_queries.py
./venv/bin/python evaluate_rendered_responses.py
./venv/bin/python evaluate_query_classifier.py
```

For Realtime tool changes, also run:

```bash
./venv/bin/python exercise_realtime_tools.py
```

## Safe Coding Rules

- Preserve retrieval-first behavior. A response should come from matched KB content or clearly fall back to an unsupported/escalation path.
- Keep `content/public/` and `content/internal/` grounded and reviewable. When adding or editing support guidance, include only approved institutional information.
- Public/student-facing KB articles must be marked or inferable as `VISIBILITY: public` and `SAFE_FOR_STUDENT: yes`. Existing top-level public articles default to public/student-safe for backward compatibility.
- Internal SOPs belong under `content/internal/` and must be marked with `VISIBILITY: internal` and `SAFE_FOR_STUDENT: no`.
- Never let internal SOP content affect normal student-facing titles, summaries, guided steps, escalation text, source footers, or response confidence.
- Internal SOP content may be shown only in a clearly labeled "Internal IT Notes" section when internal mode is enabled.
- Do not make OpenAI calls mandatory for normal support answers. Local deterministic fallback behavior must remain usable.
- Do not let LLM polishing add facts, steps, URLs, contact information, or policy language beyond retrieved source text.
- Do not let agent metadata replace retrieved source, section heading, steps, escalation text, supported state, contact details, password reset details, or Wi-Fi instructions.
- Maintain existing login/session protection for `/`, `/realtime`, `/realtime/session`, and `/realtime/tool`.
- Preserve LDAP authentication and the explicit development-only fallback behavior.
- Preserve SQLite request and feedback logging unless a requested change explicitly migrates storage.
- Keep Realtime endpoints compatible with the current client-secret and tool-dispatch flow.
- Avoid unrelated refactors, new frameworks, background workers, or persistent conversation stores unless the task requires them.
- Treat evaluation scripts and case files as first-class project behavior, not disposable test fixtures.
- Do not commit `.env`, real credentials, production secrets, or private institutional data.

## UI Style Goals

- Keep the interface practical, calm, and support-focused.
- Favor guided troubleshooting over chat-like novelty: context, steps, follow-up, additional troubleshooting, and escalation.
- Keep forms and follow-up actions simple enough for students, faculty, and support staff to use without training.
- Avoid marketing-page patterns, decorative complexity, or UI that obscures the support procedure.
- Preserve accessible, readable layouts across desktop and mobile.
- Do not expose implementation details, model behavior, or KB scoring as user-facing copy unless it is already part of the support workflow.

## Response Content Goals

- Answers must be grounded in retrieved KB text.
- Prefer concise support language that tells the user what to try next.
- Make escalation clear when the KB says to contact IT or when the topic is unsupported.
- Do not invent CCA policies, account rules, phone numbers, URLs, office locations, service availability, or troubleshooting steps.
- Keep tone steady and student-friendly without overpromising resolution.
- When a query is ambiguous, prefer disambiguation or a conservative support path over guessing.
- Keep password, MFA, and account-security flows especially strict about not requesting or exposing secrets.

## Testing Expectations

- For KB format changes, run `validate_kb.py`.
- For routing changes, run `evaluate_routing.py --strict`.
- For retrieval scoring or section parsing changes, run `evaluate_retrieval.py --strict`.
- For disambiguation changes, run `evaluate_disambiguation.py`.
- For guided response rendering changes, run `evaluate_rendered_responses.py` and manually smoke test the Flask UI when feasible.
- For classifier changes, verify both OpenAI-enabled behavior and local fallback behavior when practical.
- For authentication changes, smoke test login, logout, unauthorized redirects, LDAP configuration handling, and development fallback behavior.
- For logging changes, verify request and feedback rows are still written to SQLite.
- For Realtime changes, verify `/realtime/session`, `/realtime/tool`, and `exercise_realtime_tools.py`.
- If a check cannot be run, state why and describe the remaining risk.
