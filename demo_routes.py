from flask import Blueprint, redirect, url_for, flash, session
from functools import wraps
from db import get_db
from datetime import date, timedelta
import random

demo_bp = Blueprint('demo', __name__)

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            flash('Admin access required', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

# --- same data as seed.py ---

TEAM_NAMES = [
    "Strathmore United", "Madaraka FC", "Gamba Lions", "East Side Rovers",
    "Valley Rangers", "Campus Wolves", "Nairobi Knights", "Blue Eagles FC",
    "Red Storm", "Golden Boys",
]

MANAGER_NAMES = [
    "James Mwangi", "Peter Odhiambo", "Samuel Kipchoge", "Daniel Otieno",
    "Michael Kamau", "Brian Mutua", "Kevin Njoroge", "Patrick Wekesa",
    "Joseph Auma", "Charles Maina",
]

PLAYERS_PER_TEAM = [
    ["Allan Ochieng","Brian Simiyu","Calvin Mwenda","Dennis Korir","Edwin Chebet","Felix Mutiso","George Nganga","Henry Kariuki","Ian Njuguna","Joel Wanjiku"],
    ["Aaron Barasa","Benson Odongo","Clinton Rotich","David Sang","Emmanuel Kiptoo","Francis Kigen","Gerald Muriuki","Harrison Gitau","Isaac Macharia","James Kimani"],
    ["Adrian Wafula","Bernard Wesonga","Clement Musyoka","Duncan Mwangi","Eric Mulwa","Fredrick Onyango","Gilbert Waweru","Herbert Maina","Ivan Kibet","John Kamande"],
    ["Alfred Ogolla","Bob Makori","Chris Ndung'u","Derek Ayieko","Elias Omolo","Franklin Cheruiyot","Graham Muthoka","Hudson Omondi","Irving Wangari","Julius Otieno"],
    ["Andrew Mugo","Benedict Oloo","Cornelius Langat","Dixon Mwamba","Elijah Nderi","Ferdinand Mutua","Gideon Kirui","Humphrey Njeru","Ike Otiende","Jonathan Kiplagat"],
    ["Alex Njoroge","Boniface Onyango","Collins Mukundi","Damian Owiti","Elvis Kamau","Frank Wanyama","Gordon Mwiti","Hilary Opiyo","Ibrahim Mwangi","Joseph Kimetto"],
    ["Albert Odour","Ben Muriithi","Craig Omondi","Dan Wachira","Edward Kipchoge","Fred Ndegwa","Greg Mutua","Hans Omwega","Innocent Koskei","Jake Wekesa"],
    ["Alvin Ouma","Boris Munyao","Curtis Kirwa","Dave Mwenda","Enoch Chelimo","Fraser Ndungu","Godwin Orimba","Hector Murigi","Irvin Keter","Jason Muthee"],
    ["Amos Mwaniki","Bruno Ochieng","Conrad Njogu","Derick Koech","Eugene Nyambura","Fabian Rotich","Godfrey Ochieng","Hugo Ndwiga","Ismail Kipkemoi","Jay Gachoki"],
    ["Anthony Odera","Byron Mutuku","Caleb Njau","Dixon Otieno","Evan Kimani","Festus Waweru","Grant Muturi","Harold Oduya","Isaiah Chesire","Jefferson Kuria"],
]


def generate_round_robin(team_ids):
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
    home = random.choices([0,1,2,3,4], weights=[20,35,25,15,5])[0]
    away = random.choices([0,1,2,3,4], weights=[25,35,22,13,5])[0]
    return home, away


def do_clear(cur, league_id):
    cur.execute("DELETE FROM player_match_stats WHERE match_id IN (SELECT match_id FROM matches WHERE league_id = %s)", (league_id,))
    cur.execute("DELETE FROM scores WHERE match_id IN (SELECT match_id FROM matches WHERE league_id = %s)", (league_id,))
    cur.execute("DELETE FROM matches WHERE league_id = %s", (league_id,))
    cur.execute("DELETE FROM players WHERE team_id IN (SELECT team_id FROM teams WHERE league_id = %s)", (league_id,))
    cur.execute("DELETE FROM teams WHERE league_id = %s", (league_id,))


def do_seed(cur, league_id, season_id):
    # Stadium
    cur.execute("SELECT stadium_id FROM stadiums WHERE name = 'Campus pitch' LIMIT 1")
    row = cur.fetchone()
    if row:
        stadium_id = row[0]
    else:
        cur.execute("INSERT INTO stadiums (name, location) VALUES ('Campus pitch', 'Strathmore University') RETURNING stadium_id")
        stadium_id = cur.fetchone()[0]

    # Teams & players
    team_ids = []
    team_player_ids = {}
    for i, (name, manager) in enumerate(zip(TEAM_NAMES, MANAGER_NAMES)):
        cur.execute(
            "INSERT INTO teams (name, manager_name, stadium_id, league_id) VALUES (%s,%s,%s,%s) RETURNING team_id",
            (name, manager, stadium_id, league_id),
        )
        team_id = cur.fetchone()[0]
        team_ids.append(team_id)
        ids = []
        for pname in PLAYERS_PER_TEAM[i]:
            cur.execute("INSERT INTO players (team_id, name) VALUES (%s,%s) RETURNING player_id", (team_id, pname))
            ids.append(cur.fetchone()[0])
        team_player_ids[team_id] = ids

    # Fixtures
    rounds = generate_round_robin(team_ids)
    match_ids_by_round = {}
    start = date(date.today().year, 1, 15)
    for matchday, pairings in enumerate(rounds, start=1):
        match_ids_by_round[matchday] = []
        mdate = start + timedelta(weeks=matchday - 1)
        for home_id, away_id in pairings:
            cur.execute(
                "INSERT INTO matches (season_id, league_id, matchday, home_team_id, away_team_id, utc_date, status) "
                "VALUES (%s,%s,%s,%s,%s,%s,'Scheduled') RETURNING match_id",
                (season_id, league_id, matchday, home_id, away_id, mdate),
            )
            match_ids_by_round[matchday].append((cur.fetchone()[0], home_id, away_id))

    # Scores + stats for first 6 matchdays
    for matchday in range(1, 7):
        for match_id, home_id, away_id in match_ids_by_round[matchday]:
            ft_home, ft_away = random_score()
            ht_home = random.randint(0, ft_home)
            ht_away = random.randint(0, ft_away)
            cur.execute(
                "INSERT INTO scores (match_id, full_time_home, full_time_away, half_time_home, half_time_away) VALUES (%s,%s,%s,%s,%s)",
                (match_id, ft_home, ft_away, ht_home, ht_away),
            )
            cur.execute("UPDATE matches SET status='Completed' WHERE match_id=%s", (match_id,))

            home_players = team_player_ids[home_id]
            away_players = team_player_ids[away_id]
            all_players = home_players + away_players

            for _ in range(ft_home):
                scorer = random.choice(home_players)
                cur.execute("INSERT INTO player_match_stats (player_id,match_id,goals,assists,yellow_cards,red_cards) VALUES (%s,%s,1,0,0,0) ON CONFLICT DO NOTHING", (scorer, match_id))
                if random.random() < 0.7:
                    assister = random.choice([p for p in home_players if p != scorer] or home_players)
                    cur.execute("INSERT INTO player_match_stats (player_id,match_id,goals,assists,yellow_cards,red_cards) VALUES (%s,%s,0,1,0,0) ON CONFLICT DO NOTHING", (assister, match_id))

            for _ in range(ft_away):
                scorer = random.choice(away_players)
                cur.execute("INSERT INTO player_match_stats (player_id,match_id,goals,assists,yellow_cards,red_cards) VALUES (%s,%s,1,0,0,0) ON CONFLICT DO NOTHING", (scorer, match_id))
                if random.random() < 0.7:
                    assister = random.choice([p for p in away_players if p != scorer] or away_players)
                    cur.execute("INSERT INTO player_match_stats (player_id,match_id,goals,assists,yellow_cards,red_cards) VALUES (%s,%s,0,1,0,0) ON CONFLICT DO NOTHING", (assister, match_id))

            for player in random.sample(all_players, k=random.randint(1, 3)):
                cur.execute("INSERT INTO player_match_stats (player_id,match_id,goals,assists,yellow_cards,red_cards) VALUES (%s,%s,0,0,1,0) ON CONFLICT DO NOTHING", (player, match_id))

            if random.random() < 0.15:
                cur.execute("INSERT INTO player_match_stats (player_id,match_id,goals,assists,yellow_cards,red_cards) VALUES (%s,%s,0,0,0,1) ON CONFLICT DO NOTHING", (random.choice(all_players), match_id))


@demo_bp.route('/admin/demo/seed', methods=['POST'])
@admin_required
def demo_seed():
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("SELECT league_id FROM leagues ORDER BY league_id LIMIT 1")
        league_row = cur.fetchone()
        if not league_row:
            flash('No league found. Check your database setup.', 'error')
            return redirect(url_for('admin'))
        league_id = league_row[0]

        cur.execute("SELECT season_id FROM seasons WHERE league_id = %s ORDER BY season_id DESC LIMIT 1", (league_id,))
        season_row = cur.fetchone()
        if not season_row:
            flash('No season found. Check your database setup.', 'error')
            return redirect(url_for('admin'))
        season_id = season_row[0]

        do_clear(cur, league_id)
        do_seed(cur, league_id, season_id)
        db.commit()
        flash('Demo data loaded successfully — 10 teams, 100 players, 45 fixtures, 30 results.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error loading demo data: {str(e)}', 'error')
    finally:
        cur.close()
    return redirect(url_for('admin'))


@demo_bp.route('/admin/demo/clear', methods=['POST'])
@admin_required
def demo_clear():
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute("SELECT league_id FROM leagues ORDER BY league_id LIMIT 1")
        league_row = cur.fetchone()
        if not league_row:
            flash('No league found.', 'error')
            return redirect(url_for('admin'))
        league_id = league_row[0]

        do_clear(cur, league_id)
        db.commit()
        flash('Demo data cleared successfully.', 'success')
    except Exception as e:
        db.rollback()
        flash(f'Error clearing demo data: {str(e)}', 'error')
    finally:
        cur.close()
    return redirect(url_for('admin'))