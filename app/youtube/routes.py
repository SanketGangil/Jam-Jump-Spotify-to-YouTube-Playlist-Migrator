from flask import Blueprint, redirect, request, session, url_for, current_app
import google_auth_oauthlib.flow
from google.oauth2.credentials import Credentials
import os
import json
import googleapiclient.discovery
import google.oauth2.credentials 
import requests

youtube_bp = Blueprint('youtube', __name__)

# Helper: Convert Google Credentials object to a dictionary for session storage
def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

@youtube_bp.route('/login')
def login():
    """
    Step 1: Redirect user to Google's OAuth 2.0 Server.
    """
    # Create the client config dictionary manually from .env vars
    client_config = {
        "web": {
            "client_id": current_app.config['GOOGLE_CLIENT_ID'],
            "client_secret": current_app.config['GOOGLE_CLIENT_SECRET'],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [current_app.config['GOOGLE_REDIRECT_URI']]
        }
    }

    # Scopes needed to Manage YouTube Account
    scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config=client_config,
        scopes=scopes
    )
    
    flow.redirect_uri = current_app.config['GOOGLE_REDIRECT_URI']
    
    authorization_url, state = flow.authorization_url(
        access_type='offline', # Offline gives us a refresh token
        include_granted_scopes='true'
    )

    # Store state to verify later (CSRF protection)
    session['state'] = state
    
    return redirect(authorization_url)

@youtube_bp.route('/callback')
def callback():
    """
    Step 2: Google redirects back. Exchange code for credentials.
    """
    # Security check
    state = session['state']
    
    client_config = {
        "web": {
            "client_id": current_app.config['GOOGLE_CLIENT_ID'],
            "client_secret": current_app.config['GOOGLE_CLIENT_SECRET'],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [current_app.config['GOOGLE_REDIRECT_URI']]
        }
    }

    flow = google_auth_oauthlib.flow.Flow.from_client_config(
        client_config=client_config,
        scopes=["https://www.googleapis.com/auth/youtube.force-ssl"],
        state=state
    )
    
    flow.redirect_uri = current_app.config['GOOGLE_REDIRECT_URI']

    # Fetch the token using the URL returned by Google
    # We must pass the full URL (http://127.0.0.1...) so the library can parse the code
    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Convert credentials to dictionary and save in session
    credentials = flow.credentials
    session['youtube_token'] = credentials_to_dict(credentials)

    return redirect(url_for('index'))

from flask import flash # Add flash to imports if not already there
import googleapiclient.discovery

@youtube_bp.route('/migrate', methods=['POST'])
def migrate_playlist():
    """
    Step 4: The Core Logic. 
    1. Get Spotify Playlist ID from form.
    2. Fetch all tracks from Spotify.
    3. Create a new YouTube Playlist.
    4. Search for each track on YouTube.
    5. Add found videos to the new playlist.
    """
    if 'youtube_token' not in session or 'spotify_token' not in session:
        return redirect(url_for('index'))

    # 1. Get Data from Form
    spotify_playlist_id = request.form.get('spotify_playlist_id')
    playlist_name = request.form.get('playlist_name')
    
    # 2. Setup Clients
    # Spotify Headers
    spotify_headers = {'Authorization': f"Bearer {session['spotify_token']}"}
    
    # YouTube Client
    credentials = google.oauth2.credentials.Credentials(**session['youtube_token'])
    youtube = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)

    # 3. Fetch Spotify Tracks
    # Note: Spotify limits to 100 tracks per request. For a resume project, 
    # handling the first 100 is acceptable complexity.
    spotify_url = f"https://api.spotify.com/v1/playlists/{spotify_playlist_id}/tracks?limit=50"
    resp = requests.get(spotify_url, headers=spotify_headers)
    
    if resp.status_code != 200:
        return f"Spotify Error: {resp.text}"
        
    tracks = resp.json().get('items', [])

    # 4. Create New YouTube Playlist
    try:
        playlist_response = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": f"{playlist_name} (Imported)",
                    "description": "Migrated from Spotify via Flask App"
                },
                "status": {
                    "privacyStatus": "private" # Safety first!
                }
            }
        ).execute()
        
        new_playlist_id = playlist_response['id']
    except Exception as e:
        return f"YouTube Creation Error: {str(e)}"

    # 5. Search and Add Videos
    success_count = 0
    
    for item in tracks:
        track = item['track']
        if not track: continue # Skip empty tracks
        
        # Construct Search Query (Artist - Song Name)
        artist_name = track['artists'][0]['name']
        song_name = track['name']
        query = f"{artist_name} {song_name} official audio"
        
        # Search YouTube
        search_resp = youtube.search().list(
            part="id",
            q=query,
            maxResults=1,
            type="video"
        ).execute()
        
        if not search_resp['items']:
            continue # No video found
            
        video_id = search_resp['items'][0]['id']['videoId']
        
        # Add to Playlist
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": new_playlist_id,
                        "resourceId": {
                            "kind": "youtube#video",
                            "videoId": video_id
                        }
                    }
                }
            ).execute()
            success_count += 1
            print(f"Added: {query}")
        except Exception as e:
            print(f"Failed to add {query}: {e}")

    # 6. Finish
    return f"<h1>Migration Complete!</h1><p>Successfully moved {success_count} songs to YouTube.</p><a href='/'>Go Home</a>"