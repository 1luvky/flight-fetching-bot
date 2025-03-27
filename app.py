from flask import Flask, request, jsonify, render_template
import spacy
import requests
from dateparser import parse

app = Flask(__name__)

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# API credentials
RAPIDAPI_KEY = "f5e06178e6msh3dbe951a8063592p10a94bjsn15759e0d8496"
RAPIDAPI_HOST = "sky-scrapper.p.rapidapi.com"
CHATGPT_HOST = "chatgpt-42.p.rapidapi.com"


@app.route('/')
def index():
    return render_template("home.html")

def extract_entities(user_input):
    doc = nlp(user_input)
    entities = {"departure": None, "destination": None, "date": None}

    for ent in doc.ents:
        if ent.label_ == "GPE":
            if not entities["departure"]:
                entities["departure"] = ent.text
            else:
                entities["destination"] = ent.text
        elif ent.label_ == "DATE":
            parsed_date = parse(ent.text)
            if parsed_date:
                entities["date"] = parsed_date.strftime("%Y-%m-%d")

    return entities

@app.route("/get_response", methods=["POST"])
def get_response():
    data = request.get_json()
    user_message = data.get("message", "")
    extracted_entities = extract_entities(user_message)
    return jsonify(extracted_entities)

@app.route("/chat_with_ai", methods=["POST"])
def chat_with_ai():
    data = request.get_json()
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400
    
    # First check if it's flight-related
    extracted_entities = extract_entities(user_message)
    if extracted_entities["departure"] and extracted_entities["destination"]:
        return jsonify({
            "type": "flight",
            "data": extracted_entities
        })
    
    # If not flight-related, use ChatGPT API
    url = "https://chatgpt-42.p.rapidapi.com/chat"
    payload = {
        "messages": [{"role": "user", "content": user_message}],
        "model": "gpt-4o-mini"
    }
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": CHATGPT_HOST,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        chat_response = response.json()
        print("ChatGPT Raw Response:", chat_response)  # Debug log
        
        # Safely extract the response content
        ai_message = chat_response.get('choices', [{}])[0].get('message', {}).get('content', 'No response from AI')
        
        return jsonify({
            "type": "ai",
            "message": ai_message
        })
    except Exception as e:
        print("Error:", str(e))  # Debug log
        return jsonify({
            "type": "error",
            "message": f"Error processing your request: {str(e)}"
        }), 500

@app.route("/get_airport_codes", methods=["GET"])
def get_airport_codes():
    departure_city = request.args.get("departure")
    destination_city = request.args.get("destination")

    print(f"📥 Received request: departure={departure_city}, destination={destination_city}")  # Debug log

    if not departure_city or not destination_city:
        return jsonify({"error": "Both departure and destination cities are required"}), 400

    url = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchAirport"
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }

    def fetch_airport_code(city):
        try:
            print(f"🔍 Fetching airport code for {city}...")  # Debug log
            response = requests.get(url, headers=headers, params={"query": city, "locale": "en-US"})
            response.raise_for_status()
            data = response.json()
            print(f"✅ API Response for {city}: {data}")  # Debug log

            if "data" in data and data["data"]:  # Ensure correct key
                airport = data["data"][0]  # Get first airport
                return {
                "code": airport.get("skyId", "N/A"),
                "entityId": airport.get("entityId", "N/A"),  # NEW
                "country": airport["presentation"]["subtitle"],  # Country name
                "name": airport["presentation"]["title"]  # Airport name
            }
        except Exception as e:
            print(f"❌ Error fetching airport code for {city}: {e}")  # Debug log
            return None

    origin_info = fetch_airport_code(departure_city)
    destination_info = fetch_airport_code(destination_city)

    if origin_info and destination_info:
        return jsonify({
            "origin": origin_info,
            "destination": destination_info
        })
    else:
        return jsonify({"error": "Unable to find airport codes"}), 404


@app.route("/get_flight", methods=["GET"])
def get_flight():
    origin = request.args.get("origin")
    destination = request.args.get("destination")
    origin_entity = request.args.get("originEntityId")  # NEW
    destination_entity = request.args.get("destinationEntityId")  # NEW
    date = request.args.get("date")
    currency = request.args.get("currency", "USD")  # Default to USD
    market = request.args.get("market", "en-US")  # Default to English market
    countryCode = request.args.get("countryCode", "US")  # Default to United States

    if not origin or not destination or not date or not origin_entity or not destination_entity:
        return jsonify({"error": "Missing flight details"}), 400

    url = "https://sky-scrapper.p.rapidapi.com/api/v1/flights/searchFlights"
    querystring = {
        "originSkyId": origin,
        "destinationSkyId": destination,
        "originEntityId": origin_entity,  # NEW
        "destinationEntityId": destination_entity,  # NEW
        "date": date,
        "currency": currency,
        "market": market,
        "countryCode": countryCode,
        "cabinClass": "economy",
        "adults": "1"
    }

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
 
    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        print(jsonify(response.json()))
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
