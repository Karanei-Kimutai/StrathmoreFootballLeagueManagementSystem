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

def get_existing_data(table_name):
    db = get_db()
    cur = db.cursor()
    cur.execute(f'SELECT * FROM {table_name}')
    data = cur.fetchall()
    cur.close()
    return data

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
            ('University Football League', 'Kenya', 0, 0, 999),
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

@admin_bp.route('/manage_stadiums', methods=['GET', 'POST'])
@admin_required
def manage_stadiums():
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        try:
            stadium_id = request.form.get('stadium_id')
            name = request.form['name']
            location = request.form['location']
            capacity = request.form['capacity']

            if 'add' in request.form:
                cur.execute('INSERT INTO stadiums (name, location, capacity) VALUES (%s, %s, %s)', 
                            (name, location, capacity))
                flash('Stadium added successfully', 'success')
            elif 'edit' in request.form and stadium_id:
                cur.execute('UPDATE stadiums SET name = %s, location = %s, capacity = %s WHERE stadium_id = %s', 
                            (name, location, capacity, stadium_id))
                flash('Stadium updated successfully', 'success')
            elif 'delete' in request.form and stadium_id:
                cur.execute('DELETE FROM stadiums WHERE stadium_id = %s', (stadium_id,))
                flash('Stadium deleted successfully', 'success')
            db.commit()
        except Exception as e:
            db.rollback()
            flash('An error occurred: ' + str(e), 'error')
        finally:
            cur.close()
        return redirect(url_for('admin.manage_stadiums'))

    cur.execute('SELECT stadium_id, name, location, capacity FROM stadiums')
    stadiums = cur.fetchall()
    cur.close()
    return render_template('manage_stadiums.html', stadiums=stadiums)

@admin_bp.route('/manage_leagues', methods=['GET', 'POST'])
@admin_required
def manage_leagues():
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        try:
            league_id = request.form.get('league_id')
            name = request.form['name']
            country = request.form['country']

            if 'add' in request.form:
                cur.execute('INSERT INTO leagues (name, country) VALUES (%s, %s)', 
                            (name, country))
                flash('League added successfully', 'success')
            elif 'edit' in request.form and league_id:
                cur.execute('UPDATE leagues SET name = %s, country = %s WHERE league_id = %s', 
                            (name, country, league_id))
                flash('League updated successfully', 'success')
            elif 'delete' in request.form and league_id:
                cur.execute('DELETE FROM leagues WHERE league_id = %s', (league_id,))
                flash('League deleted successfully', 'success')
            db.commit()
        except Exception as e:
            db.rollback()
            flash('An error occurred: ' + str(e), 'error')
        finally:
            cur.close()
        return redirect(url_for('admin.manage_leagues'))

    cur.execute('SELECT league_id, name, country FROM leagues')
    leagues = cur.fetchall()
    cur.close()
    return render_template('manage_leagues.html', leagues=leagues)

@admin_bp.route('/manage_seasons', methods=['GET', 'POST'])
@admin_required
def manage_seasons():
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        try:
            season_id = request.form.get('season_id')
            league_id = request.form['league_id']
            year = request.form['year']

            if 'add' in request.form:
                cur.execute('INSERT INTO seasons (league_id, year) VALUES (%s, %s)', (league_id, year))
                flash('Season added successfully', 'success')
            elif 'edit' in request.form and season_id:
                cur.execute('UPDATE seasons SET league_id = %s, year = %s WHERE season_id = %s', (league_id, year, season_id))
                flash('Season updated successfully', 'success')
            elif 'delete' in request.form:
                season_id = request.form['deleteItemId']
                cur.execute('DELETE FROM seasons WHERE season_id = %s', (season_id,))
                flash('Season deleted successfully', 'success')
            db.commit()
        except Exception as e:
            db.rollback()
            flash('An error occurred: ' + str(e), 'error')
        finally:
            cur.close()
        return redirect(url_for('admin.manage_seasons'))

    cur.execute('''
        SELECT s.season_id, s.league_id, s.year, l.name
        FROM seasons s
        JOIN leagues l ON s.league_id = l.league_id
    ''')
    seasons = cur.fetchall()
    cur.execute('SELECT league_id, name FROM leagues')
    leagues = cur.fetchall()
    cur.close()
    return render_template('manage_seasons.html', seasons=seasons, leagues=leagues)

@admin_bp.route('/manage_teams', methods=['GET', 'POST'])
@admin_required
def manage_teams():
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        try:
            team_id = request.form.get('team_id')
            name = request.form['name']
            founded_year = request.form['founded_year']
            stadium_id = request.form.get('stadium_id') or None
            league_id = request.form.get('league_id') or get_or_create_university_league(cur)[0]
            coach_id = request.form.get('coach_id') or None

            if 'add' in request.form:
                cur.execute('INSERT INTO teams (name, founded_year, stadium_id, league_id, coach_id) VALUES (%s, %s, %s, %s, %s)', 
                            (name, founded_year, stadium_id, league_id, coach_id))
                flash('Team added successfully', 'success')
            elif 'edit' in request.form and team_id:
                cur.execute('UPDATE teams SET name = %s, founded_year = %s, stadium_id = %s, league_id = %s, coach_id = %s WHERE team_id = %s', 
                            (name, founded_year, stadium_id, league_id, coach_id, team_id))
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
        SELECT t.team_id, t.name, t.founded_year, COALESCE(s.name, 'Not set') AS stadium,
               l.name AS league, COALESCE(c.name, 'Not set') AS coach,
               t.stadium_id, t.league_id, t.coach_id
        FROM teams t
        LEFT JOIN stadiums s ON t.stadium_id = s.stadium_id
        LEFT JOIN leagues l ON t.league_id = l.league_id
        LEFT JOIN coaches c ON t.coach_id = c.coach_id
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


@admin_bp.route('/manage_coaches', methods=['GET', 'POST'])
@admin_required
def manage_coaches():
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        try:
            coach_id = request.form.get('coach_id')
            name = request.form['name']
            nationality = request.form['nationality']
            team_id = request.form['team_id']

            if 'add' in request.form:
                cur.execute('INSERT INTO coaches (name, nationality, team_id) VALUES (%s, %s, %s)', 
                            (name, nationality, team_id))
                flash('Coach added successfully', 'success')
            elif 'submit' in request.form and coach_id:
                cur.execute('UPDATE coaches SET name = %s, nationality = %s, team_id = %s WHERE coach_id = %s', 
                            (name, nationality, team_id, coach_id))
                flash('Coach updated successfully', 'success')
            elif 'delete' in request.form:
                coach_id = request.form['deleteEntityId']
                cur.execute('DELETE FROM coaches WHERE coach_id = %s', (coach_id,))
                flash('Coach deleted successfully', 'success')
            db.commit()
        except Exception as e:
            db.rollback()
            flash('An error occurred: ' + str(e), 'error')
        finally:
            cur.close()
        return redirect(url_for('admin.manage_coaches'))

    cur.execute('''
        SELECT c.coach_id, c.name, c.team_id, c.nationality, t.name AS team_name
        FROM coaches c
        JOIN teams t ON c.team_id = t.team_id
    ''')
    coaches = cur.fetchall()
    cur.execute('SELECT team_id, name FROM teams')
    teams = cur.fetchall()
    cur.close()
    return render_template('manage_coaches.html', coaches=coaches, teams=teams)



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
            position = request.form['position']
            date_of_birth = request.form['date_of_birth']
            nationality = request.form['nationality']

            if 'submit' in request.form:
                if player_id:
                    cur.execute('UPDATE players SET team_id = %s, name = %s, position = %s, date_of_birth = %s, nationality = %s WHERE player_id = %s', 
                                (team_id, name, position, date_of_birth, nationality, player_id))
                    flash('Player updated successfully', 'success')
                else:
                    cur.execute('INSERT INTO players (team_id, name, position, date_of_birth, nationality) VALUES (%s, %s, %s, %s, %s)', 
                                (team_id, name, position, date_of_birth, nationality))
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
        SELECT p.player_id, t.name AS team, p.name, p.position, p.date_of_birth, p.nationality, p.team_id
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



@admin_bp.route('/manage_countries', methods=['GET', 'POST'])
@admin_required
def manage_countries():
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        try:
            country_id = request.form.get('country_id')
            name = request.form['name']
            flag_url = request.form['flag_url']

            if 'submit' in request.form:
                if country_id:
                    cur.execute('UPDATE countries SET name = %s, flag_url = %s WHERE country_id = %s', 
                                (name, flag_url, country_id))
                    flash('Country updated successfully', 'success')
                else:
                    cur.execute('INSERT INTO countries (name, flag_url) VALUES (%s, %s)', 
                                (name, flag_url))
                    flash('Country added successfully', 'success')
            elif 'delete' in request.form:
                country_id = request.form['deleteEntityId']
                cur.execute('DELETE FROM countries WHERE country_id = %s', (country_id,))
                flash('Country deleted successfully', 'success')
            db.commit()
        except Exception as e:
            db.rollback()
            flash('An error occurred: ' + str(e), 'error')
        finally:
            cur.close()
        return redirect(url_for('admin.manage_countries'))

    cur.execute('SELECT country_id, name, flag_url FROM countries')
    countries = cur.fetchall()
    cur.close()
    return render_template('manage_countries.html', countries=countries)



@admin_bp.route('/manage_referees', methods=['GET', 'POST'])
@admin_required
def manage_referees():
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        try:
            referee_id = request.form.get('referee_id')
            name = request.form['name']
            nationality = request.form['nationality']

            if 'submit' in request.form:
                if referee_id:
                    cur.execute('UPDATE referees SET name = %s, nationality = %s WHERE referee_id = %s', 
                                (name, nationality, referee_id))
                    flash('Referee updated successfully', 'success')
                else:
                    cur.execute('INSERT INTO referees (name, nationality) VALUES (%s, %s)', 
                                (name, nationality))
                    flash('Referee added successfully', 'success')
            elif 'delete' in request.form:
                referee_id = request.form['deleteEntityId']
                cur.execute('DELETE FROM referees WHERE referee_id = %s', (referee_id,))
                flash('Referee deleted successfully', 'success')
            db.commit()
        except Exception as e:
            db.rollback()
            flash('An error occurred: ' + str(e), 'error')
        finally:
            cur.close()
        return redirect(url_for('admin.manage_referees'))

    cur.execute('SELECT referee_id, name, nationality FROM referees')
    referees = cur.fetchall()
    cur.close()
    return render_template('manage_referees.html', referees=referees)



@admin_bp.route('/manage_scorers', methods=['GET', 'POST'])
@admin_required
def manage_scorers():
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        try:
            scorer_id = request.form.get('scorer_id')
            player_id = request.form['player_id']
            season_id = request.form['season_id']
            league_id = request.form['league_id']
            goals = request.form['goals']
            assists = request.form['assists']
            penalties = request.form['penalties']

            if 'submit' in request.form:
                if scorer_id:
                    cur.execute('UPDATE scorers SET player_id = %s, season_id = %s, league_id = %s, goals = %s, assists = %s, penalties = %s WHERE scorer_id = %s',
                                (player_id, season_id, league_id, goals, assists, penalties, scorer_id))
                    flash('Scorer updated successfully', 'success')
                else:
                    cur.execute('INSERT INTO scorers (player_id, season_id, league_id, goals, assists, penalties) VALUES (%s, %s, %s, %s, %s, %s)',
                                (player_id, season_id, league_id, goals, assists, penalties))
                    flash('Scorer added successfully', 'success')
            elif 'delete' in request.form:
                scorer_id = request.form['deleteEntityId']
                cur.execute('DELETE FROM scorers WHERE scorer_id = %s', (scorer_id,))
                flash('Scorer deleted successfully', 'success')
            db.commit()
        except Exception as e:
            db.rollback()
            flash('An error occurred: ' + str(e), 'error')
        finally:
            cur.close()
        return redirect(url_for('admin.manage_scorers'))

    cur.execute('''
        SELECT s.scorer_id, p.name, se.year, l.name, s.goals, s.assists, s.penalties 
        FROM scorers s 
        JOIN players p ON s.player_id = p.player_id 
        JOIN seasons se ON s.season_id = se.season_id 
        JOIN leagues l ON s.league_id = l.league_id
    ''')
    scorers = cur.fetchall()
    cur.execute('SELECT player_id, name FROM players')
    players = cur.fetchall()
    cur.execute('SELECT season_id, year FROM seasons')
    seasons = cur.fetchall()
    cur.execute('SELECT league_id, name FROM leagues')
    leagues = cur.fetchall()
    cur.close()
    return render_template('manage_scorers.html', scorers=scorers, players=players, seasons=seasons, leagues=leagues)



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



@admin_bp.route('/manage_standings', methods=['GET', 'POST'])
@admin_required
def manage_standings():
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        try:
            standing_id = request.form.get('standing_id')
            position = request.form['position']
            team_id = request.form['team_id']
            played_games = request.form['played_games']
            won = request.form['won']
            draw = request.form['draw']
            lost = request.form['lost']
            points = request.form['points']
            goals_for = request.form['goals_for']
            goals_against = request.form['goals_against']
            goal_difference = request.form['goal_difference']
            form = request.form['form']

            if 'add' in request.form:
                cur.execute('''
                    INSERT INTO standings (position, team_id, played_games, won, draw, lost, points, goals_for, goals_against, goal_difference, form)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (position, team_id, played_games, won, draw, lost, points, goals_for, goals_against, goal_difference, form))
                flash('Standing added successfully', 'success')
            elif 'edit' in request.form and standing_id:
                cur.execute('''
                    UPDATE standings
                    SET position = %s, team_id = %s, played_games = %s, won = %s, draw = %s, lost = %s, points = %s, goals_for = %s, goals_against = %s, goal_difference = %s, form = %s
                    WHERE standing_id = %s
                ''', (position, team_id, played_games, won, draw, lost, points, goals_for, goals_against, goal_difference, form, standing_id))
                flash('Standing updated successfully', 'success')
            elif 'delete' in request.form:
                standing_id = request.form['deleteItemId']
                cur.execute('DELETE FROM standings WHERE standing_id = %s', (standing_id,))
                flash('Standing deleted successfully', 'success')
            db.commit()
        except Exception as e:
            db.rollback()
            flash('An error occurred: ' + str(e), 'error')
        finally:
            cur.close()
        return redirect(url_for('admin.manage_standings'))

    cur.execute('''
        SELECT s.standing_id, s.position, t.name, s.played_games, s.won, s.draw, s.lost, s.points, s.goals_for, s.goals_against, s.goal_difference, s.form, s.team_id
        FROM standings s
        JOIN teams t ON s.team_id = t.team_id
    ''')
    standings = cur.fetchall()
    cur.execute('SELECT team_id, name FROM teams')
    teams = cur.fetchall()
    cur.close()
    return render_template('manage_standings.html', standings=standings, teams=teams)

@admin_bp.route('/manage_users', methods=['GET', 'POST'])
@admin_required
def manage_users():
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        try:
            user_id = request.form.get('user_id')
            is_admin = request.form.get('is_admin') == 'true'

            cur.execute('UPDATE users SET is_admin = %s WHERE user_id = %s', (is_admin, user_id))
            db.commit()
            flash('User privilege updated successfully', 'success')
        except Exception as e:
            db.rollback()
            flash('An error occurred: ' + str(e), 'error')
        finally:
            cur.close()
        return redirect(url_for('admin.manage_users'))

    cur.execute('SELECT user_id, username, is_admin FROM users')
    users = cur.fetchall()
    cur.close()

    return render_template('manage_users.html', users=users)
