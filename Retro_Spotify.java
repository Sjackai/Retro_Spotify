from flask import Flask, request, redirect, url_for, session #core class we use
# to create our web application instance.
import spotipy #This object allows us to access incoming data from web requests
from spotipy.oauth2 import SpotifyOAuth #Specifically handles
# the OAuth 2.0 authorization process
import os #Access environment variables where we would securely store
# sensitive information like our Spotify Client ID and Client Secret


app = Flask(__name__)
app.secret_key = os.urandom(24)  # Important for session management

CLIENT_ID = 'f718b7c2d14940e4a7e2882b28ac293d'  # Replace with your Client ID
CLIENT_SECRET = '58eeae9440fc4261a39893fcb6681984'  # Replace with your Client Secret
REDIRECT_URI = 'http://localhost:8888/callback' # Ensure this matches your Spotify app settings
SCOPE = 'user-modify-playback-state user-read-playback-state user-library-read'

def create_spotify_oauth():
    return SpotifyOAuth(client_id=CLIENT_ID,
                        client_secret=CLIENT_SECRET,
                        redirect_uri=REDIRECT_URI,
                        scope=SCOPE)

@app.route('/')
def index():
    if 'token_info' in session:
        sp = spotipy.Spotify(auth_manager=create_spotify_oauth())
        current_playback = sp.current_playback()
        track_name = current_playback['item']['name'] if current_playback and current_playback['item'] else "No track playing"
        return f"Logged in as {sp.me()['display_name']}. Currently playing: {track_name} <br><a href='/logout'>Logout</a> <br><a href='/play_retro'>Play Retro Music</a>"
    else:
        return '<a href="/login">Login to Spotify</a>'

@app.route('/login')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    sp_oauth = create_spotify_oauth()
    code = request.args.get('code')
    if code:
        token_info = sp_oauth.get_access_token(code)
        session['token_info'] = token_info
        return redirect(url_for('index'))
    return 'Failed to get authorization code'

@app.route('/logout')
def logout():
    session.pop('token_info', None)
    return redirect(url_for('index'))

@app.route('/play_retro')
def play_retro():
    if 'token_info' in session:
        sp = spotipy.Spotify(auth_manager=create_spotify_oauth())
        # Example: Search for a retro gaming playlist and play the first one found
        results = sp.search(q='retro gaming music', type='playlist', limit=1)
        if results and results['playlists']['items']:
            playlist_uri = results['playlists']['items'][0]['uri']
            sp.start_playback(context_uri=playlist_uri)
            return redirect(url_for('index'))
        else:
            return "Could not find a retro gaming playlist."
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=8888)
