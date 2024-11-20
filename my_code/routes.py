from flask import current_app as app
from flask import Flask, session, redirect, url_for, request, render_template
from spotipy import Spotify
import random


@app.before_request
def refresh_token():
    if 'token_info' in session:
        token_info = session['token_info']
        if app.sp_oauth.is_token_expired(token_info):  # Check if the token is expired
            token_info = app.sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info  # Update the session with the new token


@app.route('/')
def home():
        # Check if the user is already authenticated
    if 'token_info' not in session:
        return render_template('login.html')  # Show a "Login with Spotify" button

    token_info = session.get('token_info')
    sp = Spotify(auth=token_info['access_token'])

    # Get current user's saved tracks
    saved_tracks = []
    index = 0
    while True:
        results = sp.current_user_saved_tracks(limit=50, offset=index)

        if len(results['items']):
            saved_tracks.extend(results['items'])
            index += 50
        else:
            break

    # Randomly select two tracks from user's saved tracks
    items = random.sample(saved_tracks, 2)
    choices = [
        {
            'name': item['track']['name'],
            'uri': item['track']['uri'],
            'popularity': item['track']['popularity']
        }
        for item in items
    ]

    # Find the more popular track. If tracks are tied, reload page and regenerate choices.
    most_popular = choices[0]
    if choices[1]['popularity'] > most_popular['popularity']:
        most_popular = choices[1]
    elif choices[1]['popularity'] == most_popular['popularity']:
        return redirect(url_for('home'))
    
    session['song_choices'] = choices
    session['most_popular'] = most_popular['name']

    return render_template('home.html', choices=choices)

@app.route('/grade', methods=['POST'])
def grade():
    selected_track = request.form.get('selected_track')
    most_popular = session.get('most_popular')
    choices = session.get('song_choices')
    correct = selected_track == most_popular
    return render_template('grade.html', correct=correct, choices=choices)


@app.route('/login')
def login():
    auth_url = app.sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = app.sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    return redirect(url_for('home'))

