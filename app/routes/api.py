from flask import Blueprint, jsonify, request, session
import json
import os

from app.services.chat import classify_query, get_greeting_response, create_prompt, query_openai
from app.services.strava import get_raw_activities, process_activities
from app.models.settings import get_settings_from_file

api_bp = Blueprint('api', __name__)

# API Route 1: Save settings to JSON file

@api_bp.route('/api/save-settings', methods=['POST'])
def save_settings():
    try:
        # Get the data from the request
        data = request.get_json()
        # print(f"Incoming data to save: {data}")  # Debug incoming settings
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        max_hr = data.get('maxHR', 200)
        zones = data.get('zones', {})

        # Validation
        errors = []
        prev_max = 0

        for zone, values in zones.items():
            min_val = values.get('min')
            max_val = values.get('max')
            if not (0 <= min_val < max_val <= 100):
                errors.append(f"Zone {zone} must have 0 <= min < max <= 100.")
            if min_val <= prev_max:
                errors.append(f"Zone {zone} must start after the previous zone.")
            prev_max = max_val

        # Check for gaps
        sorted_zones = sorted(zones.values(), key=lambda z: z['min'])
        for i in range(1, len(sorted_zones)):
            if sorted_zones[i]['min'] > sorted_zones[i - 1]['max'] + 1:
                errors.append(f"There is a gap between zones.")

        if errors:
            return jsonify({"error": "Validation failed", "details": errors}), 400

        # Save to file (or database)
        with open('settings.json', 'w') as file:
            json.dump({"maxHR": max_hr, "zones": zones}, file)

        return jsonify({"message": "Settings saved successfully!"}), 200
    except Exception as e:
        print(f"Error saving settings: {e}")
        return jsonify({"error": "Failed to save settings"}), 500

# API Route 2: Load settings from JSON file

@api_bp.route('/api/get-settings', methods=['GET'])
def get_settings():
    settings_file = 'settings.json'
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            settings_data = json.load(f)
        return jsonify(settings_data), 200
    else:
        # Default settings if file doesn't exist
        default_settings = {
            "maxHR": 200,
            "zones": {
                "1": {"min": 50, "max": 59, "name": "Recovery"},
                "2": {"min": 60, "max": 69, "name": "Aerobic Endurance"},
                "3": {"min": 70, "max": 79, "name": "Tempo"},
                "4": {"min": 80, "max": 89, "name": "Threshold"},
                "5": {"min": 90, "max": 100, "name": "VO2 Max"}
            }
        }
        return jsonify(default_settings), 200

# API Route 3: Calculate zone

@api_bp.route('/api/calculate-zone', methods=['POST'])
def calculate_zone():
    try:
        data = request.get_json()
        average_hr = data.get('average_hr')
        # print(f"Average HR used for zone calculation: {average_hr}")  # Debugging line

        # Strip "bpm" if present and convert to float
        if isinstance(average_hr, str) and 'bpm' in average_hr:
            average_hr = average_hr.replace(' bpm', '')

        # Early return if average_hr is None or not provided
        if average_hr is None:
            return jsonify({
                "zone": "Unknown Zone",
                "name": "No heart rate data available"
            }), 200

        # Load saved settings from file
        settings = get_settings_from_file()

        if not settings:
            return jsonify({"error": "Settings not found"}), 400

        max_hr = settings['maxHR']
        saved_zones = settings['zones']

        # Convert average_hr to float/int if it's a string
        try:
            average_hr = float(average_hr)
        except (TypeError, ValueError):
            return jsonify({
                "zone": "Invalid",
                "name": "Invalid heart rate value"
            }), 200

        # Validation for edge cases
        if average_hr > max_hr:
            return jsonify({
                "zone": "Invalid",
                "name": "Average heart rate exceeds maximum heart rate"
            }), 200
        if average_hr < 0:
            return jsonify({
                "zone": "Invalid",
                "name": "Heart rate cannot be negative"
            }), 200

        # # Debug line for percentage calculation
        # hr_percentage = (average_hr / max_hr) * 100
        # print(f"Debug: Average HR: {average_hr}, Max HR: {max_hr}, Percentage: {hr_percentage:.2f}%")

        # Determine which zone the heart rate falls into
        for zone_num, zone_data in saved_zones.items():
            min_hr = round((zone_data['min'] / 100) * max_hr)
            # Extend the upper limit of the zone to include all decimals
            max_hr_zone = round(((zone_data['max'] + 0.999999) / 100) * max_hr)

            # print(f"Debug: Zone {zone_num} range: {min_hr}-{max_hr_zone} bpm") # Debug line

            if min_hr <= average_hr <= max_hr_zone:
                return jsonify({
                    "zone": f"Zone {zone_num}",
                    "name": zone_data['name']
                }), 200

        return jsonify({
            "zone": "Unknown Zone",
            "name": "No matching zone found"
        }), 200
    except Exception as e:
        print(f"Error in calculate_zone: {e}")
        return jsonify({"error": str(e)}), 500

# API Route 4: Chatbot

@api_bp.route('/api/chat', methods=['POST'])
def chat():
    user_input = request.json.get("message", "").strip()
    print(f"User Input: {user_input}")  # Debug log

    # Get access token from session or request
    access_token = session.get("access_token") or request.json.get("access_token")

    if not access_token:
        return jsonify({"response": "Authorization error: No valid Strava access token found. Please log in again."}), 401

    # Classify the query
    classification = classify_query(user_input)
    print(f"Classification: {classification}")  # Debug log

    if classification == "greeting":
        user_input = request.json.get("message", "").strip()
        return jsonify({"response": get_greeting_response(user_input)})

    if classification == "irrelevant":
        return jsonify({"response": "I'm sorry, I can only help with sports-related queries like running, cycling, or training advice."})

    if classification == "relevant":
        # Fetch fresh activities every time
        raw_activities = get_raw_activities(access_token)
        processed_activities_csv = process_activities(raw_activities)
        
        # Create prompt with fresh activity data
        prompt = create_prompt(processed_activities_csv, user_input)
        
        # Query GPT
        gpt_response = query_openai(prompt, max_tokens=600)
        return jsonify({"response": gpt_response})

    # Fallback response
    return jsonify({"response": "Sorry, I couldn't process your query. Please try again."})