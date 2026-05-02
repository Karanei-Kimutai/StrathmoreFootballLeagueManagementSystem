from datetime import date
from flask import Blueprint, render_template, request, redirect, session, url_for, flash
from functools import wraps
from db import get_db
from utils import generate_single_round_robin

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin'):
            flash('You need to be an admin to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return wrap

def ensure_match_extensions(cur):
    cur.execute("""
        ALTER TABLE matches
        ADD COLUMN IF NOT EXISTS status character varying(50) DEFAULT 'Pending'
    """)

def get_or_create_university_league(cur):
    cur.execute('SELECT league_id FROM leagues ORDER BY league_id LIMIT 1')
    league = cur.fetchone()
    if league:
        league_id = league[0]
    else:
        cur.execute(
            """
            INSERT INTO leagues (name, country, cl_spot, uel_spot, relegation_spot)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING league_id
            """,
            ('Strathmore Football League', 'Kenya', 0, 0, 999),
        )
        league_id = cur.fetchone()[0]

    cur.execute(
        'SELECT season_id FROM seasons WHERE league_id = %s ORDER BY season_id DESC LIMIT 1',
        (league_id,),
    )
    season = cur.fetchone()
    if season:
        season_id = season[0]
    else:
        current_year = str(date.today().year)
        cur.execute(
            'INSERT INTO seasons (league_id, year) VALUES (%s, %s) RETURNING season_id',
            (league_id, current_year),
        )
        season_id = cur.fetchone()[0]

    return league_id, season_id

@admin_bp.route('/manage_teams', methods=['GET', 'POST'])
@admin_required
def manage_teams():
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        try:
            team_id = request.form.get('team_id')
            name = request.form['name']
            stadium_id = request.form.get('stadium_id') or None
            league_id = request.form.get('league_id') or get_or_create_university_league(cur)[0]
            manager_name = request.form.get('manager_name', '').strip()

            if 'add' in request.form:
                cur.execute('INSERT INTO teams (name, manager_name, stadium_id, league_id) VALUES (%s, %s, %s, %s)', 
                            (name, manager_name, stadium_id, league_id))
                flash('Team added successfully', 'success')
            elif 'edit' in request.form and team_id:
                cur.execute('UPDATE teams SET name = %s, manager_name = %s, stadium_id = %s, league_id = %s WHERE team_id = %s', 
                            (name, manager_name, stadium_id, league_id, team_id))
                flash('Team updated successfully', 'success')
            elif 'delete' in request.form and team_id:
                cur.execute('DELETE FROM teams WHERE team_id = %s', (team_id,))
                flash('Team deleted successfully', 'success')
            db.commit()
        except Exception as e:
            db.rollback()
            flash('An error occurred: ' + str(e), 'error')
        finally:
            cur.close()
        return redirect(url_for('admin.manage_teams'))

    league_id, _ = get_or_create_university_league(cur)
    db.commit()
    cur.execute('''
        SELECT t.team_id, t.name, COALESCE(s.name, 'Not set') AS stadium,
               l.name AS league, t.manager_name,
               t.stadium_id, t.league_id
        FROM teams t
        LEFT JOIN stadiums s ON t.stadium_id = s.stadium_id
        LEFT JOIN leagues l ON t.league_id = l.league_id
        WHERE t.league_id = %s
        ORDER BY t.name
    ''', (league_id,))
    teams = cur.fetchall()
    cur.execute('SELECT stadium_id, name FROM stadiums')
    stadiums = cur.fetchall()
    cur.execute('SELECT league_id, name FROM leagues WHERE league_id = %s', (league_id,))
    leagues = cur.fetchall()
    cur.execute('SELECT coach_id, name FROM coaches')
    coaches = cur.fetchall()
    cur.close()
    return render_template('manage_teams.html', teams=teams, stadiums=stadiums, leagues=leagues, coaches=coaches)

@admin_bp.route('/manage_players', methods=['GET', 'POST'])
@admin_required
def manage_players():
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        try:
            player_id = request.form.get('player_id')
            team_id = request.form['team_id']
            name = request.form['name']

            if 'submit' in request.form:
                if player_id:
                    cur.execute('UPDATE players SET team_id = %s, name = %s WHERE player_id = %s', 
                                (team_id, name, player_id))
                    flash('Player updated successfully', 'success')
                else:
                    cur.execute('INSERT INTO players (team_id, name) VALUES (%s, %s)', 
                                (team_id, name))
                    flash('Player added successfully', 'success')
            elif 'delete' in request.form:
                player_id = request.form['deleteEntityId']
                cur.execute('DELETE FROM players WHERE player_id = %s', (player_id,))
                flash('Player deleted successfully', 'success')
            db.commit()
        except Exception as e:
            db.rollback()
            flash('An error occurred: ' + str(e), 'error')
        finally:
            cur.close()
        return redirect(url_for('admin.manage_players'))

    league_id, _ = get_or_create_university_league(cur)
    db.commit()
    cur.execute('''
        SELECT p.player_id, t.name AS team, p.name, p.team_id
        FROM players p
        JOIN teams t ON p.team_id = t.team_id
        WHERE t.league_id = %s
    ''', (league_id,))
    players = cur.fetchall()
    cur.execute('SELECT team_id, name FROM teams WHERE league_id = %s ORDER BY name', (league_id,))
    teams = cur.fetchall()
    cur.close()
    return render_template('manage_players.html', players=players, teams=teams)




@admin_bp.route('/manage_matches', methods=['GET', 'POST'])
@admin_required
def manage_matches():
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        try:
            match_id = request.form.get('match_id')
            date = request.form['date']
            team1_id = request.form['team1_id']
            team2_id = request.form['team2_id']
            default_league_id, default_season_id = get_or_create_university_league(cur)
            season_id = request.form.get('season_id') or default_season_id
            league_id = request.form.get('league_id') or default_league_id

            if 'submit' in request.form:
                if match_id:
                    cur.execute('UPDATE matches SET utc_date = %s, home_team_id = %s, away_team_id = %s, season_id = %s, league_id = %s WHERE match_id = %s', 
                                (date, team1_id, team2_id, season_id, league_id, match_id))
                    flash('Match updated successfully', 'success')
                else:
                    cur.execute('INSERT INTO matches (utc_date, home_team_id, away_team_id, season_id, league_id) VALUES (%s, %s, %s, %s, %s)', 
                                (date, team1_id, team2_id, season_id, league_id))
                    flash('Match added successfully', 'success')
            elif 'delete' in request.form:
                match_id = request.form['deleteEntityId']
                cur.execute('DELETE FROM matches WHERE match_id = %s', (match_id,))
                flash('Match deleted successfully', 'success')
            db.commit()
        except Exception as e:
            db.rollback()
            flash('An error occurred: ' + str(e), 'error')
        finally:
            cur.close()
        return redirect(url_for('admin.manage_matches'))

    league_id, season_id = get_or_create_university_league(cur)
    db.commit()
    cur.execute('''
        SELECT m.match_id, m.utc_date, t1.name AS team1, t2.name AS team2, s.year AS season, l.name AS league,
               m.home_team_id, m.away_team_id, m.season_id, m.league_id
        FROM matches m
        JOIN teams t1 ON m.home_team_id = t1.team_id
        JOIN teams t2 ON m.away_team_id = t2.team_id
        JOIN seasons s ON m.season_id = s.season_id
        JOIN leagues l ON m.league_id = l.league_id
        WHERE m.league_id = %s
    ''', (league_id,))
    matches = cur.fetchall()
    cur.execute('SELECT team_id, name FROM teams WHERE league_id = %s ORDER BY name', (league_id,))
    teams = cur.fetchall()
    cur.execute('SELECT season_id, year FROM seasons WHERE league_id = %s', (league_id,))
    seasons = cur.fetchall()
    cur.execute('SELECT league_id, name FROM leagues WHERE league_id = %s', (league_id,))
    leagues = cur.fetchall()
    cur.close()
    return render_template('manage_matches.html', matches=matches, teams=teams, seasons=seasons, leagues=leagues)


@admin_bp.route('/generate_fixtures/<int:league_id>', methods=['POST'])
@admin_required
def generate_fixtures(league_id):
    db = get_db()
    cur = db.cursor()
    try:
        ensure_match_extensions(cur)
        cur.execute('SELECT team_id FROM teams WHERE league_id = %s ORDER BY team_id', (league_id,))
        team_ids = [row[0] for row in cur.fetchall()]
        if len(team_ids) < 2:
            flash('At least two teams are required to generate fixtures', 'error')
            return redirect(url_for('user.profile_league', league_id=league_id))

        cur.execute('SELECT COUNT(*) FROM matches WHERE league_id = %s', (league_id,))
        if cur.fetchone()[0] > 0:
            flash('Fixtures already exist for this league', 'error')
            return redirect(url_for('user.profile_league', league_id=league_id))

        cur.execute(
            'SELECT season_id FROM seasons WHERE league_id = %s ORDER BY season_id DESC LIMIT 1',
            (league_id,),
        )
        season = cur.fetchone()
        if not season:
            flash('Create a season for this league before generating fixtures', 'error')
            return redirect(url_for('user.profile_league', league_id=league_id))

        created = 0
        for matchday, pairings in enumerate(generate_single_round_robin(team_ids), start=1):
            for home_team_id, away_team_id in pairings:
                cur.execute(
                    """
                    INSERT INTO matches (season_id, league_id, matchday, home_team_id, away_team_id, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (season[0], league_id, matchday, home_team_id, away_team_id, 'Scheduled'),
                )
                created += 1

        db.commit()
        flash(f'Generated {created} fixtures', 'success')
    except Exception as e:
        db.rollback()
        flash('An error occurred: ' + str(e), 'error')
    finally:
        cur.close()

    return redirect(url_for('user.profile_league', league_id=league_id))


@admin_bp.route('/generate_fixtures', methods=['POST'])
@admin_required
def generate_default_fixtures():
    db = get_db()
    cur = db.cursor()
    try:
        league_id, _ = get_or_create_university_league(cur)
        db.commit()
    except Exception as e:
        db.rollback()
        flash('An error occurred: ' + str(e), 'error')
        return redirect(url_for('admin'))
    finally:
        cur.close()

    return redirect(url_for('admin.generate_fixtures', league_id=league_id), code=307)

@admin_bp.route('/manage_scores', methods=['GET', 'POST'])
@admin_required
def manage_scores():
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        try:
            ensure_match_extensions(cur)
            score_id = request.form.get('score_id')
            match_id = request.form['match_id']
            full_time_home = request.form['full_time_home']
            full_time_away = request.form['full_time_away']
            half_time_home = request.form['half_time_home']
            half_time_away = request.form['half_time_away']

            if 'submit' in request.form:
                previous_match_id = None
                if score_id:
                    cur.execute('SELECT match_id FROM scores WHERE score_id = %s', (score_id,))
                    previous_score = cur.fetchone()
                    previous_match_id = previous_score[0] if previous_score else None
                    cur.execute('UPDATE scores SET match_id = %s, full_time_home = %s, full_time_away = %s, half_time_home = %s, half_time_away = %s WHERE score_id = %s',
                                (match_id, full_time_home, full_time_away, half_time_home, half_time_away, score_id))
                    cur.execute('UPDATE matches SET status = %s WHERE match_id = %s', ('Completed', match_id))
                    flash('Score updated successfully', 'success')
                else:
                    cur.execute('INSERT INTO scores (match_id, full_time_home, full_time_away, half_time_home, half_time_away) VALUES (%s, %s, %s, %s, %s)',
                                (match_id, full_time_home, full_time_away, half_time_home, half_time_away))
                    cur.execute('UPDATE matches SET status = %s WHERE match_id = %s', ('Completed', match_id))
                    flash('Score added successfully', 'success')
                if previous_match_id and str(previous_match_id) != str(match_id):
                    cur.execute('DELETE FROM player_match_stats WHERE match_id = %s', (previous_match_id,))
                    cur.execute('UPDATE matches SET status = %s WHERE match_id = %s', ('Scheduled', previous_match_id))
                cur.execute('DELETE FROM player_match_stats WHERE match_id = %s', (match_id,))
                player_ids = request.form.getlist('stat_player_id[]')
                goals = request.form.getlist('stat_goals[]')
                assists = request.form.getlist('stat_assists[]')
                yellow_cards = request.form.getlist('stat_yellow_cards[]')
                red_cards = request.form.getlist('stat_red_cards[]')
                for index, player_id in enumerate(player_ids):
                    if not player_id:
                        continue
                    row = (
                        player_id,
                        match_id,
                        int(goals[index] or 0),
                        int(assists[index] or 0),
                        int(yellow_cards[index] or 0),
                        int(red_cards[index] or 0),
                    )
                    if any(value > 0 for value in row[2:]):
                        cur.execute(
                            """
                            INSERT INTO player_match_stats
                                (player_id, match_id, goals, assists, yellow_cards, red_cards)
                            VALUES (%s, %s, %s, %s, %s, %s)
                            """,
                            row,
                        )
            elif 'delete' in request.form:
                score_id = request.form['deleteEntityId']
                cur.execute('SELECT match_id FROM scores WHERE score_id = %s', (score_id,))
                score = cur.fetchone()
                if score:
                    cur.execute('DELETE FROM player_match_stats WHERE match_id = %s', (score[0],))
                    cur.execute('UPDATE matches SET status = %s WHERE match_id = %s', ('Scheduled', score[0]))
                cur.execute('DELETE FROM scores WHERE score_id = %s', (score_id,))
                flash('Score deleted successfully', 'success')
            db.commit()
        except Exception as e:
            db.rollback()
            flash('An error occurred: ' + str(e), 'error')
        finally:
            cur.close()
        return redirect(url_for('admin.manage_scores'))

    ensure_match_extensions(cur)
    league_id, _ = get_or_create_university_league(cur)
    db.commit()
    cur.execute('''
        SELECT s.score_id, s.match_id, m.utc_date, ht.name, at.name,
               s.full_time_home, s.full_time_away, s.half_time_home, s.half_time_away
        FROM scores s
        JOIN matches m ON s.match_id = m.match_id
        JOIN teams ht ON m.home_team_id = ht.team_id
        JOIN teams at ON m.away_team_id = at.team_id
        WHERE m.league_id = %s
        ORDER BY m.utc_date DESC NULLS LAST, s.score_id DESC
    ''', (league_id,))
    scores = cur.fetchall()
    cur.execute('''
        SELECT m.match_id, m.utc_date, ht.name, at.name, m.home_team_id, m.away_team_id
        FROM matches m
        JOIN teams ht ON m.home_team_id = ht.team_id
        JOIN teams at ON m.away_team_id = at.team_id
        WHERE m.league_id = %s
        ORDER BY m.utc_date DESC NULLS LAST, m.match_id DESC
    ''', (league_id,))
    matches = cur.fetchall()
    match_players = {}
    for match in matches:
        cur.execute(
            """
            SELECT player_id, name, team_id
            FROM players
            WHERE team_id IN (%s, %s)
            ORDER BY name
            """,
            (match[4], match[5]),
        )
        match_players[str(match[0])] = [
            {'id': player[0], 'name': player[1], 'team_id': player[2]}
            for player in cur.fetchall()
        ]
    cur.execute('''
        SELECT player_id, match_id, goals, assists, yellow_cards, red_cards
        FROM player_match_stats
        ORDER BY id
    ''')
    existing_stats = {}
    for stat in cur.fetchall():
        existing_stats.setdefault(str(stat[1]), []).append({
            'player_id': stat[0],
            'goals': stat[2],
            'assists': stat[3],
            'yellow_cards': stat[4],
            'red_cards': stat[5],
        })
    cur.close()
    return render_template('manage_scores.html', scores=scores, matches=matches, match_players=match_players, existing_stats=existing_stats)

