import requests

CLIENT_ID = '130483'
CLIENT_SECRET = 'd4088d3c389b9e6c31753f62ef381ee65b8c5713'
CODE = '68158b52367c20a68a53f7e6e125b6572491bb7d'  # Replace with the code from the redirect URL

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
