from flask import Flask, render_template_string
import sqlite3

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Strava Dashboard</title>
    <style>
        table { border-collapse: collapse; width: 80%; margin: 20px auto; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background: #eee; }
        h2 { text-align: center; }
    </style>
</head>
<body>
    <h2>Strava Activities Dashboard</h2>
    <table>
        <tr>
            <th>Week Start</th>
            <th>Activity Name</th>
            <th>Distance (km)</th>
            <th>Date</th>
        </tr>
        {% for activity in activities %}
        <tr>
            <td>{{ activity['week_start'] }}</td>
            <td>{{ activity['name'] }}</td>
            <td>{{ "%.2f"|format(activity['distance']/1000) }}</td>
            <td>{{ activity['start_date_local'] }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route('/')
def dashboard():
    conn = sqlite3.connect('strava_activities.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM activities ORDER BY week_start DESC, start_date_local DESC")
    activities = cur.fetchall()
    conn.close()
    return render_template_string(TEMPLATE, activities=activities)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)