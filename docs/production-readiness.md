# Production Readiness Checklist

This checklist is intended for deploying the CCA IT Support Assistant into an internal environment for real student and faculty testing.

## Required Environment Variables

Set these explicitly in the deployment environment:

- `APP_ENV=production`
- `FLASK_SECRET_KEY`
- `LDAP_SERVER`
- `LDAP_PORT`
- `LDAP_DOMAIN`
- `LDAP_USE_SSL`
- `LDAP_REQUIRED_GROUP_DN`
- `ALLOW_DEV_LOGIN=0`

Optional feature flags:

- `IT_SUPPORT_LLM_ENABLED`
- `IT_SUPPORT_LLM_MODEL`
- `OPENAI_API_KEY`
- `IT_SUPPORT_EMBEDDINGS_ENABLED`
- `IT_SUPPORT_SEMANTIC_MIN_SCORE`
- `ENABLE_INTERNAL_KB`
- `INTERNAL_KB_ALLOWED_USERS`
- `INTERNAL_KB_DEFAULT`

## Startup Validation

The app now validates deployment-sensitive configuration on startup.

In production mode (`APP_ENV=production`), startup fails if:

- `FLASK_SECRET_KEY` is missing
- `FLASK_SECRET_KEY` is still using the development fallback
- `ALLOW_DEV_LOGIN=1`
- required LDAP settings are missing
- `ENABLE_INTERNAL_KB=1` but `INTERNAL_KB_ALLOWED_USERS` is empty

In non-production mode, these conditions produce warnings instead of failing startup.

## LDAP Validation Steps

Before pilot access is enabled:

1. Confirm the target environment can reach the domain controller.
2. Confirm `ldap3` is installed in the deployed Python environment.
3. Validate one successful login for a real user in the required AD group.
4. Validate one failed login for:
   - invalid credentials
   - a real user not in the required AD group
5. Confirm `/logout` clears the session and redirects back to `/login`.

## Development Login

Development login must be disabled in any shared or production environment:

- `ALLOW_DEV_LOGIN=0`

Do not rely on the temporary fallback credentials outside local development.

## Flask Secret Key

`FLASK_SECRET_KEY` must be:

- explicitly configured
- long and random
- different between environments
- not the development fallback string

## SQLite / Log File Location

SQLite logging currently writes to:

- `it_help_logs.db` in the project root

This includes:

- `request_logs`
- `feedback_logs`

Deployment notes:

- ensure the application process can write to the project directory, or update the path before deployment
- include the database file in backup and retention planning if feedback and request logs are operationally important

## HTTPS Requirement

Run this application behind HTTPS in any real environment.

Do not expose login or support traffic over plain HTTP.

## Gunicorn / Nginx Deployment Notes

Recommended deployment shape:

- Flask app served by Gunicorn
- reverse proxy via Nginx
- HTTPS terminated at Nginx or the platform load balancer

Example operational expectations:

- run Gunicorn with a stable working directory
- pass required environment variables through the process manager
- ensure the static and template files are deployed together with the app
- confirm the SQLite database path is writable by the Gunicorn process

## Post-Deployment Smoke Test

After deployment, verify:

1. App starts without startup configuration errors.
2. `/login` loads over HTTPS.
3. LDAP login succeeds for one authorized test account.
4. Student query works:
   - example: `How do I reset my password?`
5. Faculty query works:
   - example: `Classroom display won’t turn on`
6. Guided follow-up works:
   - submit `No` and confirm additional troubleshooting and escalation appear
7. Feedback write works:
   - submit helpful/unhelpful feedback and confirm a row is written to `feedback_logs`
8. Quality gate passes from the deployed environment or release artifact:
   - `./venv/bin/python check_all.py`

## Recommended Release Gate

Before each deployment:

1. `./venv/bin/python check_all.py`
2. `./venv/bin/python evaluate_pilot_queries.py`
3. manual login and smoke test in the target environment

## Remaining Operational Risks

Current known deployment risks:

- SQLite is simple and local; it is not a multi-node logging solution
- LDAP behavior depends on the target environment and real directory access
- optional LLM and semantic retrieval features add dependency and configuration complexity if enabled
- the guided flow is still stateless and form-based, which is fine for pilot support but not a full case-management workflow
