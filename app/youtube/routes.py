from flask import Blueprint, redirect, request, session, url_for, current_app, flash
import google_auth_oauthlib.flow
import googleapiclient.discovery
import google.oauth2.credentials
from google.auth.exceptions import RefreshError
from googleapiclient.errors import HttpError
import requests
import os
import json

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
        scopes=["https://www.googleapis.com/auth/youtube.force-ssl"]
    )
    
    flow.redirect_uri = current_app.config['GOOGLE_REDIRECT_URI']
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    session['state'] = state
    return redirect(authorization_url)

@youtube_bp.route('/callback')
def callback():
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

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['youtube_token'] = credentials_to_dict(credentials)

    return redirect(url_for('index'))

@youtube_bp.route('/migrate', methods=['POST'])
def migrate_playlist():
    """
    Step 4: The Core Logic. 
    """
    if 'youtube_token' not in session or 'spotify_token' not in session:
        return redirect(url_for('index'))

    # 1. Get Data from Form (Using Flask's 'request')
    spotify_playlist_id = request.form.get('spotify_playlist_id')
    playlist_name = request.form.get('playlist_name')
    
    # 2. Setup Clients
    spotify_headers = {'Authorization': f"Bearer {session['spotify_token']}"}
    
    credentials = google.oauth2.credentials.Credentials(**session['youtube_token'])
    youtube = googleapiclient.discovery.build('youtube', 'v3', credentials=credentials)

    # 3. Check Token Validity (Renamed variable to avoid conflict)
    try:
        # Changed 'request' to 'test_req' to avoid conflict with Flask global 'request'
        test_req = youtube.channels().list(part="id", mine=True)
        test_req.execute()
    except HttpError as e:
        if e.resp.status == 401:
            # Token Expired -> Clear session and force re-login
            session.pop('youtube_token', None)
            return redirect(url_for('youtube.login'))
        else:
            return f"YouTube API Error: {e}"

    # 4. Fetch Spotify Tracks
    spotify_url = f"https://api.spotify.com/v1/playlists/{spotify_playlist_id}/tracks?limit=50"
    resp = requests.get(spotify_url, headers=spotify_headers)
    
    if resp.status_code != 200:
        return f"Spotify Error: {resp.text}"
        
    tracks = resp.json().get('items', [])

    # 5. Create New YouTube Playlist
    try:
        playlist_response = youtube.playlists().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": f"{playlist_name} (Imported)",
                    "description": "Migrated from Spotify via Flask App"
                },
                "status": {
                    "privacyStatus": "private" 
                }
            }
        ).execute()
        
        new_playlist_id = playlist_response['id']
    except Exception as e:
        return f"YouTube Creation Error: {str(e)}"

    # 6. Search and Add Videos
    success_count = 0
    
    for item in tracks:
        track = item['track']
        if not track: continue 
        
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
            continue 
            
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

    return f"<h1>Migration Complete!</h1><p>Successfully moved {success_count} songs to YouTube.</p><a href='/'>Go Home</a>"