# app/__init__.py

from flask import Flask
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth


def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_secret_key'  # Replace with your own secret key
    app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'

    CLIENT_ID = '89069cde77394ef99b8e87b43447e409'
    CLIENT_SECRET = '1c98e5f5b07140e1acfe94c9105bbe12'
    REDIRECT_URI = 'http://localhost:5000/callback'

    # Instantiate spotipy and authenticate (for Melinda Hubbard AKA Mom)
    sp_oauth = SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope='user-library-read'
    )

    app.sp_oauth = sp_oauth

    with app.app_context():
        from . import routes
        return app
