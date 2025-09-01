from flask import Flask, request, redirect
import requests
import sqlite3

def setup_db():
    conn = sqlite3.connect('strava_activities.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS athletes (
        id INTEGER PRIMARY KEY,
        firstname TEXT,
        lastname TEXT,
        access_token TEXT,
        refresh_token TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY,
        athlete_id INTEGER,
        name TEXT,
        distance REAL,
        start_date_local TEXT,
        week_start TEXT,
        FOREIGN KEY (athlete_id) REFERENCES athletes(id)
    )''')
    conn.commit()
    conn.close()
# ...existing code...
setup_db()

CLIENT_ID = '130483'
CLIENT_SECRET = 'd4088d3c389b9e6c31753f62ef381ee65b8c5713'
REDIRECT_URI = 'http://localhost:5000/exchange_token'

app = Flask(__name__)

@app.route('/')
def home():
    auth_url = (
        f"https://www.strava.com/oauth/authorize?client_id={CLIENT_ID}"
        f"&response_type=code&redirect_uri={REDIRECT_URI}"
        f"&scope=activity:read&approval_prompt=force"
    )
    return f'<a href="{auth_url}">Authorize Strava</a>'

@app.route('/exchange_token')
def exchange_token():
    code = request.args.get('code')
    token_url = 'https://www.strava.com/oauth/token'
    response = requests.post(token_url, data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'grant_type': 'authorization_code'
    })
    data = response.json()
    access_token = data['access_token']
    refresh_token = data['refresh_token']

    # Get athlete profile
    profile = requests.get(
        'https://www.strava.com/api/v3/athlete',
        headers={'Authorization': f'Bearer {access_token}'}
    ).json()
    athlete_id = profile['id']
    firstname = profile['firstname']
    lastname = profile['lastname']

    # Save athlete to DB
    conn = sqlite3.connect('strava_activities.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO athletes (id, firstname, lastname, access_token, refresh_token) VALUES (?, ?, ?, ?, ?)',
              (athlete_id, firstname, lastname, access_token, refresh_token))
    conn.commit()
    conn.close()
    return f"Authorized {firstname} {lastname}! You can close this window."

if __name__ == '__main__':
    app.run(debug=True)