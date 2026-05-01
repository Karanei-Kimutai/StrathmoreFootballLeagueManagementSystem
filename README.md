# Strathmore Football League Management System

Campus football league management for Strathmore University.

## Scope

This app focuses on the league workflows the project actually needs:

- Register teams
- Manage team squads
- Generate fixtures
- Record match scores and player stats
- Show the league table, fixtures, teams, players, and match profiles
- Support simple user registration, login, and admin-only management

## Stack

- Flask
- PostgreSQL
- Psycopg2
- Bootstrap with custom CSS
- Docker / Docker Compose

## Setup

1. Copy the environment template:

   ```sh
   cp .env.example .env
   ```

2. Start the app and database:

   ```sh
   docker compose up --build
   ```

   On first database initialization, Docker runs `create-admin.sh` to create the web app admin from:

   ```text
   APP_ADMIN_USERNAME
   APP_ADMIN_PASSWORD
   APP_ADMIN_EMAIL
   ```

3. Open:

   ```text
   http://localhost:5000
   ```

## Local Run Without Docker

```sh
pip install -r requirements.txt
flask run
```

Make sure `DATABASE_URL` points to a PostgreSQL database initialized with `schema.sql`.

## Core Files

- `main.py` - app setup, auth, landing page, profile/search routes
- `admin_routes.py` - admin team, squad, fixture, and score workflows
- `user_routes.py` - public/user league browsing and profiles
- `utils.py` - fixture generation and standings calculation
- `schema.sql` - minimal database schema and starter league seed
- `create-admin.sh` - initial web app admin seed

## License

MIT
