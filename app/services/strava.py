import datetime
from datetime import timedelta
import requests

# Function 1: Get raw activities

def get_raw_activities(access_token):
    base_url = "https://www.strava.com/api/v3"
    headers = {"Authorization": f"Bearer {access_token}"}
    now = datetime.now()
    six_months_ago = int((now - timedelta(days=180)).timestamp())

    all_activities = []
    page = 1
    
    while True:
        params = {
            "after": six_months_ago,
            "per_page": 200,
            "page": page
        }

        response = requests.get(f"{base_url}/athlete/activities", headers=headers, params=params)
        
        if response.status_code != 200:
            print(f"Error fetching Strava data: {response.text}")
            break

        activities = response.json()
        if not activities:  # No more activities to fetch
            break
            
        all_activities.extend(activities)
        page += 1

    return all_activities

# Function 2: Process the raw activities 

def process_activities(raw_activities):
    valid_activities = []
    
    # Define a mapping of Strava activity types to our desired labels
    activity_type_map = {
        "Run": "Run",
        "Ride": "Ride",
        "Hike": "Hike",
        "Swim": "Swim",
    }
    
    for act in raw_activities:
        try:
            # Extract necessary data
            name = act.get("name", "Unnamed Activity").replace(",", " ")  # Remove commas to avoid CSV issues
            distance = round(act["distance"] / 1000, 1)  # Convert meters to km
            elevation_gain = act.get("total_elevation_gain", 0)  # Elevation in meters
            avg_hr = act.get("average_heartrate", "N/A")  # Average heart rate
            elapsed_time = round(act["elapsed_time"] / 60, 1)  # Convert seconds to minutes
            
            # Get the activity type from the mapping
            activity_type = activity_type_map.get(act["type"], "Unsupported")  # Default to "Unsupported" for unknown types
            
            # Skip unsupported activity types
            if activity_type == "Unsupported":
                print(f"Skipping unsupported activity type: {act['type']}")
                continue
            
            # Calculate pace/speed based on the activity type
            if activity_type == "Run":
                pace_speed = round((elapsed_time / distance), 2) if distance > 0 else "N/A"  # min/km
            elif activity_type == "Ride":
                pace_speed = round(distance / (elapsed_time / 60), 1) if elapsed_time > 0 else "N/A"  # km/h
            else:
                pace_speed = "N/A"  # Other types don't need pace/speed

            # Append as CSV-like row if all critical data is valid
            if isinstance(avg_hr, (int, float)) and distance > 0 and elapsed_time > 0:
                valid_activities.append(
                    f"{activity_type},{name},{distance},{elevation_gain},{avg_hr},{pace_speed},{elapsed_time}"
                )
        except Exception as e:
            print(f"Skipping invalid activity: {act} (Error: {e})")
            continue

    return "\n".join(valid_activities)  # Join all rows into a single string