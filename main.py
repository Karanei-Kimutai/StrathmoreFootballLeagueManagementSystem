from flask import Flask, render_template, request, redirect, session, url_for, flash
from db import get_db, close_db
from admin_routes import admin_bp
from user_routes import user_bp
from config import Config
import bcrypt

app = Flask(__name__) 
app.secret_key = Config.SECRET_KEY

app.register_blueprint(admin_bp)
app.register_blueprint(user_bp)

@app.teardown_appcontext
def teardown_db(exception):
    close_db()

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.route('/')
def landing():
    db = get_db()
    cur = db.cursor()
    cur.execute("""
        SELECT league_id, name, NULL AS flag_url, NULL AS icon_url
        FROM leagues
        ORDER BY league_id
        LIMIT 1
    """)
    leagues = cur.fetchall()
    cur.execute("""
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
        ORDER BY m.utc_date ASC NULLS LAST, m.match_id ASC
        LIMIT 5
    """)
    matches = cur.fetchall()
    cur.close()
    return render_template('landing.html', leagues=leagues, matches=matches)

@app.route('/home')
def home():
    if 'user_id' in session:
        if session.get('is_admin'):
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('user.user_dashboard'))
    return redirect(url_for('user.user_dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()
        username = request.form['username']
        password = request.form['password']
        cur.execute(
            'SELECT user_id, username, password, is_admin FROM users WHERE username = %s',
            (username, ))
        user = cur.fetchone()
        cur.close()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_admin'] = user[3]
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    results = []
    query = ""
    if request.method == 'POST':
        query = request.form['query']
        db = get_db()
        cur = db.cursor()

        # Search in teams
        cur.execute(
            "SELECT team_id, name, 'team' AS source FROM teams WHERE name ILIKE %s",
            ('%' + query + '%', ))
        results.extend(cur.fetchall())

        # Search in players
        cur.execute(
            "SELECT player_id, name, 'player' AS source FROM players WHERE name ILIKE %s",
            ('%' + query + '%', ))
        results.extend(cur.fetchall())

        cur.close()

    return render_template('search.html', results=results, query=query)

@app.route('/admin')
def admin():
    if 'user_id' not in session or not session.get('is_admin'):
        return redirect(url_for('login'))
    return render_template('admin.html')

@app.route('/user')
def user():
    return redirect(url_for('user.user_dashboard'))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    db = get_db()
    cur = db.cursor()
    user_id = session['user_id']

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Check if the username already exists
        cur.execute(
            'SELECT * FROM users WHERE username = %s AND user_id != %s',
            (username, user_id))
        existing_user = cur.fetchone()
        if existing_user:
            flash('Username already taken', 'error')
            return redirect(url_for('profile'))

        # Check if the email already exists
        cur.execute('SELECT * FROM users WHERE email = %s AND user_id != %s',
                    (email, user_id))
        existing_email = cur.fetchone()
        if existing_email:
            flash('Email already registered', 'error')
            return redirect(url_for('profile'))

        # Hash the password if it is updated
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        cur.execute(
            'UPDATE users SET username = %s, email = %s, password = %s WHERE user_id = %s',
            (username, email, hashed_password, user_id))
        db.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))

    cur.execute('SELECT username, email FROM users WHERE user_id = %s',
                (user_id, ))
    user = cur.fetchone()
    cur.close()

    return render_template('profile.html', user=user)

if __name__ == '__main__':
    app.run(debug=True)
