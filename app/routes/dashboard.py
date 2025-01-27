from flask import Blueprint, render_template
import requests
import json
import os
from datetime import datetime, timedelta, timezone
from flask import Flask, redirect, request, session, render_template, jsonify
from flask_cors import CORS
import time

from app.models.settings import get_settings_from_file

app = Flask(__name__)
CORS(app)

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
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

    settings = get_settings_from_file()
    if not settings:
        print("No saved settings found. Please configure zones in settings.")
        data["zone_focus"] = {
            "training_focus": "Zones not configured",
            "average_heart_rate": "N/A"
        }
        return data

    # Use saved settings
    max_hr = settings['maxHR']
    saved_zones = settings['zones']
    print(f"Using saved max HR: {max_hr}")

    # Calculate zones from saved settings
    zones = {}
    for zone_num, zone_data in saved_zones.items():
        min_hr = round((zone_data['min'] / 100) * max_hr)
        max_hr_zone = round(((zone_data['max'] + 0.999999) / 100) * max_hr)
        zones[f"Zone {zone_num}"] = (min_hr, max_hr_zone)
        print(f"Zone {zone_num}: {int(min_hr)}-{int(max_hr_zone)} bpm")

    # Calculate average heart rate from activities
    activity_averages = []
    for activity in weekly_activities:
        if 'average_heartrate' in activity:
            activity_averages.append(activity['average_heartrate'])

    average_heart_rate = int(sum(activity_averages) / len(activity_averages)) if activity_averages else 0
    print(f"Calculated average HR: {average_heart_rate}")
    print(f"Max HR: {max_hr}")

    # Determine zone based on average heart rate
    zone_focus = None
    for zone, (low, high) in zones.items():
        if low <= average_heart_rate <= high:
            zone_focus = zone
            print(f"Average HR {average_heart_rate} falls into {zone}")
            break

    # Define zone names mapping
    zone_names = {
        "Zone 1": "Recovery",
        "Zone 2": "Aerobic Endurance",
        "Zone 3": "Tempo",
        "Zone 4": "Threshold",
        "Zone 5": "VO2 Max"
    }

    zone_focus_display = f"{zone_focus}: {zone_names[zone_focus]}" if zone_focus else "Unknown Zone"
    print(f"Zone focus display: {zone_focus_display}")

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
    data["pace_trends_json"] = json.dumps(data["heart_rate_trends_by_pace"])  # Pre-dump JSON
    
    data["manifest"] = manifest  # Add manifest to your data dictionary
    return render_template('dashboard.html', data=data)