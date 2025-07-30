import pygame
import random
import math
# Pygame
from pygame import Vector2
from pygame.rect import Rect
# Internal
from HelperClasses import *

pygame.init()

# Create a rect based on "center" coordinates
def calculate_centered_rect(x:int|float, y:int|float, w:int|float, h:int|float):
    """ Returns a Rect centered on xy """
    return Rect(x - w/2, y - h/2, w, h)

# Background Sprites
background_sprites = [
    pygame.image.load("sprites/backgrounds/forest.png"),
    pygame.image.load("sprites/backgrounds/fall.png"),
    pygame.image.load("sprites/backgrounds/desert.png"),
]
# Platform Sprites
platform_types = ["wood","stone","metal","glass"]
platform_sprites:dict[str, list] = {}
# Collect and scale platform sprites
global_platform_scale = 0.75
for platform_type in platform_types:
    sizes = []
    for platform_size in ["small","medium","large"]:
        sprite = pygame.image.load("sprites/platforms/%s/%s.png" % (platform_type, platform_size))
        sizes.append(pygame.transform.scale_by(sprite, global_platform_scale))
    platform_sprites[platform_type] = sizes

# Player Sprites
player_sprites = {
    "idle": pygame.image.load("sprites/player/idle.png"),
    "dead": pygame.image.load("sprites/player/dead.png"),
}
# Hud Sprites
heart_sprites = [
    pygame.image.load("sprites/hud/heart/empty.png"),
    pygame.image.load("sprites/hud/heart/full.png"),
]

# Screen
screen = pygame.display.set_mode((1024, 512))
pygame.display.set_caption("Slime Bounce")
pygame.display.set_icon(player_sprites["idle"])

# Rescale background images to fit screen height, assuming the images are square
for i in range(len(background_sprites)):
    background_sprites[i] = pygame.transform.scale(background_sprites[i], (screen.get_height(), screen.get_height()))

# Setup fonts
pygame.font.init() # you have to call this at the start, 
                   # if you want to use this module.
stats_font = pygame.font.SysFont('Comic Sans MS', 16)
title_font = pygame.font.SysFont('Comic Sans MS', 64)
button_font = pygame.font.SysFont('Comic Sans MS', 32)
title_button_font = pygame.font.SysFont('Comic Sans MS', 40)

# Static text renders and rects
transparent_overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
## Title
title_text = title_font.render("Slime Bounce", True, (100,20,150))


# Title menu play and quit
title_play = title_button_font.render("Play", True, (255,255,255))
title_quit = title_button_font.render("Quit", True, (255,255,255))
# Make title buttons same size
title_play_rect = title_play.get_rect().union(title_quit.get_rect()).scale_by(2,1.2)
title_play_rect.center = (int(screen.get_width()/2), 300)
# Copy play rect to quit so we can position them separately
title_quit_rect = title_play_rect.copy()
# Put in the bottom middle of the screen
title_quit_rect.centery = 400

## Paused
paused_text = title_font.render("Paused", True, (255,255,255))
paused_rect = paused_text.get_rect()
paused_rect.center = (int(screen.get_width()/2), int(screen.get_height()/3))

# Pause menu Quit button
paused_quit = button_font.render("Quit to title", True, (255,255,255))
paused_quit_rect = paused_quit.get_rect().scale_by(1.2,1.2)
# Put in bottom left corner of screen
paused_quit_rect.bottomleft = (50, screen.get_height() - 50)

# Results screen
results_page_rect = calculate_centered_rect(screen.get_width()/2, screen.get_height()/2,\
                                            screen.get_width()/3.25, screen.get_height()/1.25)

results_game_over = title_font.render("You died", True, (255,255,255))
results_game_over_rect = results_game_over.get_rect()
results_game_over_rect.center = (int(screen.get_width()/2), int(results_page_rect.top + results_game_over_rect.h/2))
results_next_level = title_font.render("Level Up", True, (255,255,255))
results_next_level_rect = results_next_level.get_rect()
results_next_level_rect.center = (int(screen.get_width()/2), int(results_page_rect.top + results_next_level_rect.h/2))

# Results screen Quit button
results_quit = button_font.render("Return", True, (255,255,255))
results_quit_rect = results_quit.get_rect().scale_by(1.2,1.2)
# Put in bottom left corner of screen
results_quit_rect.bottomleft = (50, screen.get_height() - 50)

# Results screen retry button
results_retry = button_font.render("Retry", True, (255,255,255))
results_retry_rect = results_retry.get_rect().scale_by(1.2,1.2)
# Put in bottom left corner of screen
results_retry_rect.bottomright = (screen.get_width() - 50, screen.get_height() - 50)

# Results screen next button
results_next = button_font.render("Next", True, (255,255,255))
results_next_rect = results_next.get_rect().scale_by(1.2,1.2)
# Put in bottom left corner of screen
results_next_rect.bottomright = (screen.get_width() - 50, screen.get_height() - 50)

# Setup clock
clock = pygame.time.Clock()

# Constants
half_pi = math.pi / 2

player_max_lives = 5
levelup_score_threshold = 1500

# Player physics constants
player_gravity = 200
player_control_speed = 500
player_bounce_factor = pygame.Vector2(0.8, 1)

# Platform settings
platform_spawn_rate = 1000
platform_spawn_heights = [340, 395, 450]
platform_spawn_speeds = [-200, 400, -150]

# Determine the amount of times to tile the background based on width
background_tile_count = math.ceil(screen.get_width() / background_sprites[0].get_width())

# Events
SPAWN_PLATFORM  = pygame.USEREVENT + 1
PLAYER_RESET_STATE  = pygame.USEREVENT + 2

# Variables
running = True
paused = False
scene = 0
background = random.randint(0, len(background_sprites)-1)

difficulty_level = 1

_debug = False
_previous_cursor_pos = Vector2()

input_vector = pygame.Vector2()
player_motion = pygame.Vector2()
player_state = "idle"
player_lives = 0
player_dead = False
# Time stats
game_start_time = 0
life_start_time = 0

# We are going to use floating points for position for smoother velocity application
# Apparently Pygame CE has a "frect" which would have solved this issue for me
player_position = pygame.Vector2()
player_rect = player_sprites["idle"].get_rect()

# Level's platform type
current_platform_type = ""
# List of all platforms
platforms:list[Platform] = []
# Dictionary of statistics to keep track of and print in the results page
results_stats:dict[str,ScoreStat] = {}
# Results page score field label
results_stats_score = stats_font.render("Score", True, (255,255,255))
results_stats_score_rect = results_stats_score.get_rect()
results_stats_score_rect.left = results_page_rect.left + 25
results_stats_score_rect.bottom = results_page_rect.bottom - 25

results_stats_difficulty = stats_font.render("Difficulty Level", True, (255,255,255))
results_stats_difficulty_rect = results_stats_difficulty.get_rect()
results_stats_difficulty_rect.left = results_page_rect.left + 25
results_stats_difficulty_rect.bottom = results_page_rect.bottom - 25 - results_stats_score_rect.h

def add_results_stat(stat:str, multiplier:float = 1, real_time:bool = True):
    """ Adds a new score statistic with the key "stat"

    `multiplier` if set scales this `value` in the score results, defaults to 1.0

    `real_time` if set controls whether value is used in level threshold, defaults to True """
    # Format highest_speed to Highest Speed
    text = stats_font.render(str.capitalize(stat).replace('_', ' '), True, (255,255,255))
    rect = text.get_rect()
    rect.left = results_page_rect.left + 25
    rect.centery = 150 + len(results_stats) * (rect.h+12)

    results_stats[stat] = ScoreStat(text, rect, multiplier, real_time)

# Exclude total time from "real time" score
add_results_stat("total_time", 0.01, False)
add_results_stat("longest_life", 0.01)
add_results_stat("highest_speed")
add_results_stat("wall_bounces", 10)
add_results_stat("platform_bounces", 50)
add_results_stat("deaths", -100, False)


# Move player storing the position as a floating vector instead of a pixel perfect position
# This makes the movement smoother
def move_player_to(x:float|None = None, y:float|None = None):
    """ Moves the player to x or y, or both

        Use this instead of setting position directly
    """
    if(x is not None and y is not None):
        player_position.update(x, y)
    else:
        if(x is not None):
            player_position.x = x
        if(y is not None):
            player_position.y = y

    player_rect.centerx = int(player_position.x)
    player_rect.centery = int(player_position.y)
def move_player_by(offset:Vector2):
    """ Moves the player by the offset
    
        Use this instead of setting position directly
    """
    # Use update to avoid unnecessary global and reassignment 
    player_position.update(player_position + offset)

    player_rect.centerx = int(player_position.x)
    player_rect.centery = int(player_position.y)

def spawn_random_platform(dt:float|None = None, x:int|None = None, y:int|None = None):
    """
        Spawns a random platform on the screen with one of the `platform_spawn_speeds` values

        if x is not defined this will place the platform off the screen opposite of the speed direction
        dt is recommended if x is not specified, to do a movement step back into the screen
        if y is not defined a value from `platform_spawn_speeds` will be chosen (same index as speed)
    """

    # Add variation to length and position
    height_index = random.randint(0, len(platform_spawn_heights) - 1)
    sprite_index = random.randint(0, len(platform_sprites["wood"]) - 1)

    speed = platform_spawn_speeds[height_index]
    # Increment the speed for every level above 1
    if (difficulty_level > 1):
        speed *= max(1,difficulty_level/2) * 1.1

    # Set default position based on speed direction
    if(x is None):
        if(speed < 0):
            # Put behind right side of screen
            x = screen.get_width()
        else:
            # Put behind left side of screen
            x = 0
    # Populate y if not specified
    if(y is None):
        y = platform_spawn_heights[height_index]

    sprite = platform_sprites[current_platform_type][sprite_index]

    # Offset the sprite spawn point off screen by half the sprite size
    if(speed < 0):
        spawn_offset = x + int(sprite.get_width()/2)
    else:
        spawn_offset = x - int(sprite.get_width()/2)

    if(dt is not None):
        # Offset the sprite spawn point back into screen by applying the motion once
        spawn_offset += int(speed * dt)

    # Calculate the rect for this sprite and position
    rect = calculate_centered_rect(spawn_offset, y, sprite.get_width(), sprite.get_height())
    platforms.append(Platform(sprite_index, rect, Vector2(speed,0)))

def respawn_player():
    """
        Respawns the player while decrementing the current `player_lives`
    """
    global player_state, player_lives, life_start_time
    # Reset motion and position
    player_motion.update()
    move_player_to(screen.get_width()/2, screen.get_height()/2 - 100)
    # Set player sprite to the dead sprite and reset 500ms later
    player_state = "dead"
    player_lives -= 1
    # This value will persist across level ups
    results_stats["deaths"].value += 1
    pygame.time.set_timer(PLAYER_RESET_STATE, 500, 1)

    # Store this life's length if it is longer than the currently stored time
    old_start_time = life_start_time
    life_start_time = pygame.time.get_ticks()
    
    results_stats["longest_life"].value = max(life_start_time - old_start_time, results_stats["longest_life"].value)

def calculate_total_score(real_time = False):
    total_score = 0
    # Draw each score stat in the panel
    for stat in results_stats:
        # Skip non real time stats if we are checking for real time
        if real_time and not results_stats[stat].real_time:
            continue

        # Add to the total score weighted by the stat's multiplier
        total_score += int(results_stats[stat].value * results_stats[stat].multiplier)

    return total_score

def on_gameplay_events(event, dt:float):
    """
        All EVENTs that run during the gameplay scene
    """
    global _debug, player_state

    # Key presses
    # Both key down and key up are used for the input vectors to undo the key press
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_LEFT or event.key == pygame.K_a:
            input_vector.x += -1
        if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
            input_vector.x += 1
        # DEBUG
        if event.key == pygame.K_F3:
            _debug = not _debug
        if _debug and event.key == pygame.K_F2:
            platforms.clear()
        # END DEBUG
    elif event.type == pygame.KEYUP:
        if event.key == pygame.K_LEFT or event.key == pygame.K_a:
            input_vector.x += 1
        if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
            input_vector.x += -1
    # On Spawn Platform
    elif event.type == SPAWN_PLATFORM:
        spawn_random_platform(dt)
    # Reset player's sprite
    elif event.type == PLAYER_RESET_STATE:
        player_state = "idle"

def on_gameplay_update(dt:float):
    """
        Gameplay scene's update loop
    """
    global player_state

    #results_stats["wall_bounces"].value

    # get current ticks
    current_time = pygame.time.get_ticks()
    # Store the duration of this session
    results_stats["total_time"].value =  current_time - game_start_time
    # Store this life's length if it is longer than currently stored time
    results_stats["longest_life"].value = max(current_time - life_start_time, results_stats["longest_life"].value)

    # DEBUG
    if _debug:
        if pygame.mouse.get_pressed()[0]: # Left Click
            rect = calculate_centered_rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], platform_sprites[current_platform_type][1].get_width(), platform_sprites[current_platform_type][1].get_height())

            cursor_motion = pygame.mouse.get_pos() - _previous_cursor_pos
            platforms.append(Platform(1, rect, cursor_motion/dt ))
        _previous_cursor_pos.update(pygame.mouse.get_pos())
    # END DEBUG

    ######
    ## Physics Update
    ##
    # Update the player motion based on gravity and the input vector
    player_motion.x += input_vector[0] * player_control_speed * dt
    player_motion.y += player_gravity * dt

    # Move player by the motion
    move_player_by(player_motion*dt)

    # IF outside of screen
    # Clamp X axis and bounce
    if(player_rect.right >= screen.get_width() or player_rect.left <= 0):
        move_player_to(x = max(player_rect.width/2, min(player_position.x, screen.get_width())))
        player_motion.x *= -player_bounce_factor.x
        # Step movement again to avoid getting stuck in wall
        move_player_by(player_motion*dt)
        results_stats["wall_bounces"].value += 1
    
    # Screen hit top
    if(player_rect.top <= 0):
        move_player_to(y=max(player_rect.height/2, min(player_position.y, screen.get_height())))
        player_motion.y *= -player_bounce_factor.y
        # Step movement again to avoid getting stuck in wall
        move_player_by(player_motion*dt)
        results_stats["wall_bounces"].value += 1
    
    # Update max speed after motion updates but before respawn check
    results_stats["highest_speed"].value = max(results_stats["highest_speed"].value , player_motion.magnitude())

    # If hit ground respawn player
    if(player_rect.bottom >= screen.get_height()):
        respawn_player()

    # Calculate ball position from last frame
    previous_pos = player_position - player_motion * dt # Vector2(pygame.mouse.get_pos())

    # Don't check other platforms to avoid getting stuck if colliding with multiple at once
    has_collided = False
    for platform in platforms:
        # Move Platform
        platform.rect = platform.rect.move(platform.motion * dt)
        # If platform is out of bounds of screen then remove it
        if(not platform.rect.colliderect(screen.get_rect())):
            platforms.remove(platform)

        # If inside of platform
        # Move ball out of rect and bounce on the hit axis
        # If we have collided already, skip this check and only move the platform above
        if(not has_collided and platform.rect.colliderect(player_rect)):
            results_stats["platform_bounces"].value += 1
            has_collided = True
            # Get direction the collision happened
            vector = previous_pos - platform.rect.center

            # Rescale direction vector to a square with assumption platform will always be wider than tall
            scaled_vector = pygame.Vector2(vector.x/platform.rect.width, vector.y/platform.rect.height)
            
            # Angle in the range of 0 -> Tau
            angle = math.atan2(scaled_vector.y, scaled_vector.x) + math.pi

            # Divide by tau instead of pi to get specific face
            axis = (round(angle / half_pi) * half_pi / math.tau) % 1

            # This could be de-duplicated somewhat
            # Check each direction to bounce and push the player out of the platform
            if(axis < 0.25):   # Left
                player_motion.x *= -player_bounce_factor.x
                if(platform.motion.x < 0): # If platform is moving left
                    player_motion.x += platform.motion.x
                player_position.x = platform.rect.topleft[0] - player_rect.width/2 - 1
            elif(axis < 0.5):  # Up
                player_motion.y *= -player_bounce_factor.y
                if(platform.motion.y < 0): # If platform is moving up
                    player_motion.y = (player_motion.y + platform.motion.y) * 0.8
                player_position.y = platform.rect.topleft[1] - player_rect.height/2 - 1
            elif(axis < 0.75): # Right
                player_motion.x *= -player_bounce_factor.x
                if(platform.motion.x > 0): # If platform is moving right
                    player_motion.x += platform.motion.x
                player_position.x = platform.rect.bottomright[0] + player_rect.width/2 + 1
            else: # Down
                player_motion.y *= -player_bounce_factor.y
                if(platform.motion.y > 0): # If platform is moving down
                    player_motion.y += (player_motion.y + platform.motion.y) * 0.8
                player_position.y = platform.rect.bottomright[1] + player_rect.height/2 + 1

            # If this platform is glass we should remove it
            if current_platform_type == "glass":
                platforms.remove(platform)


def on_gameplay_draw():
    """
        Gameplay scene's draw loop
    """
    # Draw each platform
    for platform in platforms:
        screen.blit(platform_sprites[current_platform_type][platform.sprite_index], platform.rect.topleft)

    # Draw the player
    screen.blit(player_sprites[player_state], player_rect)

    ### Debug
    if _debug:
        pygame.draw.line(screen, (255,0,0), player_rect.center, player_motion + player_rect.center, 5)
        #pygame.draw.line(screen, (0,255,0), pygame.mouse.get_pos(), _previous_cursor_pos, 5)

        screen.blit(stats_font.render("Platforms %s" % len(platforms), True, (0,0,0)), (50,50))
        screen.blit(stats_font.render("{0.x:3.2f}; {0.y:3.2f}".format(player_motion), True, (0,0,0)), (50,75))
        screen.blit(stats_font.render("%3.2f; %3.2f" % player_rect.center, True, (0,0,0)), (50,100))

        #screen.blit(debug_font.render("%3.2f" % score_max_speed, True, (0,0,0)), (50,150))
    ### END DEBUG

def on_gameplay_hud_draw():
    """
        Gameplay scene's hud draw loop
    """
    x = 40
    y = 40
    offset = heart_sprites[1].get_width()
    # Draw each heart and fill depending on remaining `player_lives`
    for i in range(player_max_lives):
        position = (x + offset*i, y)
        if i < player_lives:
            screen.blit(heart_sprites[1], position)
        else:
            screen.blit(heart_sprites[0], position)

    score_text = button_font.render("%i"  % calculate_total_score(True), True, (100,100,150))
    score_rect = score_text.get_rect()
    score_rect.topright = (screen.get_width() - 50, 50)
    screen.blit(score_text, score_rect)




def draw_button(text:pygame.Surface, rect:Rect, mouse_pos):
    """
        This handles drawing a button with highlighting on hover
    """
    # If mouse is on the button, draw lighter background otherwise draw black background
    if pygame.Rect.collidepoint(rect, mouse_pos):
        pygame.draw.rect(screen, (100,100,100), rect, border_radius=5)
    else:
        pygame.draw.rect(screen, (0,0,0), rect, border_radius=5)
    
    # Center the text on the `rect`
    text_rect = text.get_rect()
    text_rect.center = rect.center
    # Draw the text
    screen.blit(text, text_rect)

def on_title_draw(mouse_pos):
    """
        Title scene's draw loop
    """
    # Draw the title
    screen.blit(title_text, (screen.get_width()/2 - title_text.get_width()/2,64))
    # Play Button
    draw_button(title_play, title_play_rect, mouse_pos)
    # Quit Button
    draw_button(title_quit, title_quit_rect, mouse_pos)
    
def on_paused_overlay_draw(mouse_pos):
    """
        Gameplay Paused overlay draw loop
    """
    # Draw full screen darken overlay
    transparent_overlay.fill((0,0,0,50))
    screen.blit(transparent_overlay, (0,0))

    # Draw a background for the paused text with some padding
    pygame.draw.rect(screen, (0,0,0), paused_rect.scale_by(1.2,1.2))
    # Draw the paused text
    screen.blit(paused_text, paused_rect)
    # Add a quit button to corner to go to menu
    draw_button(paused_quit, paused_quit_rect, mouse_pos)


def on_results_draw(mouse_pos):
    """
        Result page scene's update loop
    """
    # Add a quit button to corner to go to menu
    draw_button(results_quit, results_quit_rect, mouse_pos)
    
    if player_dead:
        # Add replay button
        draw_button(results_retry, results_retry_rect, mouse_pos)
    else:
        # Add replay button
        draw_button(results_next, results_next_rect, mouse_pos)

    # Draw the transparent panel in the center of the screen
    pygame.draw.rect(transparent_overlay, (0,0,0,150), results_page_rect, border_radius=10)
    screen.blit(transparent_overlay, (0,0))
    
    # Draw the results page text on top
    if player_dead:
        screen.blit(results_game_over, results_game_over_rect)
    else:
        screen.blit(results_next_level, results_next_level_rect)

    total_score = 0
    # Draw each score stat in the panel
    for stat in results_stats:
        # Draw label
        screen.blit(results_stats[stat].text, results_stats[stat].rect)
        
        # Render the value's text
        stat_text = stats_font.render("%i" % int(results_stats[stat].value), True, (255,255,255))
        stat_rect = stat_text.get_rect()
        # Center the value with the label, then right align to the panel
        stat_rect.centery = results_stats[stat].rect.centery
        stat_rect.right = results_page_rect.right - 25
        # Draw the value
        screen.blit(stat_text, stat_rect)

        # Add to the total score weighted by the stat's multiplier
        total_score += int(results_stats[stat].value * results_stats[stat].multiplier)
    # Print total score
    # Draw label
    screen.blit(results_stats_score, results_stats_score_rect)
    screen.blit(results_stats_difficulty, results_stats_difficulty_rect)
    
    # Render the score
    stat_text = stats_font.render("%i" % total_score, True, (255,255,255))
    stat_rect = stat_text.get_rect()
    # Center the value with the label, then right align to the panel
    stat_rect.centery =  results_stats_score_rect.centery
    stat_rect.right = results_page_rect.right - 25
    # Draw the value
    screen.blit(stat_text, stat_rect)
    
    # Render the difficulty level
    stat_text = stats_font.render("%i" % difficulty_level, True, (255,255,255))
    stat_rect = stat_text.get_rect()
    # Center the value with the label, then right align to the panel
    stat_rect.centery =  results_stats_difficulty_rect.centery
    stat_rect.right = results_page_rect.right - 25
    # Draw the value
    screen.blit(stat_text, stat_rect)
    
def populate_platforms():
    """
        Spawns platforms randomly on each floor

        This is to give the player some platforms before timer spawned ones reach them on gameplay start
    """
    # Spawn 5 random platforms
    for i in range(5):
        # Choose random x position
        x = random.randint(0, screen.get_width())
        # Spawn platform
        spawn_random_platform(x=x)

def initialize_gameplay(next_level = False):
    """
        Initialize/Reset all gameplay variables and stats
    """
    global player_state, player_lives, game_start_time, life_start_time, player_dead, \
        difficulty_level, current_platform_type, background
    
    # Reset variables
    input_vector.update()
    player_motion.update()
    player_state = "idle"
    player_lives = player_max_lives
    player_dead = False

    background = random.randint(0, len(background_sprites)-1)

    if not next_level:
        difficulty_level = 1
    else:
        difficulty_level += 1

    # Increment current platform type max range with level
    platform_range = min(difficulty_level, len(platform_types)) - 1
    current_platform_type = platform_types[random.randint(0, platform_range)]

    # Center player
    move_player_to(screen.get_width()/2, screen.get_height()/2 - 100)
    # Clear all platforms
    platforms.clear()

    # Stats
    if not next_level:
        for stat in results_stats:
            results_stats[stat].value = 0

    # Initialization
    pygame.time.set_timer(SPAWN_PLATFORM, int(platform_spawn_rate / difficulty_level))
    populate_platforms()

    # Set starting time for life and game
    life_start_time = pygame.time.get_ticks()
    if next_level:
        # Restore relative time start
        game_start_time = pygame.time.get_ticks() - results_stats["total_time"].value
    else:
        game_start_time = life_start_time

# Game Loop
while running:
    dt = clock.tick(60)/1000

    mouse_pos = pygame.mouse.get_pos()

    # Button clicks
    if pygame.mouse.get_pressed()[0]: # Left click
        if paused:
            # Quit to title from paused
            if pygame.Rect.collidepoint(paused_quit_rect, mouse_pos):
                scene = 0
                paused = False
        elif scene == 0: # Title buttons
            # Quit game
            if pygame.Rect.collidepoint(title_quit_rect, mouse_pos):
                running = False
                break
            # Play
            elif pygame.Rect.collidepoint(title_play_rect, mouse_pos):
                scene = 1
                initialize_gameplay()
        elif scene == 2: # Results screen buttons
            # Quit to title from results
            if pygame.Rect.collidepoint(results_quit_rect, mouse_pos):
                scene = 0
            # Replay
            elif pygame.Rect.collidepoint(results_retry_rect, mouse_pos):
                scene = 1
                # Pass if this is next level or replay
                initialize_gameplay(not player_dead)


    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if scene == 1:
            # Key presses
            if event.type == pygame.KEYDOWN:
                # Pause menu
                if event.key == pygame.K_ESCAPE:
                    paused = not paused
            if not paused:
                # Do gameplay events
                on_gameplay_events(event, dt)
        ### DEBUG
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F4:
                scene = (scene+1)%3
                print("Changed scene to %i" % scene)
        ### DEBUG END

    ######
    ## On Update
    ##
    if scene == 1 and not paused:
        # Go to results if we run out of lives
        if player_lives <= 0:
            # get current ticks
            current_time = pygame.time.get_ticks()
            # Store the duration of this session
            results_stats["total_time"].value =  current_time - game_start_time
            # Store this life's length if it is longer than currently stored time
            results_stats["longest_life"].value = max(current_time - life_start_time, results_stats["longest_life"].value)
            
            player_dead = True
            scene = 2
        elif(calculate_total_score(True) >= levelup_score_threshold*difficulty_level):
            # get current ticks
            current_time = pygame.time.get_ticks()
            # Store the duration of this session
            results_stats["total_time"].value =  current_time - game_start_time
            # Store this life's length if it is longer than currently stored time
            results_stats["longest_life"].value = max(current_time - life_start_time, results_stats["longest_life"].value)

            player_dead = False
            scene = 2
        else:
            on_gameplay_update(dt)

    ######
    ## On Draw
    ##
    # Clear transparent overlay
    transparent_overlay.fill((0,0,0,0))

    # Get the current background
    bg = background_sprites[background]

    # Tile the background to fill the screen
    for i in range(background_tile_count):
        screen.blit(bg, (bg.get_width()*i, 0))

    # Draw scene
    if scene == 0: # Title
        on_title_draw(mouse_pos)
    if scene == 1: # Gameplay
        on_gameplay_draw()
        on_gameplay_hud_draw()
        if paused:
            on_paused_overlay_draw(mouse_pos)
    if scene == 2: # Results screen
        on_results_draw(mouse_pos)

    pygame.display.update()