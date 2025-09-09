import pygame
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import webbrowser  # To open the auth URL

pygame.init()

# --- Screen, Colors, Paddle, Ball, Score (as before) ---
screen_width = 800
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Retro Pong with Spotify")
white = (255, 255, 255)
black = (0, 0, 0)
paddle_width = 10
paddle_height = 60
left_paddle_y = screen_height // 2 - paddle_height // 2
right_paddle_y = screen_height // 2 - paddle_height // 2
left_paddle_x = 50
right_paddle_x = screen_width - 50 - paddle_width
paddle_speed = 5
ball_radius = 10
ball_x = screen_width // 2
ball_y = screen_height // 2
ball_speed_x = 3
ball_speed_y = 3
left_score = 0
right_score = 0
font = pygame.font.Font(None, 74)
clock = pygame.time.Clock()
game_running = True

# --- Spotify Configuration ---
CLIENT_ID = 'f718b7c2d14940e4a7e2882b28ac293d'  # Replace with your Client ID
CLIENT_SECRET = '58eeae9440fc4261a39893fcb6681984'  # Replace with your Client Secret
REDIRECT_URI = 'http://localhost:8888/callback/pong'  # A new redirect URI for Pong
SCOPE = 'user-modify-playback-state user-read-playback-state user-library-read'
SPOTIFY_AUTH_URL = None
SPOTIPY_OAUTH = None
SPOTIFY_API = None
AUTHENTICATED = False

def create_spotify_oauth():
    global SPOTIPY_OAUTH, SPOTIFY_AUTH_URL
    SPOTIPY_OAUTH = SpotifyOAuth(client_id=CLIENT_ID,
                                 client_secret=CLIENT_SECRET,
                                 redirect_uri=REDIRECT_URI,
                                 scope=SCOPE)
    SPOTIFY_AUTH_URL = SPOTIPY_OAUTH.get_authorize_url()

def get_spotify_api():
    global SPOTIFY_API, AUTHENTICATED
    if not SPOTIFY_API and 'spotify_token' in os.environ:
        try:
            token_info = eval(os.environ['spotify_token']) # Load token from environment
            if SPOTIPY_OAUTH.is_token_expired(token_info):
                new_token = SPOTIPY_OAUTH.refresh_access_token(token_info['refresh_token'])
                os.environ['spotify_token'] = str(new_token)
                SPOTIFY_API = spotipy.Spotify(auth=new_token['access_token'])
            else:
                SPOTIFY_API = spotipy.Spotify(auth=token_info['access_token'])
            AUTHENTICATED = True
        except Exception as e:
            print(f"Error loading or refreshing Spotify token: {e}")
            AUTHENTICATED = False
            SPOTIFY_API = None
    return SPOTIFY_API

def play_retro_music():
    api = get_spotify_api()
    if api:
        results = api.search(q='retro gaming music instrumental', type='playlist', limit=1)
        if results and results['playlists']['items']:
            playlist_uri = results['playlists']['items'][0]['uri']
            try:
                api.start_playback(context_uri=playlist_uri)
                print(f"Playing: {results['playlists']['items'][0]['name']}")
            except spotipy.exceptions.SpotifyException as e:
                print(f"Error starting playback: {e}")
        else:
            print("Could not find a suitable retro gaming playlist.")
    else:
        print("Spotify not authenticated.")

def handle_auth_callback():
    code = os.environ.get('SPOTIFY_AUTH_CODE')
    if code:
        try:
            token_info = SPOTIPY_OAUTH.get_access_token(code)
            os.environ['spotify_token'] = str(token_info)
            print("Spotify authentication successful!")
            os.environ['SPOTIFY_AUTH_CODE'] = '' # Clear the code
            get_spotify_api() # Initialize the API
            play_retro_music()
        except spotipy.exceptions.SpotifyException as e:
            print(f"Error during token retrieval: {e}")

# --- Game Drawing Functions (draw_paddle, draw_ball, display_score) ---
def draw_paddle(x, y):
    pygame.draw.rect(screen, white, [x, y, paddle_width, paddle_height])

def draw_ball(x, y):
    pygame.draw.circle(screen, white, (x, y), ball_radius)

def display_score():
    left_text = font.render(str(left_score), True, white)
    right_text = font.render(str(right_score), True, white)
    screen.blit(left_text, (screen_width // 4, 50))
    screen.blit(right_text, (screen_width * 3 // 4 - right_text.get_width(), 50))

# --- Main Game Loop ---
create_spotify_oauth()

while game_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not AUTHENTICATED:
                print(f"Opening Spotify authentication in your browser: {SPOTIFY_AUTH_URL}")
                webbrowser.open(SPOTIFY_AUTH_URL)
                print("After authorizing, you might be redirected to a 'localhost' page that says 'Authorization code was sent to your console...'.")
                print("Copy the entire URL from your browser's address bar and paste it here:")
                redirected_url = input()
                if redirected_url:
                    try:
                        code = SPOTIPY_OAUTH.parse_response_code(redirected_url)
                        os.environ['SPOTIFY_AUTH_CODE'] = code
                        handle_auth_callback()
                    except Exception as e:
                        print(f"Error processing the authorization URL: {e}")
                else:
                    print("Authentication cancelled.")
            elif event.key == pygame.K_m and AUTHENTICATED:
                play_retro_music()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_w] and left_paddle_y > 0:
        left_paddle_y -= paddle_speed
    if keys[pygame.K_s] and left_paddle_y < screen_height - paddle_height:
        left_paddle_y += paddle_speed
    if keys[pygame.K_UP] and right_paddle_y > 0:
        right_paddle_y -= paddle_speed
    if keys[pygame.K_DOWN] and right_paddle_y < screen_height - paddle_height:
        right_paddle_y += paddle_speed

    # --- Ball Movement and Collision ---
    ball_x += ball_speed_x
    ball_y += ball_speed_y
    if ball_y - ball_radius < 0 or ball_y + ball_radius > screen_height:
        ball_speed_y *= -1

    # Paddle collision
    left_paddle_rect = pygame.Rect(left_paddle_x, left_paddle_y, paddle_width, paddle_height)
    right_paddle_rect = pygame.Rect(right_paddle_x, right_paddle_y, paddle_width, paddle_height)
    ball_rect = pygame.Rect(ball_x - ball_radius, ball_y - ball_radius, ball_radius * 2, ball_radius * 2)

    if ball_rect.colliderect(left_paddle_rect) and ball_speed_x < 0:
        ball_speed_x *= -1
        # Add some randomness to the vertical speed
        ball_speed_y += (ball_y - left_paddle_rect.centery) // 10
    if ball_rect.colliderect(right_paddle_rect) and ball_speed_x > 0:
        ball_speed_x *= -1
        # Add some randomness to the vertical speed
        ball_speed_y += (ball_y - right_paddle_rect.centery) // 10

    # Scoring
    if ball_x - ball_radius < 0:
        right_score += 1
        ball_x = screen_width // 2
        ball_y = screen_height // 2
        ball_speed_x *= -1
        ball_speed_y *= -1
    elif ball_x + ball_radius > screen_width:
        left_score += 1
        ball_x = screen_width // 2
        ball_y = screen_height // 2
        ball_speed_x *= -1
        ball_speed_y *= -1

    # --- Drawing ---
    screen.fill(black)
    draw_paddle(left_paddle_x, left_paddle_y)
    draw_paddle(right_paddle_x, right_paddle_y)
    draw_ball(int(ball_x), int(ball_y))
    display_score()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
