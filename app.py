import requests
import json
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta, timezone
from flask import Flask, redirect, request, session, render_template, jsonify
from flask_cors import CORS, cross_origin
from pytz import utc
from collections import defaultdict, Counter
import time
from functools import lru_cache
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Get keys from the environment
load_dotenv()
CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
REDIRECT_URI = os.getenv('STRAVA_REDIRECT_URI')
app.secret_key = os.getenv('SECRET_KEY')

# Main pages
@app.route('/')
def login():
    return render_template('home.html')

@app.route('/logout')
def logout():
    if 'access_token' in session:
        requests.post("https://www.strava.com/oauth/deauthorize", 
                     data={'access_token': session['access_token']})
    
    session.clear()
    response = redirect('/')
    response.set_cookie('strava_auth', '', expires=0)  # Clear Strava cookies
    return response

@app.route('/login')
def login_strava():
    return redirect(f"https://www.strava.com/oauth/authorize"
                   f"?client_id={CLIENT_ID}"
                   f"&redirect_uri={REDIRECT_URI}"
                   f"&response_type=code"
                   f"&scope=read,activity:read"
                   f"&approval_prompt=force"
                   f"&prompt=consent")

@app.route('/callback')
def callback():
    """Handle Strava's callback and exchange authorization code for access token."""
    code = request.args.get('code')  # Get the authorization code from the query parameters
    
    if not code:
        return "Authorization failed. Please try again.", 400  # Handle missing code gracefully

    # Exchange the authorization code for an access token
    token_response = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code'
        }
    ).json()

    # Save the user's tokens and expiry in the session
    session['access_token'] = token_response.get('access_token')
    session['refresh_token'] = token_response.get('refresh_token')
    session['expires_at'] = token_response.get('expires_at')

    # Redirect to the dashboard
    return redirect('/dashboard')

# Chatbot

# Load OpenAI API key from .env and initialize client
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Use OpenAI to classify the query as 'greeting', 'relevant', or 'irrelevant'.
def classify_query(query):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": f"""
You are an intelligent query classifier for a running and fitness chatbot. Your role is to analyze the user's query and classify it into one of three categories:
- 'greeting': The user is starting the conversation with a casual or formal greeting. This could be slang as well.
- 'relevant': The user is asking a question directly related to their activities, running, cycling (riding), fitness, training, or performance nutrition. 
- 'irrelevant': The query is unrelated to fitness or training, such as asking about food recipes, math problems, or general knowledge.

Only return the single word, unstyled, no markup, just 'greeting', 'relevant', or 'irrelevant'. Nothing else.

User query: '{query}'
"""
                }
            ]
        )
        # Extract and clean the model's response
        classification = response.choices[0].message.content.strip().lower()

        # Normalize response to ensure it matches one of the valid categories
        classification = classification.strip(" '\"")  # Remove quotes or unexpected characters

        # Validate the response is an exact match to expected categories
        valid_categories = {"greeting", "relevant", "irrelevant"}
        if classification in valid_categories:
            return classification

        # Handle unexpected responses
        print(f"Unexpected classification response: {classification}")  # Debug log
        return "unknown"
    except Exception as e:
        print(f"Error in classify_query: {e}")
        return "unknown"

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

def create_prompt(activities_csv, user_query, max_activities=200):
    # Add explanation for the CSV format
    csv_explanation = """
    The activity data is presented in the following csv format:
    - Activity Type: Either 'Run' or 'Ride'.
    - Name: Name of the activity.
    - Distance: Distance in kilometers (km).
    - Elevation Gain: Elevation gain in meters (m).
    - Avg HR: Average heart rate in beats per minute (bpm).
    - Pace/Speed: For 'Run' activities, this is the average pace in minutes per kilometer (min/km). For 'Ride' activities, this is the average speed in kilometers per hour (km/h).
    - Duration: Duration of the activity in minutes (min).
    """
    # Ensure the activities are split into lines
    activities_list = activities_csv.splitlines()

    # Truncate activities to the maximum allowed
    activity_data = "\n".join(activities_list[:max_activities])

    # Combine explanation and data into the prompt
    prompt = f"""
You are a virtual running coach for a web app. Your purpose is to provide advice on whatever the user asks, whether that's running, cycling, training, or performance nutrition. Structure your response using simple sentences and clear spacing. Ensure that your response uses clear paragraphs with line breaks to separate ideas, making the information easy to read. Use a conversational and encouraging tone, while staying concise, clear, and actionable.

{csv_explanation}

Here is the user's recent training data:
{activity_data}

User question: {user_query}

Provide a tailored, well-structured and clear response based on the user's recent training. Respond as a natural human being. Do not respond like ChatGPT. Do not respond like a robot. Do not use unneccesary capital letters in headings. Do not use any markdown like ***bold*** or ### italic. Do not use lists.
"""
    return prompt

def query_openai(prompt, max_tokens=900):

    max_tokens = int(max_tokens)  # Explicitly cast to integer
    
    # Debugging print statement
    print(f"Prompt sent to GPT:\n{prompt}")  # Print the full prompt for debugging

    # Send to GPT
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in query_openai: {e}")
        return "Sorry, I couldn't process your request. Please try again."

def get_greeting_response(user_input):
    try:
        # Define the GPT prompt
        prompt = f"""
        You are a virtual assistant specializing in running, cycling, swimming, and fitness. You are part of a fitness dashboard web app built with the Strava API, so always act as if you already have access to the user's fitness data, including their recent activities and training progress. When responding to greetings, tailor your responses naturally and contextually while subtly reinforcing that you are ready to assist with their fitness journey. Keep your greeting short. Always sound confident, encouraging, and ready to assist with their training.

        User's input: {user_input}
        """
        
        # Send the prompt to GPT
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=50,  # Keep the response concise
            temperature=0.7
        )
        
        # Extract the response text
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in get_greeting_response: {e}")
        return "Sorry, I couldn't process your greeting. How can I assist you with your training?"

@app.route('/api/chat', methods=['POST'])
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

def get_settings_from_file():
    settings_file = 'settings.json'
    if os.path.exists(settings_file):
        with open(settings_file, 'r') as f:
            return json.load(f)
    return None

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'access_token' not in session:
        return redirect('/login')

    try:
        manifest_path = os.path.join(app.static_folder, 'dist', 'manifest.json')
        if os.path.exists(manifest_path):
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        else:
            manifest = {}
    except Exception as e:
        print(f"Error loading manifest: {e}")
        manifest = {}

    access_token = session['access_token']
    headers = {'Authorization': f"Bearer {access_token}"}

    # Fetch profile info
    profile_response = requests.get('https://www.strava.com/api/v3/athlete', headers=headers)
    if profile_response.status_code != 200:
        return f"Error fetching profile: {profile_response.status_code}, {profile_response.text}"
    profile = profile_response.json()

    # Fetch or cache activities
    if 'all_activities' not in session or time.time() > session.get('cache_expiry', 0):
        all_activities = []
        page = 1
        while True:
            activities_response = requests.get(
                'https://www.strava.com/api/v3/athlete/activities',
                headers=headers,
                params={'per_page': 100, 'page': page}
            )
            if activities_response.status_code != 200:
                return f"Error fetching activities: {activities_response.status_code}, {activities_response.text}"

            activities = activities_response.json()
            if not activities:
                break
            all_activities.extend(activities)
            page += 1

        session['all_activities'] = all_activities
        session['cache_expiry'] = time.time() + 600  # Cache expires in 10 minutes
    else:
        all_activities = session['all_activities']

    # Sort activities by start date (most recent first)
    all_activities = sorted(
        all_activities,
        key=lambda act: datetime.strptime(act['start_date_local'], "%Y-%m-%dT%H:%M:%S%z"),
        reverse=True
    )

    # Prepare detailed activity data for display, filtering for outdoor activities with GPS data
    detailed_activities = []
    for activity in all_activities:
        # Skip if activity is marked as indoor
        if activity.get('trainer', False) or activity.get('indoor', False):
            continue
            
        # Skip if activity doesn't have a polyline (indicating no GPS data)
        polyline = activity.get('map', {}).get('summary_polyline', '')
        if not polyline:
            continue
            
        # Skip if activity doesn't have start coordinates (another indicator of manual entry)
        start_latlng = activity.get('start_latlng', [])
        if not start_latlng:
            continue

        start_date = datetime.strptime(activity['start_date_local'], "%Y-%m-%dT%H:%M:%S%z")
        formatted_date = start_date.strftime("%A, %B %d, %Y")
        
        detailed_activities.append({
            "name": activity['name'],
            "distance": f"{activity['distance'] / 1000:.2f} km",
            "time": f"{activity['moving_time'] // 60} mins",
            "date": formatted_date,
            "polyline": polyline,
            "start_latlng": start_latlng,
            "url": f"https://www.strava.com/activities/{activity['id']}"
        })
        
        # Break once we have 5 outdoor activities
        if len(detailed_activities) >= 5:
            break

    # Rest of the stats calculations remain the same...
    now = datetime.now(timezone.utc)
    first_day_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    monthly_activities = [
        act for act in all_activities if datetime.strptime(act['start_date_local'], "%Y-%m-%dT%H:%M:%S%z") >= first_day_of_month
    ]
    monthly_distance = sum(act['distance'] for act in monthly_activities) / 1000
    monthly_time = sum(act['moving_time'] for act in monthly_activities) / 3600

    past_4_weeks = now - timedelta(weeks=4)
    last_4_weeks_activities = [
        act for act in all_activities if datetime.strptime(act['start_date_local'], "%Y-%m-%dT%H:%M:%S%z") > past_4_weeks
    ]
    last_4_weeks_distance = sum(act['distance'] for act in last_4_weeks_activities) / 1000
    last_4_weeks_time = sum(act['moving_time'] for act in last_4_weeks_activities) / 3600

    year_start = datetime(now.year, 1, 1, tzinfo=timezone.utc)
    yearly_activities = [
        act for act in all_activities if datetime.strptime(act['start_date_local'], "%Y-%m-%dT%H:%M:%S%z") >= year_start
    ]
    yearly_distance = sum(act['distance'] for act in yearly_activities) / 1000
    yearly_time = sum(act['moving_time'] for act in yearly_activities) / 3600

    data = {
        "profile": {
            "name": f"{profile['firstname']} {profile['lastname']}",
            "location": profile.get('city', 'Unknown Location'),
            "profile_picture": profile.get('profile', 'https://via.placeholder.com/80')
        },
        "monthly_stats": {
            "distance": f"{monthly_distance:.2f} km",
            "time": f"{int(monthly_time)} hrs {int((monthly_time % 1) * 60)} mins"
        },
        "last_4_weeks": {
            "activities_per_week": len(last_4_weeks_activities) // 4,
            "avg_distance_per_week": f"{last_4_weeks_distance / 4:.2f} km",
            "avg_time_per_week": f"{int(last_4_weeks_time / 4)} hrs {int(((last_4_weeks_time / 4) % 1) * 60)} mins",
        },
        "yearly_stats": {
            "activities": len(yearly_activities),
            "distance": f"{yearly_distance:.2f} km",
            "time": f"{int(yearly_time)} hrs {int((yearly_time % 1) * 60)} mins",
        },
        "activities": detailed_activities[:2],  # Only show first 2 outdoor activities
    }

# Middle section

    # Get the selected sport type from the request arguments (default to 'all')
    sport_type = request.args.get('sport_type', 'all').lower()

    # Calculate weekly stats (current week) - Current time
    now = datetime.now(timezone.utc)
    start_of_current_week = now - timedelta(days=now.weekday())
    start_of_current_week = start_of_current_week.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_current_week = start_of_current_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

    # Filter activities for the current week based on the sport type
    if sport_type == 'all':
        weekly_activities = [
            act for act in all_activities
            if start_of_current_week <= datetime.strptime(act['start_date_local'], "%Y-%m-%dT%H:%M:%S%z") <= end_of_current_week
        ]
    elif sport_type == 'ride':
        weekly_activities = [
            act for act in all_activities
            if start_of_current_week <= datetime.strptime(act['start_date_local'], "%Y-%m-%dT%H:%M:%S%z") <= end_of_current_week
            and act.get('sport_type', '').lower() in ['ride', 'virtualride', 'ebikeride', 'handcycle']
        ]
    else:
        weekly_activities = [
            act for act in all_activities
            if start_of_current_week <= datetime.strptime(act['start_date_local'], "%Y-%m-%dT%H:%M:%S%z") <= end_of_current_week
            and act.get('sport_type', '').lower() == sport_type
        ]

    # Calculate current week's stats
    weekly_distance = sum(act['distance'] for act in weekly_activities) / 1000
    weekly_time = sum(act['moving_time'] for act in weekly_activities) / 3600
    weekly_elevation = sum(act.get('total_elevation_gain', 0) for act in weekly_activities)

    # Weekly Chart Data: Current week + last 11 weeks
    weekly_labels = []
    weekly_distances = []

    weekly_labels.append(f"{start_of_current_week.strftime('%b %d')} - {end_of_current_week.strftime('%b %d')}")
    weekly_distances.append(round(weekly_distance, 2))

    for i in range(1, 12):
        start_of_week = start_of_current_week - timedelta(weeks=i)
        end_of_week = start_of_week + timedelta(days=6, hours=23, minutes=59, seconds=59)

        if sport_type == 'all':
            week_activities = [
                act for act in all_activities
                if start_of_week <= datetime.strptime(act['start_date_local'], "%Y-%m-%dT%H:%M:%S%z") <= end_of_week
            ]
        else:
            week_activities = [
                act for act in all_activities
                if start_of_week <= datetime.strptime(act['start_date_local'], "%Y-%m-%dT%H:%M:%S%z") <= end_of_week
                and act.get('sport_type', '').lower() == sport_type
            ]

        week_distance = sum(act['distance'] for act in week_activities) / 1000
        weekly_labels.append(f"{start_of_week.strftime('%b %d')} - {end_of_week.strftime('%b %d')}")
        weekly_distances.append(round(week_distance, 2))

    weekly_labels.reverse()
    weekly_distances.reverse()

    # Update weekly_stats in the data dictionary
    data["weekly_stats"] = {
        "distance": f"{weekly_distance:.2f} km",
        "time": f"{int(weekly_time)} hrs {int((weekly_time % 1) * 60)} mins",
        "elevation": f"{weekly_elevation:.0f} m"
    }

    data["weekly_chart"] = {
        "labels": weekly_labels,
        "distances": weekly_distances
    }

    # If AJAX request, return JSON data
    if request.args.get('sport_type'):
        return jsonify({
            "weekly_stats": data["weekly_stats"],
            "weekly_chart": data["weekly_chart"]
        })

# Zone section

    # Get user's settings or use defaults
    settings = get_settings_from_file()
    if settings:
        saved_max_hr = settings['maxHR']  # Get saved max HR
        saved_zones = settings['zones']
        
        # Use saved max HR directly
        max_hr = saved_max_hr
        
        # Convert percentage-based zones to actual heart rates
        zones = {}
        for zone_num, zone_data in saved_zones.items():
            min_hr = (zone_data['min'] / 100) * max_hr
            max_hr_zone = (zone_data['max'] / 100) * max_hr
            zone_name = f"Zone {zone_num}"
            zones[zone_name] = (min_hr, max_hr_zone)
    else:
        # Default calculations
        max_hr = profile.get('max_heart_rate') or (220 - profile.get('age', 30))
        zones = {
            "Zone 1": (0.50 * max_hr, 0.59 * max_hr),  # Recovery
            "Zone 2": (0.60 * max_hr, 0.69 * max_hr),   # Aerobic Endurance
            "Zone 3": (0.7 * max_hr, 0.79 * max_hr),   # Tempo
            "Zone 4": (0.80 * max_hr, 0.89 * max_hr),  # Threshold
            "Zone 5": (0.90 * max_hr, max_hr),         # VO2 Max
        }

    # Calculate average heart rate from activities
    activity_averages = []
    for activity in weekly_activities:
        if 'average_heartrate' in activity:
            activity_averages.append(activity['average_heartrate'])

    average_heart_rate = int(sum(activity_averages) / len(activity_averages)) if activity_averages else 0

    # Determine zone based on average heart rate
    zone_focus = None
    for zone, (low, high) in zones.items():
        if low <= average_heart_rate <= high:
            zone_focus = zone
            break

    zone_names = {
        "Zone 1": "Recovery",
        "Zone 2": "Aerobic Endurance",
        "Zone 3": "Tempo",
        "Zone 4": "Threshold",
        "Zone 5": "VO2 Max"
    }

    # print(f"Average HR: {average_heart_rate}")
    # print(f"Checking which zone {average_heart_rate} falls into:")

    for zone, (low, high) in zones.items():
        print(f"{zone}: {int(low)}-{int(high)} bpm")
        
    zone_focus_display = f"{zone_focus}: {zone_names[zone_focus]}" if zone_focus else "Unknown Zone"

    data["zone_focus"] = {
        "training_focus": zone_focus_display,
        "average_heart_rate": f"{average_heart_rate} bpm"
    }

# Heart Rate Trends section

    # Filter runs only (normal runs, trail runs, treadmill runs)
    running_activities = [
        act for act in all_activities 
        if act.get('sport_type') in ['Run', 'TrailRun', 'Treadmill', 'VirtualRun', 'RaceRun']
    ]

    # Define pace groups (20-second intervals in seconds per km)
    pace_groups = [
        (240, 260, "4:00–4:20"), (260, 280, "4:20–4:40"), (280, 300, "4:40–5:00"),
        (300, 320, "5:00–5:20"), (320, 340, "5:20–5:40"), (340, 360, "5:40–6:00"),
        (360, 380, "6:00–6:20"), (380, 400, "6:20–6:40"), (400, 420, "6:40–7:00"),
        (420, 440, "7:00–7:20"), (440, 460, "7:20–7:40"), (460, 480, "7:40–8:00")
    ]

    # Initialize heart rate trends data structure
    hr_trends_by_pace = {group[2]: {} for group in pace_groups}  # pace label -> month -> HR list

    # Process running activities
    for activity in running_activities:
        distance = activity.get('distance', 0)  # Distance in meters
        moving_time = activity.get('moving_time', 0)  # Time in seconds
        average_hr = activity.get('average_heartrate')  # Average heart rate

        # Skip activities with missing or invalid data
        if distance == 0 or moving_time == 0 or not average_hr:
            continue

        # Calculate average pace in seconds per km
        avg_pace = moving_time / (distance / 1000)  # sec/km

        # Match the pace to the appropriate pace group
        for low, high, pace_label in pace_groups:
            if low <= avg_pace < high:
                # Extract month from activity start date
                month = datetime.strptime(activity['start_date_local'], "%Y-%m-%dT%H:%M:%S%z").strftime("%b")
                year = datetime.strptime(activity['start_date_local'], "%Y-%m-%dT%H:%M:%S%z").year
                month_year = f"{month} '{str(year)[-2:]}"

                # Add HR data to the appropriate month and pace group
                if month_year not in hr_trends_by_pace[pace_label]:
                    hr_trends_by_pace[pace_label][month_year] = []
                hr_trends_by_pace[pace_label][month_year].append(average_hr)
                break  # Exit loop once pace group is matched

    # Calculate average heart rates for each month in each pace group
    final_hr_trends = {}
    for pace_label, monthly_data in hr_trends_by_pace.items():
        final_hr_trends[pace_label] = sorted([
            {"month_year": month_year, "bpm": round(sum(hr) / len(hr))}
            for month_year, hr in monthly_data.items()
        ], key=lambda x: datetime.strptime(x["month_year"], "%b '%y"))

    # Add the heart rate trends data to the template context
    data["heart_rate_trends_by_pace"] = final_hr_trends
    # print(json.dumps(data["heart_rate_trends_by_pace"], indent=2))
    data["pace_trends_json"] = json.dumps(data["heart_rate_trends_by_pace"])  # Pre-dump JSON
    # print("PACE_TRENDS_JSON:", data["pace_trends_json"])
    
    data["manifest"] = manifest  # Add manifest to your data dictionary
    return render_template('dashboard.html', data=data)

# Modal settings

# Save settings to JSON file
@app.route('/api/save-settings', methods=['POST'])
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

# Load settings from JSON file
@app.route('/api/get-settings', methods=['GET'])
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

@app.route('/api/calculate-zone', methods=['POST'])
def calculate_zone():
    try:
        data = request.get_json()
        average_hr = data.get('average_hr')

        # Load saved settings from file
        settings = get_settings_from_file()

        if not settings:
            return jsonify({"error": "Settings not found"}), 400

        max_hr = settings['maxHR']
        saved_zones = settings['zones']

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

        # Determine which zone the heart rate falls into
        for zone_num, zone_data in saved_zones.items():
            min_hr = (zone_data['min'] / 100) * max_hr
            max_hr_zone = (zone_data['max'] / 100) * max_hr
            if min_hr <= average_hr <= max_hr_zone:
                return jsonify({
                    "zone": f"Zone {zone_num}",
                    "name": zone_data['name']
                }), 200

        # If no zone matches, return "Unknown Zone"
        return jsonify({
            "zone": "Unknown Zone",
            "name": None
        }), 200
    except Exception as e:
        print(f"Error in calculate_zone: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)