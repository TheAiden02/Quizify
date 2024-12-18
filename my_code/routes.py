from flask import current_app as app
from flask import Flask, session, redirect, url_for, request, render_template, flash
from spotipy import Spotify
import random
from .auth import get_spotify_oauth, login_required

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
    if not 'score' in session:
        session['score'] = 0
        
    question_Number = 0
    # Check if the user is already authenticated
    if 'token_info' not in session:
        return redirect(url_for('auth.login')) 

    token_info = session.get('token_info')
    sp = Spotify(auth=token_info['access_token'])
        
    print(session)
    if request.method == 'POST':
        return redirect(url_for('game_cards'))
    return render_template('home.html')
    #return render_template('home.html', question_Number=question_Number)


#Game_cards route - render game_cards.html + retrieve songs from database and display round options
@app.route('/game_cards', methods=['GET','POST'])
def game_cards():
    
    if request.method =='POST':
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

        choices = []
        for item in items:
            name = item['track']['name']
            uri = item['track']['uri']
            popularity = item['track']['popularity']
            artists = item['track']['artists']
            artist_names = [artist['name'] for artist in artists]
            artist_names_str = ', '.join(artist_names)

            choice = {
                    'name': name,
                    'uri': uri,
                    'popularity': popularity,
                    'artists': artist_names_str
                }
            choices.append(choice)


        # Find the more popular track. If tracks are tied, reload page and regenerate choices.
        most_popular = choices[0]
        if choices[1]['popularity'] > most_popular['popularity']:
            most_popular = choices[1]
        elif choices[1]['popularity'] == most_popular['popularity']:
            return redirect(url_for('home'))
        
        # Count how many question played
        session['question'] +=1
        question = session['question']
        

        session['song_choices'] = choices
        session['most_popular'] = most_popular['name']
        selected_option = request.form.get('question_Number')
        if question_Number:
            # Store the selected option in session
            session['question_Number'] = question_Number
    
        print(session)

    print(choices)
    return render_template('game_cards.html', choices=choices, question=question, question_Number=question_Number)



#Grade Route - Render grade.html page + scoring logic 
#To add - game mode logic that tracks how many questions are selected to be played(on home) + end game when appropriate
@app.route('/grade', methods=['POST'])
def grade():
    selected_track = request.form.get('selected_track')
    most_popular = session.get('most_popular')
    choices = session.get('song_choices')
    correct = selected_track == most_popular
    if selected_track := correct:
       session['score']  +=1
       print(session['score'])
        

    return render_template('grade.html', correct=correct, choices=choices, score=session['score'])



@app.route('/callback')
def callback():
    sp_oauth = get_spotify_oauth()
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session['token_info'] = token_info
    session['question'] = session.get('question', -1)  #define question counter
    session['question_Number'] = session.get('question_Number', -1)  #Set number of questions -- infiate mode to come

    return redirect(url_for('home'))


