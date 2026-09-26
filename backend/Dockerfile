FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

# Migrate, then bootstrap the workspace (default org + team + admin user,
# idempotent) and start the server.
#
# The demo dataset is NOT loaded by default — a production deployment starts
# empty. To load it, set TECHFLOW_SEED_DEMO=1 in .env (e.g. for a demo
# server). The admin password comes from TECHFLOW_ADMIN_PASSWORD; when unset,
# a strong password is generated and printed to the container log once
# (docker compose logs backend | grep Password).
CMD ["sh", "-c", "set -eu; python manage.py migrate --noinput; python manage.py create_admin --print-password; if [ \"${TECHFLOW_SEED_DEMO:-0}\" = \"1\" ]; then python manage.py seed_demo --if-empty; fi; python manage.py runserver 0.0.0.0:8000"]
