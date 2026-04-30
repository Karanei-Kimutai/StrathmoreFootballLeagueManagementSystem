# Strathmore Football League Management System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

The Strathmore Football League Management System is a modern, user-friendly platform for managing campus football leagues. It supports teams, players, matches, scores, standings, and detailed player stats, with a clean, responsive UI and streamlined admin workflows.

## Table of Contents
1. [Project Description](#project-description)
2. [Features](#features)
3. [Technologies Used](#technologies-used)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Database Schema](#database-schema)
7. [ER Diagram](#er-diagram)
8. [Screenshots](#screenshots)
9. [License](#license)

## Project Description
This system is designed for university and campus football leagues. It provides:
- Modern, branded UI with custom CSS
- Direct front page access to league table and upcoming fixtures
- Clean separation of admin and user workflows
- Player match stats (goals, assists, cards) and advanced standings
- Easy management of teams, squads, fixtures, and results

## Features
- Modern, responsive UI (custom CSS, Bootstrap base)
- League table and upcoming fixtures on the front page
- Admin panel for registering teams, managing squads, generating fixtures, and recording results
- Player match stats: goals, assists, yellow/red cards
- User dashboard for browsing teams, players, matches, and standings
- Search for teams and players
- Secure authentication and role-based access

## Technologies Used
- **Frontend:** HTML, Custom CSS (modern, branded), Bootstrap, JavaScript
- **Backend:** Flask (Python)
- **Database:** PostgreSQL
- **Other Libraries:** Psycopg2, Python-Dotenv, Werkzeug

## Installation

### Prerequisites
- Docker and Docker Compose installed on your system
- Git for cloning the repository

### Setup Steps
1. Clone the repository:
   ```sh
   git clone https://github.com/yourusername/sports-league-management.git
   cd sports-league-management
   ```

2. Set up the environment variables:
   ```sh
   # The setup script will automatically create .env from .env.example if it doesn't exist
   cp .env.example .env
   ```
   Edit the `.env` file and set your environment variables:
   - `POSTGRES_USER`: Database username
   - `POSTGRES_PASSWORD`: Database password
   - `POSTGRES_DB`: Database name
   - `FOOTBALL_DATA_API_KEY`: Your API token from football-data.org
   - Other configuration variables as needed

3. Run the setup script:
   ```sh
   chmod +x setup.sh
   ./setup.sh
   ```
   This will:
   - Check if Docker is running
   - Create necessary environment files
   - Build and start the Docker containers

The application will be available at `http://localhost:5000`

### Manual Setup (Without Docker)
If you prefer to run the application without Docker:

1. Create and activate a virtual environment:
   ```sh
   python3 -m venv env
   source env/bin/activate
   ```

2. Install dependencies using Poetry:
   ```sh
   pip install poetry
   poetry install
   ```
   
   Or using pip:
   ```sh
   pip install -r requirements.txt
   ```

3. Set up PostgreSQL database and run the schema:
   ```sh
   psql -U your_username -d your_database -a -f schema.sql
   ```

4. Run the application:
   ```sh
   flask run
   ```

## Usage
### Admin Panel
- **Register Teams:** Add and manage teams (with squad status)
- **Manage Squads:** Add players to teams
- **Generate Fixtures:** Auto-generate round-robin fixtures
- **Record Results:** Enter match results and player stats (goals, assists, cards)
- **Encapsulated Admin UI:** All admin actions are accessible only after logging in as admin

### User Dashboard
- **League Table:** View up-to-date standings
- **Upcoming Fixtures:** See next matches on the front page
- **Teams & Players:** Browse teams, player profiles, and stats
- **Match Profiles:** View match details and player stats
- **Search:** Find teams and players quickly

## 🎯 Kaggle Dataset
The data from this system is now available as a public dataset on Kaggle:
[European Football Leagues Database 2023-2024](https://www.kaggle.com/datasets/kamrangayibov/football-data-european-top-5-leagues)

Features of the dataset:
- Complete statistics for top 5 European leagues
- Weekly automated updates
- Available in both CSV and SQLite formats
- Comprehensive documentation and usage examples
- Clean, validated data with proper relationships

## Database Schema
The database schema is designed to minimize redundancy and ensure data integrity by using foreign keys and transactions. The main entities include users, stadiums, leagues, seasons, teams, coaches, players, matches, scores, scorers, standings, referees, and match referees.

## ER Diagram
The ER diagram illustrates the relationships between different entities in the Sports League Management System. Each table represents an entity, and the lines between them represent relationships. Primary keys are indicated by the underlined attributes, and foreign keys are shown as arrows pointing to the related primary keys.

![ER Diagram](img/dbms-diagram.png)

## Screenshots
### Main Starting Screen
![Main Starting Screen](img/landing_screen.png)

### Login Screen
![Login Screen](img/login_screen.png)

### User Dashboard
![User Dashboard](img/user_dashboard_screen.png)


### Player Stats & Standings
Player match stats (goals, assists, yellow/red cards) are tracked and shown in match and player profiles. Standings are calculated with advanced tiebreakers (points, goal difference, head-to-head).

### Matches Screen
![Matches Screen](img/match_screen.png)

### Teams Screen
![Teams Screen](img/teams_screen.png)

### Player Profiles Screen
![Player Profiles Screen](img/player_screen.png)

### League Profiles Screen
![League Profiles Screen](img/league_screen.png)

### Manage Teams Screen
![Manage Teams Screen](img/manage_teams_screen.png)

### Match Profile Screen
![Match Profile Screen](img/match_profile_screen.png)

### League Profile Screen
![League Profile Screen](img/league_profile_screen.png)


### Standings
![Standings](img/standings.png)

### Team Profile Screen
![Team Profile Screen](img/team_profile_screen.png)

### Player Profile Screen
![Player Profile Screen](img/player_profile_screen.png)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
