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

# Load airport list
with open("airports.json") as f:
    AIRPORTS = json.load(f)

# Global layover hubs
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
    response = requests.post(url, data=data)
    return response.json()['access_token']

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
    response = requests.get(url, headers=headers, params=params)
    return jsonify(response.json())

def find_leg(token, origin, dest, date):
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": dest,
        "departureDate": date,
        "adults": 1,
        "max": 2
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json().get("data", [])

def get_layover_minutes(arr, dep):
    FMT = "%Y-%m-%dT%H:%M:%S"
    arr_time = datetime.strptime(arr[:19], FMT)
    dep_time = datetime.strptime(dep[:19], FMT)
    return int((dep_time - arr_time).total_seconds() // 60)

@app.route("/multileg_search")
def multileg_search():
    origin = request.args.get("origin")
    dest = request.args.get("destination")
    date = request.args.get("date")
    max_layover = int(request.args.get("max_layover", 720))  # in minutes
    layover_hub = request.args.get("layover_hub")
    token = get_token()
    hubs = [layover_hub] if layover_hub else HUBS

    results = []
    for hub in hubs:
        if hub in (origin, dest): continue
        legs1 = find_leg(token, origin, hub, date)
        for fl1 in legs1:
            try:
                arr1 = fl1["itineraries"][0]["segments"][-1]["arrival"]["at"]
                arr_time = datetime.strptime(arr1[:19], "%Y-%m-%dT%H:%M:%S")
                for d2 in [arr_time.strftime("%Y-%m-%d"), (arr_time+timedelta(days=1)).strftime("%Y-%m-%d")]:
                    legs2 = find_leg(token, hub, dest, d2)
                    for fl2 in legs2:
                        dep2 = fl2["itineraries"][0]["segments"][0]["departure"]["at"]
                        layover = get_layover_minutes(arr1, dep2)
                        if 120 <= layover <= max_layover:
                            price = float(fl1["price"]["total"]) + float(fl2["price"]["total"])
                            results.append({
                                "route": f"{origin} → {hub} → {dest}",
                                "layover": {
                                    "city": hub,
                                    "minutes": layover,
                                    "arr_time": arr1,
                                    "dep_time": dep2
                                },
                                "legs": [fl1, fl2],
                                "total_price": price
                            })
            except Exception as e:
                print(f"Skipping due to error: {e}")
                continue

    results.sort(key=lambda x: x["total_price"])
    return jsonify(results[:5])

if __name__ == "__main__":
    app.run(debug=True)


def find_leg(token, origin, dest, date):
    url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
    headers = {'Authorization': f'Bearer {token}'}
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": dest,
        "departureDate": date,
        "adults": 1,
        "max": 2
    }
    response = requests.get(url, headers=headers, params=params)
    return response.json().get("data", [])

