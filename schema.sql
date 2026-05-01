CREATE TABLE IF NOT EXISTS leagues (
    league_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    country VARCHAR(100) DEFAULT 'Kenya',
    icon_url TEXT,
    cl_spot INTEGER DEFAULT 0,
    uel_spot INTEGER DEFAULT 0,
    relegation_spot INTEGER DEFAULT 999
);

CREATE TABLE IF NOT EXISTS seasons (
    season_id SERIAL PRIMARY KEY,
    league_id INTEGER NOT NULL REFERENCES leagues(league_id) ON DELETE CASCADE,
    year VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS stadiums (
    stadium_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    capacity INTEGER
);

CREATE TABLE IF NOT EXISTS teams (
    team_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    founded_year INTEGER,
    stadium_id INTEGER REFERENCES stadiums(stadium_id) ON DELETE SET NULL,
    league_id INTEGER NOT NULL REFERENCES leagues(league_id) ON DELETE CASCADE,
    coach_id INTEGER,
    crestURL TEXT
);

CREATE TABLE IF NOT EXISTS coaches (
    coach_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    team_id INTEGER REFERENCES teams(team_id) ON DELETE SET NULL,
    nationality VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS players (
    player_id SERIAL PRIMARY KEY,
    team_id INTEGER NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    position VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    nationality VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS matches (
    match_id SERIAL PRIMARY KEY,
    season_id INTEGER NOT NULL REFERENCES seasons(season_id) ON DELETE CASCADE,
    league_id INTEGER NOT NULL REFERENCES leagues(league_id) ON DELETE CASCADE,
    matchday INTEGER,
    home_team_id INTEGER NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    away_team_id INTEGER NOT NULL REFERENCES teams(team_id) ON DELETE CASCADE,
    winner VARCHAR(255),
    utc_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'Pending'
);

CREATE TABLE IF NOT EXISTS scores (
    score_id SERIAL PRIMARY KEY,
    match_id INTEGER NOT NULL UNIQUE REFERENCES matches(match_id) ON DELETE CASCADE,
    full_time_home INTEGER,
    full_time_away INTEGER,
    half_time_home INTEGER,
    half_time_away INTEGER
);

CREATE TABLE IF NOT EXISTS player_match_stats (
    id SERIAL PRIMARY KEY,
    player_id INTEGER NOT NULL REFERENCES players(player_id) ON DELETE CASCADE,
    match_id INTEGER NOT NULL REFERENCES matches(match_id) ON DELETE CASCADE,
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    is_admin BOOLEAN DEFAULT FALSE
);

INSERT INTO leagues (name, country, cl_spot, uel_spot, relegation_spot)
VALUES ('Strathmore Football League', 'Kenya', 0, 0, 999)
ON CONFLICT DO NOTHING;

UPDATE leagues
SET icon_url = NULL
WHERE name = 'Strathmore Football League';

INSERT INTO seasons (league_id, year)
SELECT league_id, EXTRACT(YEAR FROM CURRENT_DATE)::TEXT
FROM leagues
WHERE name = 'Strathmore Football League'
  AND NOT EXISTS (
      SELECT 1
      FROM seasons
      WHERE seasons.league_id = leagues.league_id
  );

INSERT INTO stadiums (name, location, capacity)
SELECT 'Campus pitch', 'Strathmore University', NULL
WHERE NOT EXISTS (
    SELECT 1 FROM stadiums WHERE name = 'Campus pitch'
);
