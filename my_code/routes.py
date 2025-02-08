from flask import current_app as app
from flask import Flask, session, redirect, url_for, request, render_template, flash, jsonify
from spotipy import Spotify
import random
from .auth import get_spotify_oauth, login_required
import ast

# Below code was used to refresh expired tokens, leaving this commented out until I fix user authentication bugs

@app.before_request
def refresh_token():
    
    if 'token_info' in session:
        token_info = session['token_info']
        sp_oauth = get_spotify_oauth()
        if sp_oauth.is_token_expired(token_info):  # Check if the token is expired
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info  # Update the session with the new token


@login_required
@app.route('/', methods=('GET', 'POST'))
def home():
        
    session['source'] = None

    # Anything involving user input from the home page goes here
    if request.method == 'POST':
        selected_game_length = request.form.get('question_Number')
        #Assign values at the start of game based on the home page selection
        session['source'] = request.form.get('source')
        session['selectedSource'] = request.form.get('selectedSource')

        if selected_game_length: # Check to make sure the user selected a game mode
            session['game_length'] = int(selected_game_length) # Store the selected option in session
            session['question'] = 0
            session['score'] = 0
            return redirect(url_for('game_cards'))
        else:
            flash('You must select one option')
            return redirect(url_for('home'))
        
    return render_template('home.html')


#Game_cards route - render game_cards.html + retrieve songs from database and display round options
@app.route('/game_cards', methods=['GET','POST'])
def game_cards():

    # If the user is playing with their own library, make sure they are logged in
    if session['source'] == 'myLibrary' and 'token_info' not in session:
        return redirect(url_for('auth.login'))

    #Initiate the results variables
    if 'result' not in session:
        session['result'] = ''
        session['feedback'] = ''
        album = ''

    # This block of code executes when the user clicks an answer. It increments session['question'] and session['score'] if correct, then calls the get again
    # If session['question'] exceeds the user-set session['game_length'] it instead redirects to grade page
    if request.method == 'POST':
        selected_track = request.form.get('selected_track')
        print(selected_track)
        selected_track = ast.literal_eval(selected_track)
        most_popular = session.get('most_popular')
        choices = session.get('song_choices')
        correct = selected_track == most_popular
        session['question'] += 1
        session['feedback'] = choices[0]['name'] + ' popularity: '  + str(choices[0]['popularity']) + '. ' + choices[1]['name'] + ' popularity: '  + str(choices[1]['popularity'])
        if correct:
            session['score']  +=1
            session['result'] = 'Correct! '
        else:
            session['result'] = 'Incorect. '
        

        if session['question'] == session['game_length']:
            return  redirect(url_for('grade'))
        print(type(selected_track))
        return jsonify({
            'user_choice': selected_track,
            'is_correct': correct,
            'correct_song': most_popular,
            'correct_popularity': most_popular['popularity'],
            'user_choice_popularity': selected_track['popularity'],
            'score': session['score']
        })


    token_info = session.get('token_info')
    sp = Spotify(auth=token_info['access_token'])


    # Get tracks from user spotify library or spotify public playslist
    saved_tracks = []
    index = 0
    playlist_id = ''
    if session['source'] == 'myLibrary':
        results = sp.current_user_saved_tracks(limit=50, offset=index)
        if len(results['items']):
            saved_tracks.extend(results['items'])
            index += 50
    else:
        match session['selectedSource']:
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
                'name': name,
                'uri': uri,
                'popularity': popularity,
                'artists': artist_names_str,
                'album':album
              
            }
        choices.append(choice)


    # Find the more popular track. If tracks are tied, reload page and regenerate choices.
    print(choices[1])
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


