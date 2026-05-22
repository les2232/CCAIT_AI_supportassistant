# Pilot Handoff

This document is the short handoff guide for an internal CCA IT Support Assistant pilot.

## What The Project Does

- Provides retrieval-first IT support guidance from approved local KB files.
- Uses public KB articles in `content/public/` for normal student-facing answers.
- Keeps staff SOPs in `content/internal/` isolated unless internal KB mode is enabled for an allowlisted staff user.
- Presents support answers as guided troubleshooting: context, steps, follow-up, escalation, and feedback.
- Logs requests and helpful/unhelpful feedback to SQLite for pilot review.

## What It Does Not Do

- It is not a general chatbot.
- It does not invent procedures, policies, URLs, contact information, or escalation paths.
- It does not require OpenAI for normal support answers.
- It does not replace LDAP, the IT Helpdesk, instructors, OBL, or human review of support content.
- It does not provide case management, persistent conversation state, or a production analytics dashboard.

## Run Locally

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./venv/bin/python app.py
```

Open `http://127.0.0.1:5000`.

## Required Local `.env` Values

At minimum for local development:

```env
FLASK_SECRET_KEY=<generated-local-secret>
ALLOW_DEV_LOGIN=1
```

For LDAP testing, set approved local test values:

```env
LDAP_SERVER=<approved-ldap-host>
LDAP_PORT=636
LDAP_DOMAIN=<approved-domain>
LDAP_USE_SSL=1
LDAP_REQUIRED_GROUP_DN=<approved-test-group-dn>
ALLOW_DEV_LOGIN=0
```

The supported default is local-only mode:

```env
IT_SUPPORT_LOCAL_ONLY=1
OPENAI_API_KEY=
IT_SUPPORT_LLM_ENABLED=0
IT_SUPPORT_CLASSIFIER_ENABLED=0
IT_SUPPORT_EMBEDDINGS_ENABLED=0
ENABLE_AGENTS=0
ENABLE_REALTIME_SUPPORT=0
ENABLE_INTERNAL_KB=0
```

OpenAI-backed features should stay off unless explicitly reviewed and tested separately. If any OpenAI-backed feature is intentionally enabled, `IT_SUPPORT_LOCAL_ONLY` must be set to `0` first.

## Set `FLASK_SECRET_KEY`

Generate a local value:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Put the generated value in `.env`. Do not commit `.env` or real secrets.

## Enable Dev Login Locally

Set:

```env
ALLOW_DEV_LOGIN=1
```

Use dev login only on an isolated local machine. Production and shared pilot environments must use `ALLOW_DEV_LOGIN=0`.

## Quality Gate

Run:

```bash
./venv/bin/python scripts/validate_kb.py
./venv/bin/python check_all.py
./venv/bin/python evaluations/evaluate_pilot_queries.py
```

`check_all.py` runs the deterministic retrieval-first gate with optional OpenAI, embeddings, and agent metadata disabled. Use `evaluations/evaluate_query_classifier.py` separately when intentionally testing classifier behavior.

## Smoke Test

After starting the app:

1. Log in using LDAP or local dev login.
2. Submit `How do I reset my password?`
3. Submit `I changed phones and cannot verify my login`
4. Submit `How do I access D2L?`
5. Submit `How do I connect to Wi-Fi?`
6. Submit `Classroom display won't turn on`
7. Use the guided `No` follow-up and confirm extra troubleshooting and escalation appear.
8. Submit helpful/unhelpful feedback and confirm it writes to `feedback_logs`.

## Production Deployment Reminders

- Set `APP_ENV=production`.
- Set a long random `FLASK_SECRET_KEY`.
- Use LDAPS: `LDAP_USE_SSL=1` and `LDAP_PORT=636` or another approved LDAPS port.
- Set `ALLOW_DEV_LOGIN=0`.
- Serve behind HTTPS.
- Confirm the service account can write the SQLite log database path.
- Keep `ENABLE_INTERNAL_KB=0` unless approved staff usernames are listed in `INTERNAL_KB_ALLOWED_USERS`.
- Keep OpenAI-backed features disabled unless approved for the pilot and tested separately.

## Known Limitations

- SQLite logging is local and simple; it is not a multi-node reporting system.
- Disambiguation is intentionally small and focused on common pilot ambiguity.
- The guided flow is stateless and form-based.
- Some KB facts still require human verification before being treated as final institutional guidance.
- Optional OpenAI features are secondary and should not be used as sources of truth.

## Human Verification Items

From `docs/content-verification.md`, confirm before expanding or hardening public guidance:

- Whether MyCCA itself requires MFA; student email MFA is verified, but MyCCA MFA requirements are not.
- Whether `onlinelearning.cca@ccaurora.edu` remains the public-facing OBL support address.
- Microsoft 365 desktop app entitlement, OneDrive desktop sync behavior, storage quotas, and sharing limits.
- Laptop checkout procedure, exact inventory, renewal options, and eligibility.
- Exact Hub desk ownership for printing, headphones, and other service-specific checkout paths.
- Preferred student-facing naming for D2L, Brightspace, MyCourses, or a combination.
- Supported Windows 11 mapped-drive recovery steps and whether any internal path/script guidance may be public.
- Printing support ownership and personal-device printing expectations.

## Recommended Pilot Feedback Process

- Ask pilot users to use the built-in helpful/unhelpful buttons after each answer.
- Review `scripts/report_logs.py` output weekly during pilot.
- Track repeated unsupported questions, low-confidence routes, and unhelpful feedback as KB review items.
- Route content changes through human verification before editing public KB articles.
- After KB or retrieval changes, run the quality gate and add pilot/evaluation cases for any newly protected behavior.
