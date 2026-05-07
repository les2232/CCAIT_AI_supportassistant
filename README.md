# CCA IT Department Assistant

A retrieval-first IT support assistant for Community College of Aurora support workflows.

Unlike a generic chatbot, this system is built around approved documentation, guided troubleshooting, and explicit quality checks. It retrieves real support content, presents it as a structured procedure, and validates both routing and knowledge-base quality with repeatable scripts.

## Project Overview

This project is a guided IT support assistant for students and faculty at a community college.

It is designed to:

- find the best matching support procedure from an approved knowledge base
- present the result as a guided troubleshooting flow
- help users work through next steps before escalating to IT

It is for:

- students
- faculty
- internal support use cases where accurate, document-grounded guidance matters

It solves:

- repeated helpdesk questions
- inconsistent answers across common IT issues
- the need to turn documentation into a usable support experience

It is not:

- a general chatbot
- an open-ended AI assistant
- a system that invents answers from model knowledge
- a full conversational agent with persistent state

## Design Decisions

### Why retrieval-first instead of generative AI

Support guidance should come from approved procedures, not model improvisation.

Retrieval-first was chosen because it:

- keeps answers grounded in real documentation
- reduces hallucination risk
- makes behavior easier to test
- makes quality improvements depend on better content and better matching, not prompt tuning alone

The tradeoff is that the system is only as good as the knowledge base and retrieval logic. That is intentional. For this kind of support tool, controlled scope is more valuable than broad but unreliable coverage.

### Why a structured knowledge base format

Plain documentation is not enough for a guided support experience. The guide-ready field format was introduced so the system can separate:

- issue context
- primary steps
- follow-up troubleshooting
- escalation guidance

This makes the UI more usable and reduces the need to guess structure from raw text. The tradeoff is a higher documentation standard, but that cost is worth it because it improves consistency and makes support content easier to validate.

### Why a guided troubleshooting flow instead of simple Q&A

A simple answer block is often not enough for support work. Users need:

- context for what the procedure is trying to solve
- steps in a usable order
- a way to say the first pass did not work
- a clear escalation path

The guided flow turns documentation into an operational support tool rather than a search result. The tradeoff is a slightly more structured UI and response model, but the outcome is clearer and more useful for real troubleshooting.

### Why evaluation scripts exist

Most chatbot-style projects do not make behavior easy to verify. This project does.

The routing and retrieval evaluation scripts exist to catch regressions when:

- retrieval logic changes
- routing logic changes
- knowledge-base content changes

That matters because support quality should be measurable. If a content or logic change breaks known cases, the project should surface that immediately instead of relying on manual spot checks.

### Why a validation script was added

Once guide-ready fields were introduced, content quality became part of the runtime behavior.

The validation script exists to ensure:

- required guide fields are present
- structured fields are not empty
- section references actually resolve
- guided steps and escalation sections remain usable

This protects the system from silent content drift. The tradeoff is one more check in the workflow, but it is a small cost for much safer maintenance.

## Example Interaction

**User input**

`How do I reset my password?`

**Guided response**

Context:
- Use this guide when you need to reset your MyCCA password and get back into your student account.

Try these steps:
- Let’s get this working.
- Usually this fixes it. Try these steps in order.
- Go to the CCA password reset page and follow the prompts.
- Enter your student account information when asked.
- Complete the identity verification step.
- Create a new password and confirm it.

If that didn’t work:
- If the account is locked, wait a few minutes and try signing in again.
- If MFA is not working, confirm that you still have access to the correct phone, app, or verification method.

Still stuck?
- No worries — IT Support can help if sign-in is still blocked.
- Contact CCA IT Support if the password reset process does not work, the account stays locked, or MFA verification keeps failing.

## Architecture

### Flask app flow

The main application lives in [app.py](./app.py).

High-level flow:

1. user signs in through `/login`
2. authenticated user submits a question to `/`
3. the app checks for a lightweight disambiguation case for broad login-style questions
4. retrieval-first lookup runs against public KB articles in `content/public/`
5. if retrieval finds a match:
   - the matched article and section are used
   - confidence is included
   - escalation text is extracted
6. if retrieval does not find a confident match:
   - router fallback selects the best supporting article
   - section retrieval is retried inside that article
7. guided response data is built from structured guide fields when available
8. optional LLM rewriting can polish the retrieved answer text
9. the response is rendered in the Flask UI
10. the request is logged to SQLite
11. user feedback is stored in SQLite and linked to the original request log when available

### Heuristic retrieval

The main retriever is in [retriever.py](./retriever.py).

It works by:

- loading knowledge files under `content/public/`
- splitting each document into searchable sections
- scoring sections against the user question

The heuristic retrieval layer uses:

- token overlap
- weighted terms
- heading matches
- title matches
- phrase matches
- domain-specific boosts for common support patterns

This is the primary retrieval system and remains authoritative.

### Semantic retrieval fallback

Optional semantic retrieval is implemented in [semantic_retriever.py](./semantic_retriever.py) and integrated through [retriever.py](./retriever.py).

It uses:

- `sentence-transformers`
- model: `all-MiniLM-L6-v2`
- cosine similarity over section embeddings
- local cache file: `.semantic_cache/section_index.json`

It is controlled by environment variables and is designed as a conservative fallback. If semantic retrieval is unavailable or not confident, the app falls back to the heuristic retriever.

### Structured guide fields

Guide-ready articles include explicit structured fields that support guided troubleshooting mode:

- `TITLE`
- `AUDIENCE`
- `TAGS`
- `CONTEXT`
- `STEPS`
- `IF NOT FIXED`
- `ESCALATE`

These are parsed in [response_builder.py](./response_builder.py). When present, guided mode uses them instead of relying on sentence-level heuristic extraction.

### Guided troubleshooting flow

The UI presents retrieved answers as a guided support flow:

- context
- steps to try
- follow-up prompt: `Did this fix your issue?`
- additional troubleshooting if the answer is `No`
- escalation guidance

This flow is intentionally simple:

- no complex client-side state
- no persistent conversation model
- disambiguation and follow-up are handled with form resubmission

### Optional LLM rewrite layer

The optional rewrite layer is implemented in [llm_answer.py](./llm_answer.py).

Important constraints:

- retrieval is still required first
- the LLM does not answer from general knowledge
- the LLM receives only:
  - user question
  - article id
  - section heading
  - retrieved answer text

If LLM rewriting is disabled, unavailable, or fails, the original retrieved answer is returned unchanged.

### LDAP authentication

Authentication is implemented in [auth.py](./auth.py).

It supports:

- LDAP bind against Active Directory
- required AD group membership check
- optional development-only fallback login controlled by environment variable

The main app uses Flask sessions to protect `/` and redirect unauthenticated users to `/login`.

### SQLite logging and feedback

SQLite logging is implemented in [logging_store.py](./logging_store.py).

Tables:

- `request_logs`
- `feedback_logs`

What is logged:

- redacted question text
- routed topic/article
- response type
- escalation flag
- whether LLM polishing was used
- helpful/unhelpful feedback linked back to a request when possible

The logging layer redacts obvious sensitive values before writing request or
feedback text, including passwords, MFA codes, student IDs, email addresses,
and phone numbers.

## Knowledge Base Format

Knowledge articles live under [content/](./content/):

- `content/public/` contains student/faculty-facing support articles.
- `content/internal/` contains staff-only SOPs that can appear only as internal notes for allowlisted users.

The loader keeps existing article IDs stable. For example, `content/public/password-reset.txt` is still identified as `password-reset.txt`, and `content/internal/printing/map-network-printer.txt` is still identified as `printing/map-network-printer.txt`.

The system supports two content styles:

- standard sectioned articles
- guide-ready articles with explicit structured fields

Structured guide fields are documented in:

- [docs/guide-format.md](./docs/guide-format.md)

### Guide-ready fields

- `TITLE`
- `AUDIENCE`
- `TAGS`
- `CONTEXT`
- `STEPS`
- `IF NOT FIXED`
- `ESCALATE`

In the current implementation, guide fields often reference existing article headings in the same file rather than duplicating the same procedure text. This keeps retrieval behavior stable while still giving guided mode explicit structure.

### Example

```txt
SOURCE: Community College of Aurora Example Article

==================================================

EXAMPLE SUPPORT ARTICLE

What this helps with:
- Use this guide when a student cannot complete a sign-in workflow.

How to sign in:
1. Open the service.
2. Sign in with your student account.
3. Try the task again.

If you're still stuck:
- Contact CCA IT Support if sign-in still fails.

- TITLE: Example Support Article
- AUDIENCE: Students
- TAGS: login, account, sign-in
- CONTEXT:
  - What this helps with:
- STEPS:
  - How to sign in:
- IF NOT FIXED:
  - If you're still stuck:
- ESCALATE:
  - If you're still stuck:
```

## Evaluation and Validation

This project includes explicit evaluation scripts and a knowledge-base validator.

### Routing evaluation

Run:

```bash
./venv/bin/python evaluate_routing.py --strict
```

This validates topic/article routing behavior for representative support questions.

### Retrieval evaluation

Run:

```bash
./venv/bin/python evaluate_retrieval.py --strict
```

This validates section-level retrieval behavior, including expected article and matched heading.

### Knowledge-base validation

Run:

```bash
./venv/bin/python validate_kb.py
```

This validates structured guide fields and guide-heading references for KB files under `content/public/` and `content/internal/`.

What it checks:

- required guide fields for guide-ready articles
- heading references that must exist in the same file
- whether `STEPS` resolves to usable step content
- whether `ESCALATE` resolves to escalation text

## Running Locally

### 1. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Copy the safe example file and keep your local values out of git:

```bash
cp .env.example .env
```

At minimum, set:

- `FLASK_SECRET_KEY`

Generate a local secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Paste that value into `.env` as `FLASK_SECRET_KEY`. Do not commit `.env` or
real secrets.

Optional features:

- LDAP settings for your environment
- LLM rewriting
- OpenAI-backed classification
- Realtime voice support
- semantic retrieval fallback
- additive agent metadata
- internal KB notes for explicitly allowed staff users
- development fallback login

### 4. Run the Flask app

```bash
./venv/bin/python app.py
```

Then open:

```txt
http://127.0.0.1:5000
```

## Environment Variables

### Required for normal deployment

- `FLASK_SECRET_KEY`

Local development should set this in `.env`. Production deployments should use
the target hosting platform's secret-management mechanism.

### LDAP authentication

- `LDAP_SERVER`
- `LDAP_PORT`
- `LDAP_DOMAIN`
- `LDAP_USE_SSL`
- `LDAP_REQUIRED_GROUP_DN`

### Development-only fallback login

- `ALLOW_DEV_LOGIN`

When enabled, the app allows a temporary local fallback login. This should remain disabled outside development.

### Optional LLM rewrite settings

- `OPENAI_API_KEY`
- `IT_SUPPORT_LLM_ENABLED`
- `IT_SUPPORT_LLM_MODEL`
- `IT_SUPPORT_CLASSIFIER_MODEL`

OpenAI-backed features are optional. The app must remain usable without
`OPENAI_API_KEY`.

### Optional Realtime voice settings

- `OPENAI_REALTIME_PROMPT_ID`
- `OPENAI_REALTIME_MODEL`
- `OPENAI_REALTIME_VOICE`

### Optional semantic retrieval settings

- `IT_SUPPORT_EMBEDDINGS_ENABLED`
- `IT_SUPPORT_SEMANTIC_MIN_SCORE`

The semantic layer also uses a local cache:

- `.semantic_cache/section_index.json`

### Optional agent metadata settings

- `ENABLE_AGENTS`
- `IT_SUPPORT_AGENT_MODEL`
- `IT_SUPPORT_AGENT_TIMEOUT_SECONDS`

`ENABLE_AGENTS` defaults to off. When enabled with `OPENAI_API_KEY`, agent
output is additive metadata only. The local KB and deterministic response fields
remain authoritative.

### Optional internal KB settings

- `ENABLE_INTERNAL_KB`
- `INTERNAL_KB_ALLOWED_USERS`
- `INTERNAL_KB_DEFAULT`

`ENABLE_INTERNAL_KB` defaults to off. When enabled, internal notes are still
shown only to logged-in usernames listed in comma-separated
`INTERNAL_KB_ALLOWED_USERS`. `INTERNAL_KB_DEFAULT=1` applies only to those
allowlisted users.

## Development Workflow

Recommended workflow for safe changes:

1. edit or add public knowledge articles in `content/public/`, or staff-only SOPs in `content/internal/`
2. run KB validation
3. run routing and retrieval evaluations
4. smoke test the Flask UI

Commands:

```bash
./venv/bin/python validate_kb.py
./venv/bin/python evaluate_disambiguation.py
./venv/bin/python evaluate_routing.py --strict
./venv/bin/python evaluate_retrieval.py --strict
./venv/bin/python evaluate_rendered_responses.py
./venv/bin/python check_all.py
./venv/bin/python app.py
```

Recommended after UI or flow changes:

- test normal question submission
- test disambiguation
- test guided Yes/No follow-up
- test feedback logging

## Production Notes

Detailed deployment guidance is documented in:

- [docs/production-readiness.md](./docs/production-readiness.md)
- [docs/deployment-runbook.md](./docs/deployment-runbook.md)

Before deployment:

- disable development fallback login
- require a secure `FLASK_SECRET_KEY`
- validate LDAP bind and group membership in the target environment
- serve the app behind Gunicorn, Nginx, or equivalent
- use HTTPS
- verify that optional LLM and semantic features are intentionally enabled or disabled

This project should be treated as an internal support application, not a public anonymous chatbot endpoint.

## Why This Project Is Different

This project is designed as a support system, not a demo chatbot. The combination of retrieval-first behavior, structured guide-ready content, guided troubleshooting flow, and explicit evaluation and validation makes it closer to an operational internal tool than a prompt-based prototype.

## Future Improvements

Realistic next steps:

- expand structured guide coverage across the remaining knowledge articles
- improve disambiguation beyond the current broad login cases
- add basic analytics or a review dashboard for request and feedback trends
- support optional stateful guided flows where a small number of troubleshooting branches need persistent context

## Limitations

Current limitations:

- disambiguation is intentionally simple and only covers limited broad-query cases
- there is no persistent conversation state yet
- some articles still rely on fallback heuristic extraction rather than structured guide fields
- the optional LLM layer is rewrite-only and should not be treated as a source of truth
- guide-ready content is partially converted, not fully complete across all articles

## Project Structure

```txt
app.py                    Flask web entry point
support_service.py        retrieval-first orchestration
retriever.py              section retrieval
router.py                 fallback article routing
response_builder.py       guided response shaping
auth.py                   LDAP and dev login helpers
logging_store.py          SQLite request and feedback logs
llm_answer.py             optional retrieved-text polishing
content/
  public/                 student/faculty-facing KB articles
  internal/               staff-only SOPs for internal notes
templates/                Flask templates
static/                   browser assets
docs/                     runbooks and review docs
deploy/                   service and nginx examples
validate_kb.py            KB validator
evaluate_*.py             regression checks
*_eval_cases.py           evaluation case data
report_logs.py            local log reporting
export_*.py               local review/audit exports
```
