import os
import json
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

AMADEUS_CLIENT_ID = os.environ["AMADEUS_CLIENT_ID"]
AMADEUS_CLIENT_SECRET = os.environ["AMADEUS_CLIENT_SECRET"]

with open("airports.json") as f:
    AIRPORTS = json.load(f)

HUBS = [
    "ATL","ORD","DFW","DEN","LAX","JFK","EWR","MIA","SEA","SFO","CLT","IAH","PHX","BOS","MSP","DTW","PHL",
    "YVR","YYC","YYZ","YUL","MEX","CUN","LHR","LGW","CDG","FRA","AMS","MAD","BCN","IST","ZRH","MUC","CPH",
    "DXB","DOH","AUH","JNB","CPT","NBO","CAI","NRT","HND","ICN","PEK","PVG","SIN","HKG","BKK","KUL",
    "SYD","MEL","AKL","GRU","EZE","GIG","SCL","BOG","LIM","PTY"
]

def get_token():
    url = 'https://test.api.amadeus.com/v1/security/oauth2/token'
    data = {
        'grant_type': 'client_credentials',
        'client_id': AMADEUS_CLIENT_ID,
        'client_secret': AMADEUS_CLIENT_SECRET
    }
    return requests.post(url, data=data).json()['access_token']

@app.route('/airports')
def get_airports():
    return jsonify(AIRPORTS)

@app.route('/search')
def search_direct():
    origin = request.args.get("origin")
    dest = request.args.get("destination")
    date = request.args.get("date")
    adults = request.args.get("adults", 1)
    token = get_token()
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": dest,
        "departureDate": date,
        "adults": adults,
        "max": 3
    }
    return jsonify(requests.get(url, headers=headers, params=params).json())

def find_leg(token, origin, dest, date):
    url = "https://test.api.amadeus.com
