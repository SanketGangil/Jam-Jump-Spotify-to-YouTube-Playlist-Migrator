from flask import Flask, session
from flask_session import Session
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Server-side Session
    Session(app)

    # Register Blueprints
    from app.spotify.routes import spotify_bp
    from app.youtube.routes import youtube_bp
    
    app.register_blueprint(spotify_bp, url_prefix='/spotify')
    app.register_blueprint(youtube_bp, url_prefix='/youtube')

    # Home Route
    @app.route('/')
    def index():
        html = "<h1>Jam Jump</h1>"
        
        # Check Spotify Status
        if 'spotify_token' in session:
            html += "<p style='color:green'>Spotify Connected!</p>"
        else:
            html += "<p><a href='/spotify/login'>Login to Spotify</a></p>"

        # Check YouTube Status (Placeholder for Phase 3)
        # Check YouTube Status
        if 'youtube_token' in session:
            html += "<p style='color:green'>YouTube Connected!</p>"
        else:
            html += "<p><a href='/youtube/login'>Login to YouTube</a></p>"

        html += "<br><hr><br>"
        
        if 'spotify_token' in session and 'youtube_token' in session:
            html += "<h3>Ready to go!</h3>"
            html += "<p><a href='/spotify/playlists'><button style='padding:10px; font-size:16px;'>View My Playlists</button></a></p>"
        else:
            html += "<p>Please connect both services to start migrating.</p>"

        return html

    return app 