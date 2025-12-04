# Jam Jump : Spotify to YouTube Playlist Migrator 

A secure, full-stack Flask application that automates the migration of playlists from Spotify to YouTube. This project demonstrates OAuth 2.0 integration, third-party API consumption (Spotify Web API & YouTube Data API v3), and modular backend architecture.

## Features

* **Secure Authentication**: Implements OAuth 2.0 Authorization Code flow for both Spotify and Google/YouTube.
* **Session Management**: Uses server-side sessions (`Flask-Session`) to securely handle access tokens without exposing them to the client.
* **Smart Migration**:
    * Fetches tracks from a selected Spotify playlist.
    * Creates a corresponding private playlist on YouTube.
    * Automatically searches for the official audio/video on YouTube.
    * Adds found videos to the new playlist.
* **Modular Architecture**: Built using Flask Blueprints to separate authentication logic (`auth`), API interaction, and core application routes.

## Tech Stack

* **Language**: Python 3.x
* **Backend Framework**: Flask
* **APIs**:
    * [Spotify Web API](https://developer.spotify.com/documentation/web-api/) (via `requests`)
    * [YouTube Data API v3](https://developers.google.com/youtube/v3) (via `google-api-python-client`)
* **Authentication**: OAuth 2.0 (`google-auth-oauthlib`)
* **Data Handling**: Flask-Session (Server-side session storage)
* **Frontend**: HTML5, CSS3 (Jinja2 Templates)

## Project Structure

```bash
spotify-youtube-migrator/
├── app/
│   ├── __init__.py       # App Factory & Configuration
│   ├── templates/        # HTML Jinja2 Templates
│   ├── static/           # CSS Assets
│   ├── spotify/          # Spotify Blueprint (Auth & Fetching)
│   └── youtube/          # YouTube Blueprint (Auth & Migration Logic)
├── config.py             # Environment Configuration
├── requirements.txt      # Python Dependencies
├── run.py                # Application Entry Point
└── .env                  # API Keys (Not included in repo)

## Setup & Installation
1. **Prerequisites**:
    * Python 3.8+ installed.
    * A Spotify Developer Account.
    * A Google Cloud Project with YouTube Data API v3 enabled.

2. **Clone the Repository**

3. **Install Dependencies**
    * It is recommended to use a virtual environment.
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

4. **Configure Environment Variables**
* Create a `.env` file in the root directory and add your credentials:
```bash
# Flask Settings
SECRET_KEY=your_random_secret_string
FLASK_APP=run.py
FLASK_ENV=development

# Spotify API
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=[http://127.0.0.1:5000/spotify/callback](http://127.0.0.1:5000/spotify/callback)

# Google/YouTube API
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=[http://127.0.0.1:5000/youtube/callback](http://127.0.0.1:5000/youtube/callback)

# OAuth Security (For Local Development Only)
OAUTHLIB_INSECURE_TRANSPORT=1

5. **Run the Application**
```bash
python run.py

6. Access the application at `http://127.0.0.1:5000`.

## Future Improvements
* **Reverse Migration (YouTube to Spotify)**: Add functionality to migrate YouTube playlists back to Spotify, completing the two-way sync ecosystem.
* **Progress Bar**: Add a real-time progress bar (via WebSocket) to show the user which song is currently being migrated.
* **Duplicate Detection**: Implement logic to check if a song already exists in the target playlist to prevent duplicates.
* **Cloud Deployment**: Configure the app for deployment on cloud platforms like Render, Heroku, or AWS (requires updating Redirect URIs to HTTPS).
* **UI Enhancements**: Improve the frontend with a modern CSS framework like Tailwind or Bootstrap.

## Contributing
Contributions, issues, and feature requests are welcome!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request