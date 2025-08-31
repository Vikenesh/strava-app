from flask import Flask, render_template_string
import sqlite3

app = Flask(__name__)

@app.route('/')
def dashboard():
    conn = sqlite3.connect('strava_activities.db')
    c = conn.cursor()
    c.execute('SELECT id, name, distance, start_date_local, week_start FROM activities ORDER BY start_date_local DESC')
    activities = c.fetchall()
    conn.close()
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Strava Activities Dashboard</title>
        <style>
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h2>Strava Activities Dashboard</h2>
        <table>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Distance (km)</th>
                <th>Date</th>
                <th>Week Start</th>
            </tr>
            {% for id, name, distance, start_date_local, week_start in activities %}
            <tr>
                <td>{{ id }}</td>
                <td>{{ name }}</td>
                <td>{{ '%.2f' % (distance/1000) }}</td>
                <td>{{ start_date_local }}</td>
                <td>{{ week_start }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    '''
    return render_template_string(html, activities=activities)

if __name__ == '__main__':
    app.run(debug=True)
