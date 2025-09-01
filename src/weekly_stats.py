import requests
import time
import datetime
import sqlite3
from collections import defaultdict

CLIENT_ID = '130483'  # Replace with your Strava client ID
CLIENT_SECRET = 'd4088d3c389b9e6c31753f62ef381ee65b8c5713'  # Replace with your Strava client secret
REFRESH_TOKEN = 'd5bb6b81044b0ae8735f30d2fcc6e0a32f9f3985'  # Replace with your Strava refresh token

def refresh_access_token():
    url = 'https://www.strava.com/oauth/token'
    payload = {
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'grant_type': 'refresh_token',
        'refresh_token': REFRESH_TOKEN
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        data = response.json()
        return data['access_token']
    else:
        print('Error refreshing token:', response.status_code, response.text)
        return None

ACCESS_TOKEN = '84eacdbaa980c9140e965463ad75764b3ef60f13'
# ACCESS_TOKEN = refresh_access_token()

# ...existing code...
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

def save_activities_to_db(activities):
    conn = sqlite3.connect('strava_activities.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY,
        name TEXT,
        distance REAL,
        start_date_local TEXT,
        week_start TEXT
    )''')
    for activity in activities:
        date_str = activity.get('start_date_local', '')
        if not date_str:
            continue
        date_obj = datetime.datetime.strptime(date_str[:10], '%Y-%m-%d')
        week_start = date_obj - datetime.timedelta(days=date_obj.weekday())
        week_label = week_start.strftime('%Y-%m-%d')
        c.execute('''INSERT OR IGNORE INTO activities (id, name, distance, start_date_local, week_start) VALUES (?, ?, ?, ?, ?)''',
                  (activity.get('id'), activity.get('name', 'No Name'), activity.get('distance', 0), date_str, week_label))
    conn.commit()
    conn.close()


def fetch_and_save_activities_for_all():
    now = int(time.time())
    four_weeks_ago = now - 28 * 24 * 60 * 60
    url_template = 'https://www.strava.com/api/v3/athlete/activities?after={after}'
    for athlete in get_all_athletes():
        athlete_id, firstname, lastname, access_token = athlete
        url = url_template.format(after=four_weeks_ago)
        headers = {'Authorization': f'Bearer {access_token}'}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            activities = response.json()
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
            print(f"Saved activities for {firstname} {lastname}")
        else:
            print(f"Error for {firstname} {lastname}: {response.status_code}")
if ACCESS_TOKEN:
    now = int(time.time())
    four_weeks_ago = now - 28 * 24 * 60 * 60
    url = f'https://www.strava.com/api/v3/athlete/activities?after={four_weeks_ago}'
    headers = {'Authorization': f'Bearer {ACCESS_TOKEN}'}

    # Fetch athlete profile for name
    profile_url = 'https://www.strava.com/api/v3/athlete'
    profile_response = requests.get(profile_url, headers=headers)
    athlete_name = 'Unknown'
    if profile_response.status_code == 200:
        athlete = profile_response.json()
        athlete_name = athlete.get('firstname', '') + ' ' + athlete.get('lastname', '')

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        activities = response.json()
        save_activities_to_db(activities)
        print(f'Athlete: {athlete_name}')

        # Calculate and print monthly mileage
        monthly_mileage = sum(activity.get('distance', 0) for activity in activities) / 1000  # meters to km
        print(f'Total Monthly Mileage: {monthly_mileage:.2f} km')

        # Group activities by calendar week
        weeks = defaultdict(list)
        for activity in activities:
            date_str = activity.get('start_date_local', '')
            if not date_str:
                continue
            date_obj = datetime.datetime.strptime(date_str[:10], '%Y-%m-%d')
            week_start = date_obj - datetime.timedelta(days=date_obj.weekday())
            week_label = week_start.strftime('%Y-%m-%d')
            weeks[week_label].append(activity)
        # Sort weeks by date (descending)
        print('Monthly Activities (split by calendar week):')
        for week_label in sorted(weeks.keys(), reverse=True):
            print(f'\nWeek starting {week_label}:')
            for activity in weeks[week_label]:
                print(f"- {activity.get('name', 'No Name')} | Distance: {activity.get('distance', 0)/1000:.2f} km | Date: {activity.get('start_date_local', '')}")
    else:
        print('Error:', response.status_code, response.text)
else:
    print('Could not refresh access token.')

setup_db()
fetch_and_save_activities_for_all()
# Step 1: Get a new authorization code
# Visit this URL in your browser (replace REDIRECT_URI if needed):
# https://www.strava.com/oauth/authorize?client_id=130483&response_type=code&redirect_uri=http://localhost/exchange_token&scope=activity:read&approval_prompt=force
# After authorizing, copy the 'code' from the redirect URL.

# Step 2: Exchange the code for new tokens
# Uncomment and run this block once to get your new access and refresh tokens:
'''
import requests

CLIENT_ID = '130483'
CLIENT_SECRET = 'd4088d3c389b9e6c31753f62ef381ee65b8c5713'
CODE = 'PASTE_CODE_HERE'  # Replace with the code from the redirect URL

response = requests.post(
    'https://www.strava.com/oauth/token',
    data={
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': CODE,
        'grant_type': 'authorization_code'
    }
)
print(response.json())  # Copy the new access_token and refresh_token into your script below
'''