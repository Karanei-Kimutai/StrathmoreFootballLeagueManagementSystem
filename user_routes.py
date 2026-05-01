from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from functools import wraps
from db import get_db
from utils import calculate_league_standings

user_bp = Blueprint('user', __name__)

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' not in session:
            flash('You need to be logged in to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

def ensure_player_match_stats(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS player_match_stats (
            id SERIAL PRIMARY KEY,
            player_id integer NOT NULL REFERENCES players(player_id),
            match_id integer NOT NULL REFERENCES matches(match_id),
            goals integer DEFAULT 0,
            assists integer DEFAULT 0,
            yellow_cards integer DEFAULT 0,
            red_cards integer DEFAULT 0
        )
    """)

def get_primary_league_id(cur):
    cur.execute('SELECT league_id FROM leagues ORDER BY league_id LIMIT 1')
    league = cur.fetchone()
    return league[0] if league else None

@user_bp.route('/user')
def user_dashboard():
    return render_template('user_dashboard.html')

@user_bp.route('/user/teams')
def user_teams():
    db = get_db()
    cur = db.cursor()

    league_id = get_primary_league_id(cur)
    query = """
        SELECT team_id, name, crestURL 
        FROM teams
        WHERE 1=1
    """
    filters = []

    # Add filters based on the selected values
    if league_id:
        query += " AND league_id = %s"
        filters.append(league_id)

    query += " LIMIT %s OFFSET %s"
    filters.append(20)
    filters.append((request.args.get('page', 1, type=int) - 1) * 20)

    cur.execute(query, filters)
    teams = cur.fetchall()

    cur.execute('SELECT COUNT(*) FROM teams WHERE 1=1 ' + (' AND league_id = %s' if league_id else ''), filters[:-2])
    total_teams = cur.fetchone()[0]
    cur.close()

    total_pages = (total_teams + 19) // 20

    return render_template('user_teams.html', teams=teams, page=request.args.get('page', 1, type=int), total_pages=total_pages, max=max, min=min, str=str)

@user_bp.route('/user/players')
def user_players():
    db = get_db()
    cur = db.cursor()

    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    league_id = get_primary_league_id(cur)
    team_id = request.args.get('team_id')
    position = request.args.get('position')

    cur.execute('SELECT team_id, name FROM teams')
    teams = cur.fetchall()

    positions = ['Goalkeeper', 'Defence', 'Midfield', 'Offence']

    # Build the base query
    query = """
        SELECT p.player_id, p.name, p.position, t.crestURL, t.name
        FROM players p
        JOIN teams t ON p.team_id = t.team_id
        WHERE 1=1
    """
    filters = []

    # Add filters based on the selected values
    if league_id:
        query += " AND t.league_id = %s"
        filters.append(league_id)
    if team_id:
        query += " AND p.team_id = %s"
        filters.append(team_id)
    if position:
        query += " AND p.position = %s"
        filters.append(position)

    query += " LIMIT %s OFFSET %s"
    filters.append(per_page)
    filters.append(offset)

    cur.execute(query, filters)
    players = cur.fetchall()

    cur.execute('SELECT COUNT(*) FROM players p JOIN teams t ON p.team_id = t.team_id WHERE 1=1' + (' AND t.league_id = %s' if league_id else '') + (' AND p.team_id = %s' if team_id else '') + (' AND p.position = %s' if position else ''), filters[:-2])
    total_players = cur.fetchone()[0]
    cur.close()

    total_pages = (total_players + per_page - 1) // per_page

    return render_template('user_players.html', players=players, page=page, total_pages=total_pages, teams=teams, positions=positions, max=max, min=min, str=str)




@user_bp.route('/user/leagues')
def user_leagues():
    db = get_db()
    cur = db.cursor()
    league_id = get_primary_league_id(cur)
    cur.close()

    if league_id:
        return redirect(url_for('user.profile_league', league_id=league_id))

    return render_template('user_leagues.html', leagues=[])
    
@user_bp.route('/user/matches')
def user_matches():
    db = get_db()
    cur = db.cursor()

    league_id = get_primary_league_id(cur)
    team_id = request.args.get('team_id')
    matchday = request.args.get('matchday')

    cur.execute('SELECT team_id, name FROM teams')
    teams = cur.fetchall()

    matchdays = [i for i in range(1, 39)]  # Assuming matchdays from 1 to 38

    # Build the base query
    query = """
        SELECT m.match_id, 
               t1.name AS home_team_name, 
               t2.name AS away_team_name, 
               s.full_time_home AS home_score, 
               s.full_time_away AS away_score,
               TO_CHAR(m.utc_date, 'Month DD, YYYY') AS formatted_date,
               t1.crestURL AS home_team_logo,
               t2.crestURL AS away_team_logo,
               m.matchday
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.team_id
        JOIN teams t2 ON m.away_team_id = t2.team_id
        LEFT JOIN scores s ON m.match_id = s.match_id
        WHERE 1=1
    """
    filters = []

    # Add filters based on the selected values
    if league_id:
        query += " AND m.league_id = %s"
        filters.append(league_id)
    if team_id:
        query += " AND (m.home_team_id = %s OR m.away_team_id = %s)"
        filters.append(team_id)
        filters.append(team_id)
    if matchday:
        query += " AND m.matchday = %s"
        filters.append(matchday)

    query += " ORDER BY m.utc_date DESC"

    cur.execute(query, filters)
    matches = cur.fetchall()
    cur.close()

    return render_template('user_matches.html', matches=matches, teams=teams, matchdays=matchdays, str=str)



@user_bp.route('/team/<int:team_id>')
def profile_team(team_id):
    db = get_db()
    cur = db.cursor()

    # Get team details along with stadium, coach, league, and crestURL
    cur.execute("""
        SELECT t.name, t.founded_year, s.name AS stadium_name, c.name AS coach_name, l.name AS league_name, t.crestURL
        FROM teams t
        LEFT JOIN stadiums s ON t.stadium_id = s.stadium_id
        LEFT JOIN coaches c ON t.coach_id = c.coach_id
        JOIN leagues l ON t.league_id = l.league_id
        WHERE t.team_id = %s
    """, (team_id,))
    team = cur.fetchone()

    # Get players
    cur.execute("""
        SELECT p.player_id, p.name, p.date_of_birth, p.position, p.nationality
        FROM players p 
        WHERE p.team_id = %s
    """, (team_id,))
    players = cur.fetchall()

    # Get match scores
    cur.execute("""
        SELECT 
            m.match_id,
            TO_CHAR(m.utc_date, 'Mon, DD YYYY') AS utc_date, 
            t1.name AS home_team_name, 
            t2.name AS away_team_name, 
            s.full_time_home, 
            s.full_time_away,
            t1.crestURL AS home_team_logo,
            t2.crestURL AS away_team_logo,
            m.matchday
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.team_id
        JOIN teams t2 ON m.away_team_id = t2.team_id
        LEFT JOIN scores s ON m.match_id = s.match_id
        WHERE m.home_team_id = %s OR m.away_team_id = %s
        ORDER BY m.utc_date DESC
    """, (team_id, team_id))
    scores = cur.fetchall()

    cur.close()

    if team:
        return render_template('profile_team.html',
                               team=team,
                               players=players,
                               scores=scores,
                               logo_url=team[5])
    else:
        flash('Team not found', 'error')
        return redirect(url_for('user.user_dashboard'))




@user_bp.route('/player/<int:player_id>')
def profile_player(player_id):
    db = get_db()
    cur = db.cursor()

    # Fetch player details
    cur.execute("""
        SELECT p.name, p.date_of_birth, p.position, t.team_id, t.name AS team_name, p.nationality
        FROM players p 
        JOIN teams t ON p.team_id = t.team_id 
        WHERE p.player_id = %s
    """, (player_id,))
    player = cur.fetchone()

    ensure_player_match_stats(cur)
    db.commit()
    cur.execute("""
        SELECT COALESCE(SUM(goals), 0), COALESCE(SUM(assists), 0),
               COALESCE(SUM(yellow_cards), 0), COALESCE(SUM(red_cards), 0)
        FROM player_match_stats
        WHERE player_id = %s
    """, (player_id,))
    statistics = cur.fetchone()

    cur.close()

    if player:
        return render_template('profile_player.html', player=player, statistics=statistics)
    else:
        flash('Player not found', 'error')
        return redirect(url_for('user.user_dashboard'))





@user_bp.route('/match/<int:match_id>')
def profile_match(match_id):
    db = get_db()
    cur = db.cursor()

    ensure_player_match_stats(cur)
    db.commit()

    cur.execute("""
        SELECT m.match_id, 
               t1.name AS home_team_name, 
               t2.name AS away_team_name, 
               s.full_time_home AS home_score, 
               s.full_time_away AS away_score,
               TO_CHAR(m.utc_date, 'Month DD, YYYY') AS formatted_date,
               m.matchday,
               t1.crestURL AS home_team_logo,
               t2.crestURL AS away_team_logo,
               COALESCE(st.name, 'Campus pitch') AS stadium_name,
               COALESCE(st.location, 'University campus') AS stadium_location,
               t1.team_id AS home_team_id,
               t2.team_id AS away_team_id
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.team_id
        JOIN teams t2 ON m.away_team_id = t2.team_id
        LEFT JOIN scores s ON m.match_id = s.match_id
        LEFT JOIN stadiums st ON t1.stadium_id = st.stadium_id
        WHERE m.match_id = %s
    """, (match_id,))
    match = cur.fetchone()

    cur.execute("""
        SELECT s.full_time_home, s.full_time_away, s.half_time_home, s.half_time_away
        FROM scores s
        WHERE s.match_id = %s
    """, (match_id,))
    scores = cur.fetchall()

    cur.execute("""
        SELECT p.name, p.team_id, pms.goals, pms.assists, pms.yellow_cards, pms.red_cards
        FROM player_match_stats pms
        JOIN players p ON pms.player_id = p.player_id
        WHERE pms.match_id = %s
        ORDER BY pms.goals DESC, pms.assists DESC, p.name
    """, (match_id,))
    player_stats = cur.fetchall()

    cur.close()

    if match:
        return render_template('profile_match.html', match=match, scores=scores, player_stats=player_stats)
    else:
        flash('Match not found', 'error')
        return redirect(url_for('user.user_dashboard'))





@user_bp.route('/league/<int:league_id>')
def profile_league(league_id):
    db = get_db()
    cur = db.cursor()

    cur.execute("""
        SELECT l.name, l.country, NULL AS icon_url, NULL AS flag_url, l.cl_spot, l.uel_spot, l.relegation_spot
        FROM leagues l
        WHERE l.league_id = %s
    """, (league_id,))
    league = cur.fetchone()

    cur.execute('SELECT team_id, name, cresturl FROM teams WHERE league_id = %s', (league_id,))
    teams = cur.fetchall()

    cur.execute("""
        SELECT m.match_id, m.utc_date, m.home_team_id, m.away_team_id,
               s.full_time_home, s.full_time_away
        FROM matches m
        LEFT JOIN scores s ON m.match_id = s.match_id
        WHERE m.league_id = %s
        ORDER BY m.utc_date ASC NULLS LAST, m.match_id ASC
    """, (league_id,))
    matches = cur.fetchall()
    standings = calculate_league_standings(teams, matches, league)

    cur.close()

    return render_template('profile_league.html', league=league, teams=teams, standings=standings)
