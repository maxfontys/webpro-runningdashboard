import json
import os
from flask import request, jsonify

# Function 1: Get settings from settings.json file

def get_settings_from_file():
    settings_file = 'settings.json'
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            return json.load(f)
    return None

# Function 2: Save settings

def save_settings():
    try:
        # Get the data from the request
        data = request.get_json()
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
