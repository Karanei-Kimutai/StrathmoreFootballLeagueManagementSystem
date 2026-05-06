# Strathmore Football League Management System

A focused Flask and PostgreSQL web app for running the Strathmore University campus football league. The project has been trimmed to the workflows the league needs day to day: team registration, squad management, fixture generation, result entry, player match stats, and public league browsing.

## What The App Does

The system has two main experiences:

- Public/user experience: view the league table, fixtures, teams, players, match profiles, and player statistics.
- Admin experience: register teams, manage squads, create fixtures, record match scores, and capture player stats such as goals, assists, yellow cards, and red cards.

The app is intentionally scoped to a single Strathmore league instead of a broad multi-league football database.

## Core Features

- Admin login and role-based access
- Automatic initial admin creation when the database is first initialized
- Team registration
- Squad/player management
- Round-robin fixture generation
- Match score entry
- Per-match player statistics
- Dynamic league standings calculation
- Search for teams and players
- Public profiles for leagues, teams, players, and matches

## Tech Stack

- Python 3
- Flask
- PostgreSQL
- Psycopg2
- Bcrypt
- Tailwind CSS and a small custom compatibility stylesheet
- Docker and Docker Compose

## Project Structure

```text
.
├── main.py              # Flask app setup, auth, landing page, search, profile routes
├── admin_routes.py      # Admin team, player, fixture, and score workflows
├── user_routes.py       # Public/user browsing routes and profile pages
├── utils.py             # Fixture generation and standings calculation
├── db.py                # PostgreSQL connection helper
├── config.py            # Environment-based app configuration
├── schema.sql           # Minimal database schema and starter league/season/pitch seed
├── init-db.sh           # PostgreSQL role/database initialization helper
├── create-admin.sh      # Initial web app admin seed
├── docker-compose.yml   # App and PostgreSQL services
├── Dockerfile           # Flask app container
├── requirements.txt     # Python dependencies
├── templates/           # Jinja templates
└── static/              # CSS and static images
```

## Environment Variables

Create `.env` from `.env.example` before running the app:

```sh
cp .env.example .env
```

Required values:

```text
FLASK_APP=main.py
FLASK_ENV=development
SECRET_KEY=your_secret_key_here

POSTGRES_USER=sports_league_owner
POSTGRES_PASSWORD=sports_league_password
POSTGRES_DB=sports_league
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}

APP_ADMIN_USERNAME=SFLAdmin
APP_ADMIN_PASSWORD=password
APP_ADMIN_EMAIL=admin@strathmore.edu
```

`APP_ADMIN_USERNAME`, `APP_ADMIN_PASSWORD`, and `APP_ADMIN_EMAIL` are used by `create-admin.sh` when PostgreSQL initializes a fresh database volume.


## Setup & Development Workflows

You can run the app using either Docker (recommended for most users) or set up everything locally on your machine. Both workflows are supported and described below.

### Docker Workflow (Recommended)

- Handles all dependencies and database setup automatically.
- Start the app and database:

  ```sh
  docker compose up --build
  ```

- Open the app at: http://localhost:5000
- The database service runs initialization scripts (`init-db.sh`, `schema.sql`, `create-admin.sh`) on first creation.
- After startup, log in with the admin credentials from your `.env`.
- To reset the database, remove the volume:

  ```sh
  docker compose down -v
  docker compose up --build
  ```

- To seed the database with demo data for development/testing:

  ```sh
  docker compose exec web python seed.py
  ```

### Local Setup Workflow (Windows)

- Use the provided PowerShell script `setup-local-db.ps1` to automate local PostgreSQL setup:
  1. Creates the required PostgreSQL user and database.
  2. Loads the schema from `schema.sql`.
  3. Prints the connection string for your `.env` file.
- Configure your environment variables in `.env` as described above.
- The app uses `config.py` to load these variables and provide secure, flexible configuration for Flask and database access.
- Install dependencies:

  ```sh
  pip install -r requirements.txt
  ```

- Start the app with `flask run` after installing dependencies and setting up the database.
- For local non-Docker runs, set `DATABASE_URL` to a host-accessible PostgreSQL URL, for example:

  ```text
  DATABASE_URL=postgresql://sports_league_owner:sports_league_password@localhost:5432/sports_league
  ```

> **Note:** The local setup script is intended for Windows/PowerShell users. For Mac/Linux, set up PostgreSQL manually or use Docker.

#### Running the PowerShell Setup Script (Windows)

To set up the local PostgreSQL database using PowerShell:

1. Open PowerShell as Administrator.
2. Navigate to your project directory.
3. Run the following command:

   ```sh
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
   ./setup-local-db.ps1
   ```

This will create the database, user, and load the schema automatically. The script will print the connection string to use in your `.env` file.

## Demo Data Functionality

The admin panel includes convenient controls to quickly load or clear demo data for demonstrations and testing:

- **Load Demo Data**: Instantly populate the league with 10 teams, 100 players, 45 fixtures, and 30 completed matches (with player stats). This is useful for demos or development.
- **Clear Demo Data**: Remove all teams, players, matches, scores, and player stats, returning the system to a clean state. The league and admin account are preserved.

These actions are available from the admin dashboard UI. No manual script execution is required—just use the buttons provided in the admin panel under "Demo Controls."

> **Note:** Loading demo data will overwrite any existing league data. Use the clear function to reset the system as needed.

## Admin Workflow

1. Log in with the seeded admin account.
2. Open the admin dashboard.
3. Register teams.
4. Add players to team squads.
5. Generate fixtures once enough teams exist.
6. Record match results.
7. Add player stats while entering or editing scores.

Fixtures are generated as a single round-robin using the helper in `utils.py`.

## Public/User Workflow

Visitors can browse:

- League table
- Fixtures
- Teams
- Players
- League profiles
- Team profiles
- Player profiles and aggregated stats
- Match profiles and per-match player stats

Public sign-up is intentionally disabled. The app uses a single seeded admin account for management, while league browsing remains public.

## Database Overview

The trimmed schema keeps only the tables needed by the app:

- `users`
- `leagues`
- `seasons`
- `stadiums`
- `coaches`
- `teams`
- `players`
- `matches`
- `scores`
- `player_match_stats`

Standings are calculated dynamically from matches and scores rather than stored as a separate table.

## Useful Commands

Check Python syntax:

```sh
python -B -m py_compile main.py admin_routes.py user_routes.py utils.py config.py db.py
```

View current Git status:

```sh
git status --short
```

Rebuild containers:

```sh
docker compose up --build
```

Start from a clean development database:

```sh
docker compose down -v
docker compose up --build
```

## Notes For Maintainers

- Keep `.env` local and uncommitted.
- Use `.env.example` for shared configuration defaults.
- `create-admin.sh` is only for initial database creation in Docker.
- Avoid reintroducing the old broad football dataset scope unless the product direction changes.
- Keep the app centered on Strathmore league operations.

## License

MIT
