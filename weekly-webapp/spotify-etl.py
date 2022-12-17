import requests
import base64
from os import environ 
from requests.models import PreparedRequest

from flask import Flask, redirect, request

app = Flask(__name__)

CLIENT_ID = environ.get('CLIENT_ID')
CLIENT_SECRET = environ.get('CLIENT_SECRET')
secret_string = CLIENT_ID + ":" + CLIENT_SECRET

in_bytes = secret_string.encode('ascii')

base64_secret_string = base64.b64encode(in_bytes).decode('ascii')
print(base64_secret_string)
url = 'https://accounts.spotify.com/authorize?'
params = {
            'client_id':CLIENT_ID,
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
            "Authorization": 'Basic ' + base64_secret_string,
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
