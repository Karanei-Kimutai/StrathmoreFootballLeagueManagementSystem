"""
Strathmore Football League - Database Seed Script
--------------------------------------------------
Seeds the database with:
- 10 teams
- 10 players per team (100 players total)
- Round-robin fixtures (45 matches)
- Scores for ~30 matches
- Player match stats for scored matches

Usage:
    python seed.py

Requires DATABASE_URL in environment or a .env file.
"""

import os
import random
import psycopg2
from dotenv import load_dotenv
from itertools import combinations
from datetime import date, timedelta

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Check your .env file.")

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

TEAM_NAMES = [
    "Strathmore United",
    "Madaraka FC",
    "Gamba Lions",
    "East Side Rovers",
    "Valley Rangers",
    "Campus Wolves",
    "Nairobi Knights",
    "Blue Eagles FC",
    "Red Storm",
    "Golden Boys",
]

MANAGER_NAMES = [
    "James Mwangi",
    "Peter Odhiambo",
    "Samuel Kipchoge",
    "Daniel Otieno",
    "Michael Kamau",
    "Brian Mutua",
    "Kevin Njoroge",
    "Patrick Wekesa",
    "Joseph Auma",
    "Charles Maina",
]

# 10 players per team — Kenyan-flavoured names
PLAYERS_PER_TEAM = [
    [
        "Allan Ochieng", "Brian Simiyu", "Calvin Mwenda", "Dennis Korir",
        "Edwin Chebet", "Felix Mutiso", "George Nganga", "Henry Kariuki",
        "Ian Njuguna", "Joel Wanjiku",
    ],
    [
        "Aaron Barasa", "Benson Odongo", "Clinton Rotich", "David Sang",
        "Emmanuel Kiptoo", "Francis Kigen", "Gerald Muriuki", "Harrison Gitau",
        "Isaac Macharia", "James Kimani",
    ],
    [
        "Adrian Wafula", "Bernard Wesonga", "Clement Musyoka", "Duncan Mwangi",
        "Eric Mulwa", "Fredrick Onyango", "Gilbert Waweru", "Herbert Maina",
        "Ivan Kibet", "John Kamande",
    ],
    [
        "Alfred Ogolla", "Bob Makori", "Chris Ndung'u", "Derek Ayieko",
        "Elias Omolo", "Franklin Cheruiyot", "Graham Muthoka", "Hudson Omondi",
        "Irving Wangari", "Julius Otieno",
    ],
    [
        "Andrew Mugo", "Benedict Oloo", "Cornelius Langat", "Dixon Mwamba",
        "Elijah Nderi", "Ferdinand Mutua", "Gideon Kirui", "Humphrey Njeru",
        "Ike Otiende", "Jonathan Kiplagat",
    ],
    [
        "Alex Njoroge", "Boniface Onyango", "Collins Mukundi", "Damian Owiti",
        "Elvis Kamau", "Frank Wanyama", "Gordon Mwiti", "Hilary Opiyo",
        "Ibrahim Mwangi", "Joseph Kimetto",
    ],
    [
        "Albert Odour", "Ben Muriithi", "Craig Omondi", "Dan Wachira",
        "Edward Kipchoge", "Fred Ndegwa", "Greg Mutua", "Hans Omwega",
        "Innocent Koskei", "Jake Wekesa",
    ],
    [
        "Alvin Ouma", "Boris Munyao", "Curtis Kirwa", "Dave Mwenda",
        "Enoch Chelimo", "Fraser Ndungu", "Godwin Orimba", "Hector Murigi",
        "Irvin Keter", "Jason Muthee",
    ],
    [
        "Amos Mwaniki", "Bruno Ochieng", "Conrad Njogu", "Derick Koech",
        "Eugene Nyambura", "Fabian Rotich", "Godfrey Ochieng", "Hugo Ndwiga",
        "Ismail Kipkemoi", "Jay Gachoki",
    ],
    [
        "Anthony Odera", "Byron Mutuku", "Caleb Njau", "Dixon Otieno",
        "Evan Kimani", "Festus Waweru", "Grant Muturi", "Harold Oduya",
        "Isaiah Chesire", "Jefferson Kuria",
    ],
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def generate_round_robin(team_ids):
    """Return list of rounds, each round is a list of (home_id, away_id)."""
    teams = list(team_ids)
    if len(teams) % 2:
        teams.append(None)
    n = len(teams)
    rounds = []
    for round_index in range(n - 1):
        pairings = []
        for i in range(n // 2):
            home = teams[i]
            away = teams[n - 1 - i]
            if home is None or away is None:
                continue
            if round_index % 2:
                home, away = away, home
            pairings.append((home, away))
        rounds.append(pairings)
        teams = [teams[0], teams[-1]] + teams[1:-1]
    return rounds


def random_score():
    """Return (home_goals, away_goals) biased toward low scores."""
    home = random.choices([0, 1, 2, 3, 4], weights=[20, 35, 25, 15, 5])[0]
    away = random.choices([0, 1, 2, 3, 4], weights=[25, 35, 22, 13, 5])[0]
    return home, away


def half_time_score(full_home, full_away):
    """Return plausible half-time score."""
    ht_home = random.randint(0, full_home)
    ht_away = random.randint(0, full_away)
    return ht_home, ht_away


def match_date(matchday):
    """Spread matches weekly from a start date in the current season."""
    start = date(date.today().year, 1, 15)
    return start + timedelta(weeks=matchday - 1)


# ---------------------------------------------------------------------------
# Seed
# ---------------------------------------------------------------------------

def seed():
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("Connecting to database...")

    # ---- Check / get league & season ----------------------------------------
    cur.execute("SELECT league_id FROM leagues ORDER BY league_id LIMIT 1")
    league_row = cur.fetchone()
    if not league_row:
        cur.execute(
            "INSERT INTO leagues (name, country, cl_spot, uel_spot, relegation_spot) "
            "VALUES (%s, %s, %s, %s, %s) RETURNING league_id",
            ("Strathmore Football League", "Kenya", 0, 0, 999),
        )
        league_id = cur.fetchone()[0]
        print(f"  Created league (id={league_id})")
    else:
        league_id = league_row[0]
        print(f"  Using existing league (id={league_id})")

    cur.execute(
        "SELECT season_id FROM seasons WHERE league_id = %s ORDER BY season_id DESC LIMIT 1",
        (league_id,),
    )
    season_row = cur.fetchone()
    if not season_row:
        cur.execute(
            "INSERT INTO seasons (league_id, year) VALUES (%s, %s) RETURNING season_id",
            (league_id, str(date.today().year)),
        )
        season_id = cur.fetchone()[0]
        print(f"  Created season (id={season_id})")
    else:
        season_id = season_row[0]
        print(f"  Using existing season (id={season_id})")

    # ---- Stadium -------------------------------------------------------------
    cur.execute("SELECT stadium_id FROM stadiums WHERE name = 'Campus pitch' LIMIT 1")
    stadium_row = cur.fetchone()
    if not stadium_row:
        cur.execute(
            "INSERT INTO stadiums (name, location, capacity) VALUES (%s, %s, %s) RETURNING stadium_id",
            ("Campus pitch", "Strathmore University", None),
        )
        stadium_id = cur.fetchone()[0]
    else:
        stadium_id = stadium_row[0]

    # ---- Wipe existing seed data for a clean re-run -------------------------
    print("  Clearing existing teams, players, matches, scores, stats...")
    cur.execute("DELETE FROM player_match_stats WHERE match_id IN (SELECT match_id FROM matches WHERE league_id = %s)", (league_id,))
    cur.execute("DELETE FROM scores WHERE match_id IN (SELECT match_id FROM matches WHERE league_id = %s)", (league_id,))
    cur.execute("DELETE FROM matches WHERE league_id = %s", (league_id,))
    cur.execute("DELETE FROM players WHERE team_id IN (SELECT team_id FROM teams WHERE league_id = %s)", (league_id,))
    cur.execute("DELETE FROM teams WHERE league_id = %s", (league_id,))

    # ---- Teams ---------------------------------------------------------------
    print("Seeding teams...")
    team_ids = []
    for i, (name, manager) in enumerate(zip(TEAM_NAMES, MANAGER_NAMES)):
        cur.execute(
            "INSERT INTO teams (name, manager_name, stadium_id, league_id) "
            "VALUES (%s, %s, %s, %s) RETURNING team_id",
            (name, manager, stadium_id, league_id),
        )
        team_id = cur.fetchone()[0]
        team_ids.append(team_id)
        print(f"  {name} (id={team_id})")

    # ---- Players -------------------------------------------------------------
    print("Seeding players...")
    # Map team_id -> list of player_ids (needed for stats)
    team_player_ids = {}
    for team_id, player_names in zip(team_ids, PLAYERS_PER_TEAM):
        ids = []
        for name in player_names:
            cur.execute(
                "INSERT INTO players (team_id, name) VALUES (%s, %s) RETURNING player_id",
                (team_id, name),
            )
            ids.append(cur.fetchone()[0])
        team_player_ids[team_id] = ids
        print(f"  Inserted {len(ids)} players for team_id={team_id}")

    # ---- Fixtures (round-robin) ---------------------------------------------
    print("Generating fixtures...")
    rounds = generate_round_robin(team_ids)
    match_ids_by_round = {}  # matchday -> list of (match_id, home_id, away_id)
    for matchday, pairings in enumerate(rounds, start=1):
        match_ids_by_round[matchday] = []
        mdate = match_date(matchday)
        for home_id, away_id in pairings:
            cur.execute(
                "INSERT INTO matches (season_id, league_id, matchday, home_team_id, away_team_id, utc_date, status) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING match_id",
                (season_id, league_id, matchday, home_id, away_id, mdate, "Scheduled"),
            )
            match_id = cur.fetchone()[0]
            match_ids_by_round[matchday].append((match_id, home_id, away_id))
    total_matches = sum(len(v) for v in match_ids_by_round.values())
    print(f"  Created {total_matches} fixtures across {len(rounds)} matchdays")

    # ---- Scores for first 6 matchdays (30 matches) --------------------------
    print("Seeding scores and player stats...")
    MATCHDAYS_TO_SCORE = 6
    scored = 0
    for matchday in range(1, MATCHDAYS_TO_SCORE + 1):
        for match_id, home_id, away_id in match_ids_by_round[matchday]:
            ft_home, ft_away = random_score()
            ht_home, ht_away = half_time_score(ft_home, ft_away)

            cur.execute(
                "INSERT INTO scores (match_id, full_time_home, full_time_away, half_time_home, half_time_away) "
                "VALUES (%s, %s, %s, %s, %s)",
                (match_id, ft_home, ft_away, ht_home, ht_away),
            )
            cur.execute(
                "UPDATE matches SET status = 'Completed' WHERE match_id = %s",
                (match_id,),
            )
            scored += 1

            # ---- Player stats -----------------------------------------------
            home_players = team_player_ids[home_id]
            away_players = team_player_ids[away_id]

            # Distribute goals among home scorers
            goals_left = ft_home
            for _ in range(ft_home):
                scorer = random.choice(home_players)
                cur.execute(
                    """
                    INSERT INTO player_match_stats (player_id, match_id, goals, assists, yellow_cards, red_cards)
                    VALUES (%s, %s, 1, 0, 0, 0)
                    ON CONFLICT DO NOTHING
                    """,
                    (scorer, match_id),
                )
                # Add assist ~70% of the time
                if random.random() < 0.7:
                    assister = random.choice([p for p in home_players if p != scorer] or home_players)
                    cur.execute(
                        """
                        INSERT INTO player_match_stats (player_id, match_id, goals, assists, yellow_cards, red_cards)
                        VALUES (%s, %s, 0, 1, 0, 0)
                        ON CONFLICT DO NOTHING
                        """,
                        (assister, match_id),
                    )

            # Distribute goals among away scorers
            for _ in range(ft_away):
                scorer = random.choice(away_players)
                cur.execute(
                    """
                    INSERT INTO player_match_stats (player_id, match_id, goals, assists, yellow_cards, red_cards)
                    VALUES (%s, %s, 1, 0, 0, 0)
                    ON CONFLICT DO NOTHING
                    """,
                    (scorer, match_id),
                )
                if random.random() < 0.7:
                    assister = random.choice([p for p in away_players if p != scorer] or away_players)
                    cur.execute(
                        """
                        INSERT INTO player_match_stats (player_id, match_id, goals, assists, yellow_cards, red_cards)
                        VALUES (%s, %s, 0, 1, 0, 0)
                        ON CONFLICT DO NOTHING
                        """,
                        (assister, match_id),
                    )

            # Yellow cards — 1-3 random players per match
            all_players = home_players + away_players
            for player in random.sample(all_players, k=random.randint(1, 3)):
                cur.execute(
                    """
                    INSERT INTO player_match_stats (player_id, match_id, goals, assists, yellow_cards, red_cards)
                    VALUES (%s, %s, 0, 0, 1, 0)
                    ON CONFLICT DO NOTHING
                    """,
                    (player, match_id),
                )

            # Red card — ~15% chance, one player
            if random.random() < 0.15:
                player = random.choice(all_players)
                cur.execute(
                    """
                    INSERT INTO player_match_stats (player_id, match_id, goals, assists, yellow_cards, red_cards)
                    VALUES (%s, %s, 0, 0, 0, 1)
                    ON CONFLICT DO NOTHING
                    """,
                    (player, match_id),
                )

    print(f"  Scored {scored} matches with player stats")

    conn.commit()
    cur.close()
    conn.close()

    print("\nSeed complete!")
    print(f"  Teams:    {len(TEAM_NAMES)}")
    print(f"  Players:  {len(TEAM_NAMES) * 10}")
    print(f"  Fixtures: {total_matches}")
    print(f"  Scored:   {scored} matches ({MATCHDAYS_TO_SCORE} matchdays)")
    print(f"  Remaining {total_matches - scored} matches are 'Scheduled'")


if __name__ == "__main__":
    seed()