# Deployment Runbook

This runbook describes how to deploy the CCA IT Support Assistant on a Linux VM using Gunicorn, Nginx, HTTPS, and environment variables.

## Assumptions

- Linux VM
- Python 3 available
- application code deployed from this repository
- repository cloned to a stable deployment directory
- a dedicated service account is available
- Nginx is installed
- a TLS certificate is available now or will be installed before production traffic is enabled

Example assumptions used below:

- deploy user: `cca-assistant`
- app directory: `/opt/cca-it-support-assistant`
- virtual environment: `/opt/cca-it-support-assistant/venv`
- environment file: `/etc/cca-it-support-assistant.env`
- systemd unit: `cca-it-support-assistant.service`
- Gunicorn bind: `127.0.0.1:8000`

## Setup Steps

### 1. Clone the repository

```bash
sudo mkdir -p /opt/cca-it-support-assistant
sudo chown -R cca-assistant:cca-assistant /opt/cca-it-support-assistant
sudo -u cca-assistant git clone <REPO_URL> /opt/cca-it-support-assistant
```

### 2. Create a virtual environment

```bash
cd /opt/cca-it-support-assistant
python3 -m venv venv
source venv/bin/activate
```

### 3. Install requirements

```bash
cd /opt/cca-it-support-assistant
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
```

### 4. Create the production environment file

Create `/etc/cca-it-support-assistant.env`:

```bash
sudo tee /etc/cca-it-support-assistant.env >/dev/null <<'EOF'
APP_ENV=production
FLASK_SECRET_KEY=<SET_A_LONG_RANDOM_SECRET>

LDAP_SERVER=CCCDC01.ccc.ccofc.edu
LDAP_PORT=389
LDAP_DOMAIN=ccc.ccofc.edu
LDAP_USE_SSL=0
LDAP_REQUIRED_GROUP_DN=CN=CCA_Leslie_Project,OU=CCA_Groups_Security_User,OU=CCA,DC=ccc,DC=ccofc,DC=edu

ALLOW_DEV_LOGIN=0

# Optional features
# IT_SUPPORT_LLM_ENABLED=0
# IT_SUPPORT_LLM_MODEL=
# OPENAI_API_KEY=
# IT_SUPPORT_EMBEDDINGS_ENABLED=0
# IT_SUPPORT_SEMANTIC_MIN_SCORE=0.45
# ENABLE_INTERNAL_KB=0
# INTERNAL_KB_ALLOWED_USERS=
# INTERNAL_KB_DEFAULT=0
EOF
```

Protect the file:

```bash
sudo chown root:cca-assistant /etc/cca-it-support-assistant.env
sudo chmod 640 /etc/cca-it-support-assistant.env
```

### 5. Confirm required production settings

Before starting the service, confirm:

- `APP_ENV=production`
- `FLASK_SECRET_KEY` is set and not using the development fallback
- LDAP variables are set explicitly
- `ALLOW_DEV_LOGIN=0`
- if `ENABLE_INTERNAL_KB=1`, `INTERNAL_KB_ALLOWED_USERS` contains only approved staff usernames

## Gunicorn Command

Example Gunicorn command:

```bash
cd /opt/cca-it-support-assistant
source venv/bin/activate
set -a
source /etc/cca-it-support-assistant.env
set +a
gunicorn --workers 3 --bind 127.0.0.1:8000 app:app
```

Notes:

- the WSGI app reference is `app:app`
- bind Gunicorn only to localhost and let Nginx handle public traffic

## systemd Service

Example unit file: `/etc/systemd/system/cca-it-support-assistant.service`

```ini
[Unit]
Description=CCA IT Support Assistant
After=network.target

[Service]
Type=simple
User=cca-assistant
Group=cca-assistant
WorkingDirectory=/opt/cca-it-support-assistant
EnvironmentFile=/etc/cca-it-support-assistant.env
ExecStart=/opt/cca-it-support-assistant/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 app:app
Restart=always
RestartSec=5
TimeoutStopSec=30

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable cca-it-support-assistant
sudo systemctl start cca-it-support-assistant
sudo systemctl status cca-it-support-assistant
```

## Nginx Reverse Proxy

Example Nginx config:

`/etc/nginx/sites-available/cca-it-support-assistant`

```nginx
server {
    listen 80;
    server_name support.example.edu;

    # Replace with your HTTPS redirect policy once certificates are ready
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name support.example.edu;

    ssl_certificate /path/to/fullchain.pem;
    ssl_certificate_key /path/to/privkey.pem;

    client_max_body_size 10m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

Enable and reload:

```bash
sudo ln -s /etc/nginx/sites-available/cca-it-support-assistant /etc/nginx/sites-enabled/cca-it-support-assistant
sudo nginx -t
sudo systemctl reload nginx
```

## Post-Deployment Smoke Test

Run these checks after deployment:

1. The app loads over HTTPS.
2. An authorized LDAP user can log in.
3. An unauthorized or wrong-group user cannot log in.
4. A student query works.
   - Example: `How do I reset my password?`
5. A faculty query works.
   - Example: `Classroom display won’t turn on`
6. Feedback writes successfully.
   - Submit feedback and confirm a row is added to `feedback_logs`.
7. The quality gate passes on the server:

```bash
cd /opt/cca-it-support-assistant
./venv/bin/python check_all.py
./venv/bin/python evaluate_pilot_queries.py
```

## Rollback Plan

If a deployment fails:

1. Stop the service:

```bash
sudo systemctl stop cca-it-support-assistant
```

2. Revert to the previous application version:

```bash
cd /opt/cca-it-support-assistant
sudo -u cca-assistant git log --oneline -n 5
sudo -u cca-assistant git checkout <PREVIOUS_COMMIT_OR_TAG>
```

3. Reinstall requirements if dependencies changed:

```bash
cd /opt/cca-it-support-assistant
./venv/bin/pip install -r requirements.txt
```

4. Restart the service:

```bash
sudo systemctl start cca-it-support-assistant
sudo systemctl status cca-it-support-assistant
```

5. Re-run the smoke test.

## Operational Notes

### SQLite database location

The SQLite database currently lives at:

- `/opt/cca-it-support-assistant/it_help_logs.db`

This contains:

- `request_logs`
- `feedback_logs`

Ensure the service account can write to the application directory.

### Logs

Operational logs should be reviewed from:

- `journalctl -u cca-it-support-assistant`
- Nginx access and error logs

Example:

```bash
sudo journalctl -u cca-it-support-assistant -n 200 --no-pager
sudo tail -n 200 /var/log/nginx/access.log
sudo tail -n 200 /var/log/nginx/error.log
```

### Reviewing feedback

Feedback is stored in SQLite. Example read-only inspection:

```bash
cd /opt/cca-it-support-assistant
sqlite3 it_help_logs.db "SELECT id, created_at, request_log_id, helpful FROM feedback_logs ORDER BY id DESC LIMIT 20;"
```

### Updating the knowledge base safely

Recommended update workflow:

1. edit public KB articles in `content/public/` or staff-only SOPs in `content/internal/`
2. run:

```bash
./venv/bin/python validate_kb.py
./venv/bin/python check_all.py
./venv/bin/python evaluate_pilot_queries.py
```

3. manually smoke test one student query and one faculty query
4. deploy only after all checks pass
