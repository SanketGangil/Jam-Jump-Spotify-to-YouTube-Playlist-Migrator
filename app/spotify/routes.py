from flask import Blueprint, redirect, request, session, url_for, current_app, render_template
import requests
import urllib.parse
import os

spotify_bp = Blueprint('spotify', __name__)

@spotify_bp.route('/login')
def login():
    """
    Step 1: Redirect user to Spotify's Authorization Page.
    """
    # Scopes needed: read private playlists, read public playlists
    scope = "playlist-read-private playlist-read-collaborative"
    
    params = {
        'client_id': current_app.config['SPOTIFY_CLIENT_ID'],
        'response_type': 'code',
        'redirect_uri': current_app.config['SPOTIFY_REDIRECT_URI'],
        'scope': scope,
        'show_dialog': 'true' # Force login screen (good for testing)
    }
    
    auth_url = f"https://accounts.spotify.com/authorize?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@spotify_bp.route('/callback')
def callback():
    """
    Step 2: Spotify redirects back here with a 'code'.
    We exchange that code for an Access Token.
    """
    if 'error' in request.args:
        return f"Error: {request.args['error']}"
    
    if 'code' not in request.args:
        return "Error: No code received from Spotify"

    # Exchange Authorization Code for Access Token
    req_body = {
        'code': request.args['code'],
        'grant_type': 'authorization_code',
        'redirect_uri': current_app.config['SPOTIFY_REDIRECT_URI'],
        'client_id': current_app.config['SPOTIFY_CLIENT_ID'],
        'client_secret': current_app.config['SPOTIFY_CLIENT_SECRET']
    }

    response = requests.post('https://accounts.spotify.com/api/token', data=req_body)
    token_info = response.json()

    if 'access_token' not in token_info:
        return f"Failed to get token: {token_info}"

    # Save token in Server-Side Session
    session['spotify_token'] = token_info['access_token']
    
    # Optional: Save refresh token if you want to support long usage
    # session['spotify_refresh_token'] = token_info.get('refresh_token')

    return redirect(url_for('index'))

@spotify_bp.route('/playlists')
def get_playlists():
    """
    Step 3: Fetch user's playlists and render the dashboard.
    """
    if 'spotify_token' not in session:
        return redirect(url_for('spotify.login'))

    headers = {
        'Authorization': f"Bearer {session['spotify_token']}"
    }

    # API Endpoint to get current user's playlists
    response = requests.get('https://api.spotify.com/v1/me/playlists', headers=headers)
    
    if response.status_code == 401:
        # found a bug error 401
        # 401 means "Unauthorized" (Token Expired)
        # Clear the old token and force a re-login
        session.pop('spotify_token', None)
        return redirect(url_for('spotify.login'))

    if response.status_code != 200:
        return f"Error fetching playlists: {response.text}"

    playlists = response.json().get('items', [])
    
    return render_template('dashboard.html', playlists=playlists)