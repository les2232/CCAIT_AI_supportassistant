# Final Pilot Readiness Checklist

Use this checklist immediately before pilot launch. Do not mark an item complete unless a human reviewer has checked it against the current code, docs, KB content, deployed environment, or rendered app output.

## 1. Verified Public KB Content

- [ ] OBL location is verified and public wording says OBL is in room F103.
- [ ] Hub location, contact, and hours are verified and public wording matches the approved source.
- [ ] Microsoft 365 wording says students have web access and does not imply desktop app entitlement.
- [ ] Student email wording says email uses MFA and encourages students to prioritize logging into email after registering.
- [ ] MFA changed-phone/account-recovery wording tells students to contact CCA IT when they cannot verify login after a phone/device/number change.
- [ ] Laptop wording is cautious about availability, checkout procedure, inventory, renewal rules, and eligibility.
- [ ] Adobe Creative Cloud wording says access is limited to graphic design students or students whose class requires Adobe.
- [ ] SolidWorks wording says it is installed on Innovation Lab computers and CAST 132 computers only.
- [ ] Classroom audio wording tells users to select Extron as the speaker/audio output device, if this guidance is currently verified.

## 2. Internal KB Separation

- [ ] Public student-facing content lives under `content/public/`.
- [ ] Internal-only content lives under `content/internal/`.
- [ ] Student mode does not leak internal paths, internal SOPs, printer server paths, Entra/admin details, or internal escalation notes.
- [ ] Internal mode is intentionally separate from student mode and covered by tests.
- [ ] Public answers remain retrieval-first and grounded in approved public KB content.

## 3. Required Checks Passing

- [ ] `./venv/bin/python check_all.py` passes from the repository root.
- [ ] `git diff --check` passes from the repository root.
- [ ] If `scripts/run-local-kb.sh` exists, `bash -n scripts/run-local-kb.sh` passes.
- [ ] Local `FLASK_SECRET_KEY` and LDAP startup warnings are understood as expected in local eval context unless production mode is being tested.
- [ ] Any production-mode check is run with explicit production environment values, not local fallback values.

## 4. No Generated Files Tracked

- [ ] No `__pycache__/` files are tracked.
- [ ] No `.pytest_cache/` files are tracked.
- [ ] No `.semantic_cache/` files are tracked.
- [ ] No SQLite log DBs are tracked.
- [ ] No local `.env` files are tracked.
- [ ] No generated logs are tracked.
- [ ] No candidate scraper output is tracked.
- [ ] No secrets, API keys, passwords, tokens, or private account values are tracked.

## 5. Login And Session Behavior

- [ ] Local-only mode blocks `OPENAI_API_KEY` conflicts for deterministic KB-only testing.
- [ ] Production uses an explicit `FLASK_SECRET_KEY` and does not rely on the development fallback.
- [ ] LDAP/LDAPS server, port, domain, SSL setting, and required group DN are explicitly reviewed before production.
- [ ] Production LDAP does not use cleartext LDAP unless explicitly approved for a non-production environment.
- [ ] Session cookie settings are covered by production readiness checks.
- [ ] Optional AI, classifier, embeddings, Realtime, and agent paths remain disabled unless explicitly reviewed and approved.

## 6. CSRF, Rate Limiting, And Security Controls

- [ ] Login and form posts reject missing or invalid CSRF tokens.
- [ ] Valid CSRF tokens allow login and form submissions.
- [ ] Login rate limiting works for failed attempts.
- [ ] Successful login does not break rate-limit state.
- [ ] Request and feedback logging redact sensitive fields.
- [ ] Logging failures do not expose user text in unsafe ways.

## 7. Contact And Escalation Wording

- [ ] Public answers use student-friendly or faculty/staff-friendly contact paths appropriate to the matched article.
- [ ] CCA IT Helpdesk is used for account, MFA, email, Wi-Fi, device, and classroom technology issues.
- [ ] Hub contact information is not presented as an IT Helpdesk replacement.
- [ ] OBL contact/path is used for online learning, course design, and instructional support where appropriate.
- [ ] Rendered answers avoid duplicate escalation blocks.
- [ ] Rendered answers avoid internal-only terms unless internal mode is active.

## 8. Pilot Prompts To Manually Test

| Prompt | Expected behavior | Pass/fail | Notes |
| --- | --- | --- | --- |
| I can't log in | Concise login disambiguation with D2L, student email, MyCCA, campus computer, Wi-Fi, MFA/Auth, and not-sure options. | [ ] | |
| My student email is not working | Student email troubleshooting with correct account/password, email MFA, Outlook web, and CCA IT path if MFA/account access is blocked. | [ ] | |
| I got a new phone and can't approve MFA | MFA recovery guidance that tells the student to contact CCA IT for changed phone/device/number verification method help. | [ ] | |
| I am not getting my verification code | MFA verification troubleshooting that does not assume Duo for students and does not overclaim service behavior. | [ ] | |
| Where is OBL located? | Direct OBL location answer: F103. No generic IT troubleshooting block. | [ ] | |
| Where is the Hub? | Direct Hub location/contact/hours answer for CentreTech Hub, Classroom Building, Room 107. | [ ] | |
| I need a laptop | Cautious laptop availability/checkout guidance with Student Success path and no overclaim about inventory or eligibility. | [ ] | |
| Can I use Adobe? | Adobe answer says Creative Cloud is on CCA Macs and access is limited to eligible students/classes. | [ ] | |
| Where can I use SolidWorks? | SolidWorks answer gives Innovation Lab computers and CAST 132 computers only. | [ ] | |
| Audio not working in classroom | Classroom audio steps include mute, room/app volume, selecting Extron as output, and retrying audio. | [ ] | |
| Projector has no signal | Classroom projector troubleshooting with source/input and cable/adapter checks, plus appropriate IT escalation info. | [ ] | |
| How do I print on campus? | Public printing guidance without internal printer server paths or internal mapping instructions. | [ ] | |
| Zoom asks for SSO | Public Zoom SSO guidance without internal-only SSO/domain/license-sync details. | [ ] | |
| I need help | Concise broad-help options, not an invented answer. | [ ] | |

## 9. README And Deployment Notes

- [ ] If `scripts/run-local-kb.sh` exists, README includes local KB-only runner instructions.
- [ ] Deployment runbook uses the correct project gate: `./venv/bin/python check_all.py`.
- [ ] Deployment docs distinguish local KB-only testing from production settings.
- [ ] Deployment path/user mismatch is reviewed: `docs/deployment-runbook.md` examples use `/opt/cca-it-support-assistant` and `cca-assistant`, while `deploy/cca-it-support-assistant.service` uses `/opt/project/it-ai-agent` and `www-data`.
- [ ] Pilot tag and latest commit are recorded before launch.
- [ ] Rollback or stop/start commands have been reviewed for the actual deployment host.

## 10. Final Sign-Off

- Reviewer:
- Date:
- Git commit:
- Pilot tag:
- Checks run:
- Known unresolved items:
- Approved for pilot? yes/no:
