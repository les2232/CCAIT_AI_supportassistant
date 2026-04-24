# Guide-Ready Knowledge Base Format

This project supports a guide-ready article format for structured troubleshooting responses.

The guide fields are parsed in [response_builder.py](../response_builder.py) and validated by [validate_kb.py](../validate_kb.py).

## Supported Fields

- `TITLE`
- `AUDIENCE`
- `TAGS`
- `CONTEXT`
- `STEPS`
- `IF NOT FIXED`
- `ESCALATE`

## Recommended Pattern

Write the article as a normal support document first, with clear retrieval-friendly headings. Then add guide fields at the end of the file.

Use guide fields to reference existing article headings whenever possible. This keeps retrieval behavior stable and avoids duplicating full troubleshooting text in the same file.

## Example

```txt
SOURCE: Community College of Aurora Example Support

==================================================

EXAMPLE SUPPORT ARTICLE

What this helps with:
- Use this guide when a student cannot complete a sign-in workflow.

How to sign in:
1. Open the service.
2. Sign in with your student account.
3. Try the task again.

If you're still stuck:
- Contact CCA IT Support if the sign-in process still fails.

- TITLE: Example Support Article
- AUDIENCE: Students
- TAGS: login, sign-in, account
- CONTEXT:
  - What this helps with:
- STEPS:
  - How to sign in:
- IF NOT FIXED:
  - If you're still stuck:
- ESCALATE:
  - If you're still stuck:
```

## Field Semantics

### `TITLE`

Short name for the guide-ready article.

### `AUDIENCE`

Expected audience, such as:

- Students
- Faculty
- Staff

### `TAGS`

Comma-separated keywords for maintenance and authoring clarity.

### `CONTEXT`

Short explanatory text or section references used to populate the guided response context panel.

### `STEPS`

Primary troubleshooting or procedure steps. These should resolve to at least one usable step.

### `IF NOT FIXED`

Next-step troubleshooting shown when the user indicates the first pass did not solve the issue.

### `ESCALATE`

Escalation guidance for the guided flow. This should resolve to actionable support guidance.

## Validation

Run:

```bash
./venv/bin/python validate_kb.py
```

The validator checks:

- required fields for guide-ready articles
- empty `TITLE`, `AUDIENCE`, or `TAGS`
- heading references that do not exist in the same file
- whether `STEPS` resolves to usable step content
- whether `ESCALATE` resolves to escalation text
