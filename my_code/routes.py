from flask import current_app as app
from flask import Flask, session, redirect, url_for, request, render_template, flash, jsonify
from spotipy import Spotify, SpotifyException
import random
from .auth import get_spotify_oauth, login_required
from my_code.db import get_db
import ast
import json

# Below code was used to refresh expired tokens, leaving this commented out until I fix user authentication bugs

@app.before_request
def refresh_token():
    
    if 'token_info' in session:
        token_info = session['token_info']
        sp_oauth = get_spotify_oauth()
        if sp_oauth.is_token_expired(token_info):  # Check if the token is expired
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info  # Update the session with the new token

@app.route('/', methods=['GET', 'POST'])
def home():
        
    session['source'] = None

    # Anything involving user input from the home page goes here
    if request.method == 'POST':
        selected_game_length = request.form.get('question_Number')
        #Assign values at the start of game based on the home page selection
        session['source'] = request.form.get('source') # The user's choice of their own playlists or the built-in public playlists
        session['selected_source'] = request.form.get('selectedSource') # The specific chosen playlist

        if selected_game_length: # Check to make sure the user selected a game mode
            session['game_length'] = int(selected_game_length) # Store the selected option in session
            session['question'] = 1
            session['score'] = 0
            return redirect(url_for('game_cards'))
        else:
            flash('You must select one option')
            return redirect(url_for('home'))
        
    user_playlists = []
    current_user = session.get('user_id')

    if current_user is not None:
        db = get_db()
        user_playlists = db.execute(
            'SELECT * FROM user_playlists WHERE user_id = ?', (session['user_id'],)
        ).fetchall()

    user_playlists = [ dict(row) for row in user_playlists ] # Convert each sqlite3.row into a json serializable dictionary so javascript can handle it
        
    return render_template('home.html', playlists = user_playlists)

@app.route('/home/get_select', methods=['POST'])
def get_select():
    source = request.form.get('source')

    return redirect(url_for('home'))


#Game_cards route - render game_cards.html + retrieve songs from database and display round options
@app.route('/game_cards', methods=['GET','POST'])
def game_cards():

    # If the user is playing with their own library, make sure they are logged in
    if session['source'] == 'my_playlists' and 'token_info' not in session:
        return redirect(url_for('auth.login'))

    #Initiate the results variables
    if 'result' not in session:
        session['result'] = ''
        session['feedback'] = ''
        album = ''

    # This block of code executes when the user clicks an answer. It increments question number, score if correct, and sends data to the client for displaying the result.
    if request.method == 'POST':
        selected_track = request.form.get('selected_track')
        selected_track = ast.literal_eval(selected_track)
        most_popular = session.get('most_popular')
        most_popular_uri = most_popular.get('uri')
        choices = session.get('song_choices')
        correct = selected_track['uri'] == most_popular_uri
        session['question'] += 1
        session['feedback'] = choices[0]['name'] + ' popularity: '  + str(choices[0]['popularity']) + '. ' + choices[1]['name'] + ' popularity: '  + str(choices[1]['popularity'])
        last_question = session['question'] == session['game_length'] + 1
        if correct:
            session['score']  += 1
            session['result'] = 'Correct! '
        else:
            session['result'] = 'Incorect. '
        
        return jsonify({
            'user_choice': selected_track,
            'is_correct': correct,
            'correct_song': most_popular_uri,
            'correct_popularity': most_popular['popularity'],
            'user_choice_popularity': selected_track['popularity'],
            'score': session['score'],
            'last_question': last_question
        })




    # Get tracks from user spotify library or spotify public playslist
    saved_tracks = []
    index = 0
    playlist_id = ''
    if session['source'] == 'my_playlists':
        # get access token for logged-in user
        token_info = session.get('token_info')
        sp = Spotify(auth=token_info['access_token'])

        # get the current user's playlists
        db = get_db()
        user_playlist_urls = db.execute(
            'SELECT playlist_url FROM user_playlists WHERE user_id = ?', (session.get('user_id'),)
        ).fetchall()

        if session['selected_source'] == 'my_library':
            results = sp.current_user_saved_tracks(limit=50, offset=index)
            if len(results['items']):
                saved_tracks.extend(results['items'])
                index += 50
        else:
            print(session['selected_source'])
            results = sp.playlist_items(session['selected_source'])
            if len(results['items']):
                saved_tracks.extend(results['items'])
                index += 50


    else:
        # get non-user-specific access token with client credentials flow
        auth_manager = get_spotify_oauth('cli')
        sp = Spotify(auth_manager=auth_manager)
        
        match session['selected_source']:
            case 'classicRock':
                playlist_id = '1ti3v0lLrJ4KhSTuxt4loZ'
            case 'pop':
                playlist_id = '6mtYuOxzl58vSGnEDtZ9uB'
            case 'indie':
                playlist_id = '30QV4edB1roGt1FnTNxqy1'
            case 'rap':
                playlist_id = '01MRi9jFGeSEEttKOk7VgR'
            case 'showtunes':
                playlist_id = '4717W6DDMFngWIaJGjDV5r'
            case 'country':
                playlist_id = '02t75h5hsNOw4VlC1Qad9Z'
            case 'classical':
                playlist_id = '27Zm1P410dPfedsdoO9fqm'
        results = sp.playlist_tracks(playlist_id)
        print(type(results))
        if len(results['items']):
            saved_tracks.extend(results['items'])
            index += 50

    # Randomly select two tracks from user's saved tracks
    items = random.sample(saved_tracks, 2)

    choices = []
    for item in items:
        name = item['track']['name']
        uri = item['track']['uri']
        popularity = item['track']['popularity']
        artists = item['track']['artists']
        artist_names = [artist['name'] for artist in artists]
        artist_names_str = ', '.join(artist_names)
        album = item['track']['album']
        images = {
            'url': item['track']['album']['images'][0]['url'],
            'height': 300,
            'width': 300
        }

   
        choice = {
                "name": name,
                "uri": uri,
                "popularity": popularity,
                "artists": artist_names_str,
                "album":album
            }
        choices.append(choice)


    # Find the more popular track. If tracks are tied, reload page and regenerate choices.
    most_popular = choices[0]
    if choices[1]['popularity'] > most_popular['popularity']:
        most_popular = choices[1]
    elif choices[1]['popularity'] == most_popular['popularity']:
        return redirect(url_for('home'))
    
    question = session['question']

    session['song_choices'] = choices
    session['most_popular'] = most_popular



    return render_template('game_cards.html', source=session['source'], choices=choices, question=question, game_length=session['game_length'], result=session['result'], feedback=session['feedback'], reveal=False)

@app.route('/game_cards_answers')
def game_cards_answers(source, choices, question, game_length, result, feedback):
    return render_template('game_cards.html', source=source, choices=choices, question=question, game_length=game_length, result=result, feedback=feedback, reveal=True)

#Grade Route - Display final score after user has completed the game
@app.route('/grade', methods=['GET','POST'])
def grade():
    if request.method == 'POST':
        return redirect(url_for('home'))
    correct = session['score']
    total = session['game_length']
    return render_template('grade.html', correct=correct, total=total)

# This route is for loading the profile page. It grabs all of the playlists associated with the current user from the database and sends them as a list of SQL rows to the frontend
@app.route('/profile')
def profile():
    playlists = []
    playlist_names = []
    playlist_urls = []
    db = get_db()
    user_id = session.get('user_id')
    print(type(user_id))
    playlists = db.execute(
        'SELECT * FROM user_playlists WHERE user_id=?', (user_id,)
    ).fetchall()

    return render_template('profile.html', playlists = playlists)

# Route for adding playlists to the user_playlist table of the database. Gets a spotify url from the frontend, sends it to Spotify to get the playlist, and adds the playlist data to the database.
@app.route('/profile/add_playlist', methods=['POST'])
def add_playlist():
    if "user_id" not in session:
        return redirect(url_for('login'))
    response = {}
    playlist_url = request.form.get('playlist_url')
    db = get_db()

    token_info = session.get('token_info')
    sp = Spotify(auth=token_info['access_token'])

    try:
        response = sp.playlist(playlist_url)
        playlist_name = response["name"]
    except SpotifyException as e: 
        match str(e.http_status):
            case "400":
                error_msg = "Error 400: bad request. Make sure to input a valid Spotify URL."
            case "404":
                error_msg = "Error 404: playlist not found. Make sure that the URL is correct and the playlist was not created by Spotify."
            case _:
                error_msg = f"Error {e.http_status}. Double check your URL and try again."
        flash(error_msg)
        return redirect(url_for('profile'))
    except:
        flash("Some error occurred. Wish I could tell you more lol sorry")

    print(playlist_name)
    
    if response:
        try:
            db.execute(
                "INSERT INTO user_playlists (user_id, playlist_name, playlist_url) VALUES (?, ?, ?)",
                (
                    session['user_id'],
                    playlist_name,
                    playlist_url
                ),
            )
            db.commit()
        except db.IntegrityError:
            error = f"Playlist {playlist_name} is already added."
            print(error)
        except db.Error:
            print(f"error {db.Error.sqlite_errorcode}: {db.Error.sqlite_errorname}")
        except:
            print("An unkown error occurred when trying to insert playlist")

    return redirect(url_for('profile'))

# Removes playlists from the user_playlists table of the database
@app.route('/profile/remove_playlist', methods=['POST'])
def remove_playlist():
    db = get_db()
    playlist_name = request.form.get('playlist_name')
    user_id = session['user_id']
    print(f"user_id: {user_id}, playlist_name: {playlist_name}")
    try:
        db.execute(
            "DELETE FROM user_playlists WHERE user_id = ? and playlist_name = ?", (user_id, playlist_name)
        )
        print("delete went through")
    except:
        print("error")
    db.commit()

    return redirect(url_for('profile'))

# Spotify sends authentication data here after user logs into spotify
@app.route('/callback')
def callback():
    sp_oauth = get_spotify_oauth()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info

    # If the user got here by clicking start game, session['source'] has been initialized and they should be sent to game_cards to start playing
    if session['source'] != None:
        return redirect(url_for('game_cards'))
    else: # If the user got here by clicking login from the home page, they should be sent back to the home page where they can set up their game.
        return redirect(url_for('home'))


