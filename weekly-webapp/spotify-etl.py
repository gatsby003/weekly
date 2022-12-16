import requests
import base64
from requests.models import PreparedRequest

from flask import Flask, redirect, request

app = Flask(__name__)

CLIENT_ID = '46a828fc7c8b4ff08dc7ab18aa972293'
CLIENT_SECRET = 'bf254fabce3b44a99ff3b7a50ee38e02'
secret_string = CLIENT_ID + ":" + CLIENT_SECRET

in_bytes = secret_string.encode('ascii')

base64_secret_string = base64.b64encode(in_bytes).decode('ascii')
print(base64_secret_string)

url = 'https://accounts.spotify.com/authorize?'
params = {
            'client_id':'46a828fc7c8b4ff08dc7ab18aa972293',
            'response_type':'code',
            'redirect_uri':'http://127.0.0.1:5000/home',
            'state':'spotify_state',
            'scope':'user-read-recently-played'
        }
req = PreparedRequest()
req.prepare_url(url,params)

@app.route('/home')
def home():
    code = request.args['code']
    print(code)
    res = requests.post(
        url='https://accounts.spotify.com/api/token',
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri" : "http://127.0.0.1:5000/home"
        },
        headers={
            "Authorization": 'Basic ' + 'NDZhODI4ZmM3YzhiNGZmMDhkYzdhYjE4YWE5NzIyOTM6YmYyNTRmYWJjZTNiNDRhOTlmZjNiN2E1MGVlMzhlMDI=',
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    data = res.json()
    print(res.json())
    return "You are authenticated"

@app.route('/login')
def login():
    print(req.url)
    return redirect(req.url, code=302)
