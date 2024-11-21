import os

from flask import Flask
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY = 'your_secret_key',  # Replace with secure secret key
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite')
        )
    
    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)    
    app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # # Spotify authentication details
    # CLIENT_ID = '89069cde77394ef99b8e87b43447e409'
    # CLIENT_SECRET = '1c98e5f5b07140e1acfe94c9105bbe12'
    # REDIRECT_URI = 'http://localhost:5000/callback'

    # # Instantiate spotipy and authenticate (for Melinda Hubbard AKA Mom)
    # sp_oauth = SpotifyOAuth(
    #     client_id=CLIENT_ID,
    #     client_secret=CLIENT_SECRET,
    #     redirect_uri=REDIRECT_URI,
    #     scope='user-library-read',
    #     cache_path=None
    # )

    #app.sp_oauth = sp_oauth

    with app.app_context():
        from . import routes

        from . import db
        db.init_app(app)

        from . import auth
        app.register_blueprint(auth.bp)

        return app
