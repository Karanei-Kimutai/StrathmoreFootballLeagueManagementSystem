#!/bin/bash
set -e

APP_ADMIN_USERNAME="${APP_ADMIN_USERNAME:-SFLAdmin}"
APP_ADMIN_PASSWORD="${APP_ADMIN_PASSWORD:-password}"
APP_ADMIN_EMAIL="${APP_ADMIN_EMAIL:-admin@strathmore.edu}"

psql -v ON_ERROR_STOP=1 \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    -v admin_username="$APP_ADMIN_USERNAME" \
    -v admin_password="$APP_ADMIN_PASSWORD" \
    -v admin_email="$APP_ADMIN_EMAIL" <<'SQL'
CREATE EXTENSION IF NOT EXISTS pgcrypto;

UPDATE leagues
SET icon_url = NULL
WHERE icon_url IS NOT NULL;

INSERT INTO users (username, password, email, is_admin)
VALUES (
    :'admin_username',
    crypt(:'admin_password', gen_salt('bf')),
    :'admin_email',
    TRUE
)
ON CONFLICT (username) DO UPDATE
SET is_admin = TRUE,
    email = EXCLUDED.email;
SQL
