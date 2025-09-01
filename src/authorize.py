from flask import Flask, request, redirect
import requests
import sqlite3
import datetime
from collections import defaultdict
from flask import Flask, request, redirect, render_template_string

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

# filepath: c:\Users\Admin\strava-app\src\authorize.py
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
    if 'access_token' not in data:
        error_msg = data.get('message', 'Unknown error')
        return f"Error authorizing: {error_msg}<br>{data}"

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

    # Fetch and save recent activities for this athlete
    now = int(datetime.datetime.now().timestamp())
    four_weeks_ago = now - 28 * 24 * 60 * 60
    activities_url = f'https://www.strava.com/api/v3/athlete/activities?after={four_weeks_ago}'
    headers = {'Authorization': f'Bearer {access_token}'}
    activities_response = requests.get(activities_url, headers=headers)
    if activities_response.status_code == 200:
        activities = activities_response.json()
        conn = sqlite3.connect('strava_activities.db')
        c = conn.cursor()
        for activity in activities:
            date_str = activity.get('start_date_local', '')
            if not date_str:
                continue
            date_obj = datetime.datetime.strptime(date_str[:10], '%Y-%m-%d')
            week_start = date_obj - datetime.timedelta(days=date_obj.weekday())
            week_label = week_start.strftime('%Y-%m-%d')
            c.execute('''INSERT OR IGNORE INTO activities (id, athlete_id, name, distance, start_date_local, week_start) VALUES (?, ?, ?, ?, ?, ?)''',
                      (activity.get('id'), athlete_id, activity.get('name', 'No Name'), activity.get('distance', 0), date_str, week_label))
        conn.commit()
        conn.close()
    else:
        print("Could not fetch activities:", activities_response.text)

    return redirect(f"/stats?athlete_id={athlete_id}")

@app.route('/stats')
def stats():
    athlete_id = request.args.get('athlete_id')
    conn = sqlite3.connect('strava_activities.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT firstname, lastname FROM athletes WHERE id=?", (athlete_id,))
    athlete = c.fetchone()
    c.execute("SELECT * FROM activities WHERE athlete_id=? ORDER BY start_date_local DESC", (athlete_id,))
    activities = c.fetchall()
    conn.close()

    # Group activities by week
    weeks = defaultdict(list)
    for activity in activities:
        date_str = activity['start_date_local']
        date_obj = datetime.datetime.strptime(date_str[:10], '%Y-%m-%d')
        week_start = date_obj - datetime.timedelta(days=date_obj.weekday())
        week_label = week_start.strftime('%Y-%m-%d')
        weeks[week_label].append(activity)

    # Render as HTML
    TEMPLATE = """
    <h2>Weekly Stats for {{ athlete_name }}</h2>
    {% for week_label, acts in weeks.items() %}
      <h3>Week starting {{ week_label }}</h3>
      <ul>
      {% for activity in acts %}
        <li>{{ activity['name'] }} | {{ "%.2f"|format(activity['distance']/1000) }} km | {{ activity['start_date_local'] }}</li>
      {% endfor %}
      </ul>
    {% endfor %}
    """
    athlete_name = f"{athlete['firstname']} {athlete['lastname']}" if athlete else "Unknown"
    return render_template_string(TEMPLATE, athlete_name=athlete_name, weeks=weeks)

# ...existing code...

if __name__ == '__main__':
    app.run(debug=True)