# Project Audit

Last updated: 2026-05-22

Purpose: identify what is required for the CCA IT Support Assistant pilot, what is optional, what is future work, and what may confuse maintainers. This is an audit only; do not remove or refactor files based on this document without a separate cleanup task.

Current audit note: this pass observed existing uncommitted work in `README.md`, `content/public/password-reset.txt`, `content/public/student-email.txt`, and `scripts/run-local-kb.sh`. Those changes were not evaluated as a committed baseline.

## Pilot Posture

The pilot should run in deterministic local KB-only mode:

```env
IT_SUPPORT_LOCAL_ONLY=1
OPENAI_API_KEY=
IT_SUPPORT_LLM_ENABLED=0
IT_SUPPORT_CLASSIFIER_ENABLED=0
IT_SUPPORT_EMBEDDINGS_ENABLED=0
ENABLE_AGENTS=0
ENABLE_REALTIME_SUPPORT=0
```

In this posture, approved local KB content, deterministic routing, deterministic retrieval, disambiguation, and escalation are authoritative. Optional OpenAI, agent, Realtime, and semantic retrieval paths must remain disabled unless explicitly reviewed.

## Runtime App Files

Required for the Flask assistant:

| Item | Classification | Notes |
|---|---|---|
| `app.py` | Keep | Flask entry point; owns auth routes, main support form, feedback, internal-mode rendering, and disabled-by-default Realtime routes. |
| `auth.py` | Keep | LDAP authentication and dev-only fallback login controls. |
| `config.py` | Keep | Runtime env parsing, startup validation, session-cookie config, local-only conflict checks. |
| `support_service.py` | Keep | Coordinates retrieval-first answer resolution and optional additive metadata. |
| `retriever.py` | Keep | Primary heuristic section retrieval. |
| `router.py` | Keep | Deterministic article fallback selection. |
| `response_builder.py` | Keep | Builds guided support UI fields from retrieved KB content. |
| `input_guard.py` | Keep | Handles greetings, vague requests, and broad login disambiguation before retrieval. |
| `kb_scope.py` | Keep | Enforces public/internal KB separation. |
| `logging_store.py` | Keep | SQLite request and feedback logging with redaction. |
| `llm_answer.py` | Keep but document | Optional LLM answer polishing. Disabled by default and source-bounded when enabled. |
| `query_classifier.py` | Keep but document | Optional OpenAI classifier with deterministic fallback. Disabled by default. |
| `agent_service.py` | Keep but document | Optional additive agent metadata. Disabled by default and cannot replace KB-derived fields. |
| `semantic_retriever.py` | Keep but document | Optional embedding fallback. Disabled by default; brings dependency and cache complexity if enabled. |
| `realtime_tools.py` | Keep but document | Optional Realtime tool dispatcher. Disabled by default. |
| `templates/index.html`, `templates/login.html` | Keep | Required UI templates for the pilot app. |
| `templates/realtime.html` | Keep but document | Only used when `ENABLE_REALTIME_SUPPORT=1`; should not affect KB-only pilot. |
| `static/styles.css`, `static/app.js` | Keep | Required UI assets. |
| `static/realtime.js` | Keep but document | Only used by disabled-by-default Realtime UI. |
| `requirements.txt` | Keep but document | Contains runtime and optional AI/embedding dependencies. Large optional dependency footprint could confuse maintainers later. |
| `.env.example` | Keep | Documents safe local/pilot env defaults. |

## Public KB Content

Required for the public student-facing pilot:

| Area | Files | Classification | Notes |
|---|---|---|---|
| Contact / IT routing | `content/public/contact-it.txt`, `content/public/cca-tech-help.txt`, `content/public/it-resources.txt` | Keep | Core escalation and campus-support guidance. |
| Login / account / MFA | `content/public/password-reset.txt`, `content/public/mfa-account-security.txt` | Keep | High-risk account guidance; keep conservative and evaluated. |
| Student email / Microsoft 365 | `content/public/student-email.txt`, `content/public/student-email-troubleshooting.txt`, `content/public/student-email-office365.txt` | Keep | Core pilot coverage; should remain verified and cautious. |
| D2L / online learning | `content/public/d2l.txt`, `content/public/d2l-troubleshooting.txt`, `content/public/online-blended-learning.txt` | Keep | Needed for broad login disambiguation and online-course support. |
| Wi-Fi / printing / devices | `content/public/wifi-troubleshooting.txt`, `content/public/printing.txt`, `content/public/student-laptops-calculators.txt` | Keep | Common student support paths. |
| Zoom / YuJa / classroom / Windows | `content/public/zoom-support.txt`, `content/public/yuja-panorama.txt`, `content/public/classroom-technology.txt`, `content/public/windows-11.txt` | Keep | Useful pilot scope; several ownership/details remain human-verification sensitive. |

Public KB risks:

- Keep public wording tied to verified institutional facts.
- Keep unresolved claims tracked in `docs/content-verification.md`.
- Do not move internal SOP details into public KB files.
- Broad login issues should keep disambiguating rather than guessing.

## Internal KB Content

Internal KB files:

- `content/internal/mfa/student-microsoft-365-mfa.txt`
- `content/internal/printing/map-network-printer.txt`
- `content/internal/software/pdf-digital-signature-acrobat.txt`
- `content/internal/zoom/zoom-sso-login.txt`

Classification: Keep but document.

Separation model:

- Internal files live under `content/internal/`.
- `kb_scope.py` marks internal namespace content as internal-only by default.
- Normal student retrieval loads only public, student-safe files.
- Internal notes require `ENABLE_INTERNAL_KB=1` and an allowlisted user in `INTERNAL_KB_ALLOWED_USERS`.
- Internal matches render only in an "Internal IT Notes" panel and must not replace student-facing answers.
- `evaluations/evaluate_kb_scope.py` is the required regression check for this boundary.

Pilot note: keep `ENABLE_INTERNAL_KB=0` unless a staff-only pilot explicitly approves it.

## Evaluation And Required Gate

Required gate:

```bash
./venv/bin/python check_all.py
```

`check_all.py` forces deterministic env overrides and runs:

- `scripts/validate_kb.py`
- `evaluations/evaluate_logging_privacy.py`
- `evaluations/evaluate_phase1_production.py`
- `evaluations/evaluate_security_controls.py`
- `evaluations/evaluate_kb_scope.py`
- `evaluations/evaluate_agent_service.py`
- `evaluations/evaluate_disambiguation.py`
- `evaluations/evaluate_routing.py --strict`
- `evaluations/evaluate_retrieval.py --strict`
- `evaluations/evaluate_rendered_responses.py`

Other useful checks:

| Item | Classification | Notes |
|---|---|---|
| `evaluations/evaluate_pilot_queries.py` | Keep but document | Useful release/smoke check referenced in handoff docs, but not currently part of `check_all.py`. |
| `evaluations/evaluate_query_classifier.py` | Keep but document | Focused check for optional classifier behavior. Not required for KB-only pilot unless classifier is being touched. |
| `evaluations/*_eval_cases.py` | Keep | Test data for routing/retrieval/pilot evaluations. |
| `scripts/exercise_realtime_tools.py` | Defer | Useful only for Realtime tool changes; Realtime is disabled for pilot. |
| `scripts/validate_kb.py` | Keep | Required content validator and part of `check_all.py`. |

## Optional AI, Classifier, Realtime, And Semantic Features

| Feature | Files | Default | Classification | Pilot guidance |
|---|---|---|---|---|
| LLM answer polishing | `llm_answer.py` | Off | Keep but document | Must remain fallback-only and source-bounded. |
| OpenAI query classifier | `query_classifier.py` | Off | Keep but document | Deterministic local fallback remains authoritative. |
| Agent metadata | `agent_service.py` | Off | Keep but document | Additive metadata only; must not replace answer fields. |
| Realtime voice interface | `realtime_tools.py`, `templates/realtime.html`, `static/realtime.js`, Realtime routes in `app.py` | Off | Defer | Should not be part of student-facing pilot unless separately approved. |
| Semantic retrieval | `semantic_retriever.py`, `.semantic_cache/` at runtime | Off | Defer | Brings large dependencies and cache behavior; keep disabled for deterministic pilot. |

Startup validation in `config.py` fails when local-only mode conflicts with `OPENAI_API_KEY` or optional AI flags being enabled.

## Pilot Handoff Documentation

| File | Classification | Notes |
|---|---|---|
| `README.md` | Keep | Main project orientation and local run instructions. |
| `AGENTS.md` | Keep | Contributor/agent operating rules; important for preserving retrieval-first behavior. |
| `docs/pilot-handoff.md` | Keep | Short pilot operator handoff. |
| `docs/deployment-runbook.md` | Keep | Deployment, restart, rollback, and log commands. |
| `docs/production-readiness.md` | Keep | Production/pilot readiness checklist and startup validation expectations. |
| `docs/content-verification.md` | Keep | Source-of-truth tracking for verified and unresolved claims. |
| `docs/human-verification-checklist.md` | Keep | Human review handoff checklist. |
| `docs/guide-format.md` | Keep | KB authoring format. |
| `docs/manual-kb-review.md` | Keep but document | Generated-style review workbook; useful but could drift if not regenerated intentionally. |
| `docs/future-work.md` | Keep | Clearly marks public KB ingest scraper as future-only. |
| `docs/project-audit.md` | Keep | This audit. |

## Future Work And Experimental Files

| Item | Classification | Notes |
|---|---|---|
| `docs/future-work.md` | Keep | Correctly states public KB ingest scraper must remain non-runtime/candidate-only and require human review. |
| Public KB ingest scraper idea | Defer | Do not add before pilot. No scraper workflow, dependencies, or indexing path should be introduced now. |
| `scripts/run-local-kb.sh` | Keep but document | Convenience wrapper for deterministic local KB-only Flask runs. Newly added in working tree; should be committed only if accepted. |
| `scripts/export_kb_audit.py` | Keep but document | Regenerates `docs/manual-kb-review.md`; not runtime. Could overwrite manual notes if run casually. |
| `scripts/export_review_csv.py` | Keep but document | Operational review helper for SQLite logs; not runtime. |
| `scripts/report_logs.py` | Keep | Useful pilot operations report. |
| `scripts/seed_test_logs.py` | Candidate for removal later | Non-runtime sample data helper. Some sample topics/strings may be stale or inconsistent with current KB, so keep out of pilot docs unless reviewed. |
| `deploy/cca-it-support-assistant.service` | Keep but document | Concrete service file uses `/opt/project/it-ai-agent` and `www-data`; runbook uses generic `/opt/cca-it-support-assistant` and `cca-assistant`. This difference may confuse maintainers. |
| `deploy/nginx-itsupport.conf` | Keep but document | Concrete domain/cert paths are environment-specific. Good as deployed example, but should not be blindly copied. |
| `requirements.txt` optional AI/embedding packages | Needs human review | Required for current installed feature set, but large optional dependencies make KB-only deployment heavier than necessary. Do not change before pilot. |

## Questionable Or Confusing Items

| Item | Classification | Reason |
|---|---|---|
| Two deployment identities/paths in docs vs `deploy/` | Keep but document | Runbook uses generic `cca-assistant` and `/opt/cca-it-support-assistant`; deploy files use `www-data` and `/opt/project/it-ai-agent`. Clarify which is authoritative for the pilot server before handoff. |
| `evaluate_pilot_queries.py` is recommended in docs but not in `check_all.py` | Keep but document | It may be a supplemental smoke check rather than required gate. Maintainers should know `check_all.py` is the deterministic required gate. |
| Realtime UI/assets/routes are present while Realtime is disabled | Defer | Safe behind `ENABLE_REALTIME_SUPPORT=0`, but can confuse maintainers who see voice UI files. |
| Optional OpenAI/agent/semantic files are present in a KB-only pilot | Keep but document | Startup validation protects local-only mode; docs should continue calling these optional. |
| `docs/manual-kb-review.md` generated review workbook | Keep but document | Useful for manual review, but generated content can become stale. |
| `scripts/seed_test_logs.py` sample content | Candidate for removal later | May include stale sample topics from earlier phases; not runtime or gate-critical. |
| Large dependency footprint in `requirements.txt` | Needs human review | Includes optional OpenAI, agents, sentence-transformers, torch/CUDA stack. This is not a pilot blocker but should be reviewed after handoff. |
| Uncommitted local content edits | Needs human review | Audit observed uncommitted changes in `content/public/password-reset.txt` and `content/public/student-email.txt`; verify they are intentional before committing a pilot release. |

## Commands

Run locally in deterministic KB-only mode:

```bash
cd /opt/project/it-ai-agent
scripts/run-local-kb.sh
```

Default local URL:

```txt
http://127.0.0.1:5055
```

Override local host/port:

```bash
FLASK_RUN_HOST=127.0.0.1 FLASK_RUN_PORT=5060 scripts/run-local-kb.sh
```

Run the required quality gate:

```bash
cd /opt/project/it-ai-agent
./venv/bin/python check_all.py
git diff --check
```

Run focused checks when needed:

```bash
./venv/bin/python scripts/validate_kb.py
./venv/bin/python evaluations/evaluate_kb_scope.py
./venv/bin/python evaluations/evaluate_rendered_responses.py
./venv/bin/python evaluations/evaluate_pilot_queries.py
```

Restart deployed service if using the documented systemd unit:

```bash
sudo systemctl restart cca-it-support-assistant
sudo systemctl status cca-it-support-assistant
```

Reload Nginx after proxy/config changes:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

View service logs:

```bash
sudo journalctl -u cca-it-support-assistant -n 200 --no-pager
sudo tail -n 200 /var/log/nginx/access.log
sudo tail -n 200 /var/log/nginx/error.log
```

Review feedback logs:

```bash
cd /opt/project/it-ai-agent
./venv/bin/python scripts/report_logs.py
```

## Pilot Blockers

No pilot blockers were identified in this audit pass.

Items to confirm before final handoff:

- Decide whether the concrete `deploy/` files or the generic runbook examples are authoritative for the pilot server.
- Confirm uncommitted KB wording changes are intentional before committing a release.
- Keep optional AI, Realtime, agent, and semantic retrieval flags disabled for pilot.
- Continue tracking unresolved human-verification items in `docs/content-verification.md`.
