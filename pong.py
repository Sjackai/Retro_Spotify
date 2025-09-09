import pygame
left_paddle_x = 50
right_paddle_x = screen_width - 50 - paddle_width
paddle_speed = 7 # Adjust speed to match thicker paddles
ball_radius = 8 #  smaller ball
ball_x = screen_width // 2
ball_y = screen_height // 2
ball_speed_x = 5
ball_speed_y = 5
ball_speed_increment = 0.1 # increase speed per hit
max_ball_speed = 15 # Maximum ball speed
left_score = 0
right_score = 0
# a basic monospaced font for retro look
retro_font = pygame.font.Font(pygame.font.get_default_font(), 60)
small_font = pygame.font.Font(pygame.font.get_default_font(), 20) # For instructions
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
        track_uris = [
            "spotify:track:0B7zVYoRimfnl1RqmFNksV",
            "spotify:track:2s2W7srrbWNmQB27RmF2he",
            "spotify:track:7zDQbfuTAFOM58C27tyAW4",
            "spotify:track:3gJwzQk84n80Z9r3q4B881",
            "spotify:track:7nukFkQ0oDN85D66FkE6hA"
        ]

        if track_uris:
            try:
                api.start_playback(uris=track_uris)
                print("Playing a selection of 5 retro tracks.")
            except spotipy.exceptions.SpotifyException as e:
                print(f"Error starting playback: {e}")
        else:
            print("No track URIs provided.")
    else:
        print("Spotify not authenticated.")

def handle_auth_callback():
    code = os.environ.get('SPOTIFY_AUTH_CODE')
    if code:
        try:
            token_info = SPOTIPY_OAUTH.get_access_token(code)
            os.environ['spotify_token'] = str(token_info)
            print("✅ Spotify authentication successful! Get ready for some awesome tunes!")
            os.environ['SPOTIFY_AUTH_CODE'] = '' # Clear the code
            get_spotify_api() # Initialize the API
            play_retro_music() # <---- CALLED HERE NOW
        except spotipy.exceptions.SpotifyException as e:
            print(f"Error during token retrieval: {e}")

# --- Game Drawing Functions ---
def draw_paddle(x, y):
    pygame.draw.rect(screen, paddle_color, [x, y, paddle_width, paddle_height])

def draw_ball(x, y):
    pygame.draw.circle(screen, ball_color, (x, y), ball_radius)

def draw_net():
    net_color = paddle_color
    segment_length = 15
    segment_gap = 10
    for i in range(0, screen_height, segment_length + segment_gap):
        pygame.draw.line(screen, net_color, (screen_width // 2, i), (screen_width // 2, i + segment_length), 2)

def display_score():
    left_text = retro_font.render(str(left_score), True, text_color)
    right_text = retro_font.render(str(right_score), True, text_color)
    screen.blit(left_text, (screen_width // 4, 50))
    screen.blit(right_text, (screen_width * 3 // 4 - right_text.get_width(), 50))

def display_spotify_instructions():
    instruction_text = small_font.render("Press SPACE to Connect to Spotify (Premium Required)", True, text_color)
    screen.blit(instruction_text, (10, screen_height - 30))

# --- Main Game Loop ---
create_spotify_oauth()

while game_running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            game_running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and not AUTHENTICATED:
                print("-" * 40)
                print("🎧 Ready to pump up the retro tunes?")
                print("To connect to your Spotify, a browser window will open.")
                print("Please grant permission for this game to control your music.")
                print("-" * 40)
                print(f"Opening Spotify authentication in your browser: {SPOTIFY_AUTH_URL}")
                webbrowser.open(SPOTIFY_AUTH_URL)
                print("-" * 40)
                print("Almost there!")
                print("Once you authorize, you'll be redirected to a page that might look a little strange.")
                print("Don't worry, that's normal!")
                print("Please **copy the entire web address (URL)** from the address bar of that new page.")
                print("Then, come back here and paste that URL into the console and press Enter.")
                print("-" * 40)
                redirected_url = input("Paste the full redirected URL here: ")
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
                pass # We don't need to call play_retro_music here anymore

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
        ball_speed_y += (ball_y - left_paddle_rect.centery) // 10
        # Increase ball speed on hit
        if abs(ball_speed_x) < max_ball_speed:
            ball_speed_x *= 1 + ball_speed_increment
        if abs(ball_speed_y) < max_ball_speed:
            ball_speed_y *= 1 + ball_speed_increment
    if ball_rect.colliderect(right_paddle_rect) and ball_speed_x > 0:
        ball_speed_x *= -1
        ball_speed_y += (ball_y - right_paddle_rect.centery) // 10
        # Increase ball speed on hit
        if abs(ball_speed_x) < max_ball_speed:
            ball_speed_x *= 1 + ball_speed_increment
        if abs(ball_speed_y) < max_ball_speed:
            ball_speed_y *= 1 + ball_speed_increment

    # Scoring
    if ball_x - ball_radius < 0:
        right_score += 1
        ball_x = screen_width // 2
        ball_y = screen_height // 2
        ball_speed_x = 5 # Reset ball speed after scoring
        ball_speed_y = 5
    elif ball_x + ball_radius > screen_width:
        left_score += 1
        ball_x = screen_width // 2
        ball_y = screen_height // 2
        ball_speed_x = -5 # Reset ball speed after scoring
        ball_speed_y = -5

    # --- Drawing ---
    screen.fill(dark_green) # Retro background color
    draw_net()
    draw_paddle(left_paddle_x, left_paddle_y)
    draw_paddle(right_paddle_x, right_paddle_y)
    draw_ball(int(ball_x), int(ball_y))
    display_score()
    display_spotify_instructions() # Draw the Spotify instructions

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
