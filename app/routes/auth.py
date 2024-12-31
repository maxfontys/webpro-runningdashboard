from flask import Flask, redirect, request, session, render_template, jsonify, Blueprint
import requests
import os
from dotenv import load_dotenv

auth_bp = Blueprint('auth', __name__)

# Get keys from the environment
load_dotenv()
CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
REDIRECT_URI = os.getenv('STRAVA_REDIRECT_URI')

# Route 1

@auth_bp.route('/login')
def login_strava():
    return redirect(f"https://www.strava.com/oauth/authorize"
                   f"?client_id={CLIENT_ID}"
                   f"&redirect_uri={REDIRECT_URI}"
                   f"&response_type=code"
                   f"&scope=read,activity:read"
                   f"&approval_prompt=force"
                   f"&prompt=consent")

# Route 2

@auth_bp.route('/logout')
def logout():
    if 'access_token' in session:
        requests.post("https://www.strava.com/oauth/deauthorize", 
                     data={'access_token': session['access_token']})
    
    session.clear()
    response = redirect('/')
    response.set_cookie('strava_auth', '', expires=0)  # Clear Strava cookies
    return response

# Route 3 

@auth_bp.route('/callback')
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