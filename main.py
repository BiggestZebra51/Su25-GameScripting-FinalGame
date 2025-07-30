import pygame
import random
import math
# Pygame
from pygame import Vector2
from pygame.rect import Rect
# Internal
from HelperClasses import *

pygame.init()

def calculate_centered_rect(x:int|float, y:int|float, w:int|float, h:int|float):
    return Rect(x - w/2, y - h/2, w, h)

# Screen
screen = pygame.display.set_mode((1024, 512))
pygame.display.set_caption("Test Game")

# Background Sprites
background_sprites = [
    pygame.image.load("sprites/backgrounds/forest.png"),
    pygame.image.load("sprites/backgrounds/fall.png"),
    pygame.image.load("sprites/backgrounds/desert.png"),
]
# Platform Sprites
platform_sprites = [
    pygame.image.load("sprites/platforms/stone/small.png"),
    pygame.image.load("sprites/platforms/stone/medium.png"),
    pygame.image.load("sprites/platforms/stone/medium.png"),
    pygame.image.load("sprites/platforms/stone/large.png"),
]
# Player Sprites
player_sprites = {
    "idle": pygame.image.load("sprites/player/idle.png"),
    "dead": pygame.image.load("sprites/player/dead.png"),
}
heart_sprites = [
    pygame.image.load("sprites/hud/heart/empty.png"),
    pygame.image.load("sprites/hud/heart/full.png"),
]

# Rescale background images to fit screen height, assuming the images are square
for i in range(len(background_sprites)):
    background_sprites[i] = pygame.transform.scale(background_sprites[i], (screen.get_height(), screen.get_height()))

# Rescale the platforms to be a little smaller
# TODO Bake this
global_platform_scale = 0.75
for i in range(len(platform_sprites)):
    sprite = platform_sprites[i]
    platform_sprites[i] = pygame.transform.scale(sprite, (sprite.get_width() * global_platform_scale, sprite.get_height() * global_platform_scale))

# Setup fonts
pygame.font.init() # you have to call this at the start, 
                   # if you want to use this module.
debug_font = pygame.font.SysFont('Comic Sans MS', 16)
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

# End screen
results_page_rect = calculate_centered_rect(screen.get_width()/2, screen.get_height()/2,\
                                            screen.get_width()/3.25, screen.get_height()/1.25)

results_text = title_font.render("You died", True, (255,255,255))
results_rect = results_text.get_rect()
results_rect.center = (int(screen.get_width()/2), int(results_page_rect.top + results_rect.h/2))

# End screen Quit button
results_quit = button_font.render("Return", True, (255,255,255))
results_quit_rect = results_quit.get_rect().scale_by(1.2,1.2)
# Put in bottom left corner of screen
results_quit_rect.bottomleft = (50, screen.get_height() - 50)

# End screen retry button
results_retry = button_font.render("Retry", True, (255,255,255))
results_retry_rect = results_retry.get_rect().scale_by(1.2,1.2)
# Put in bottom left corner of screen
results_retry_rect.bottomright = (screen.get_width() - 50, screen.get_height() - 50)

# Setup clock
clock = pygame.time.Clock()

# Constants
half_pi = math.pi / 2

player_max_lives = 5
# Player physics constants
player_gravity = 200
player_control_speed = 500
player_bounce_factor = pygame.Vector2(0.8, 1)

# Platform variables
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
player_lives = 0

_debug = False
_previous_cursor_pos = Vector2()

input_vector = pygame.Vector2()
player_motion = pygame.Vector2()
player_state = "idle"

# We are going to use floating points for position for smoother velocity application
# Apparently Pygame CE has a "frect" which would have solved this issue for me
player_position = pygame.Vector2()
player_rect = player_sprites["idle"].get_rect()

platforms:list[Platform] = []

# Dictionary of statistics to keep track of and print in the results page
results_stats:dict[str,ScoreStat] = {}

def add_results_stat(stat:str):
    # Format highest_speed to Highest Speed
    text = debug_font.render(str.capitalize(stat).replace('_', ' '), True, (255,255,255))
    rect = text.get_rect()
    rect.left = results_page_rect.left + 25
    rect.centery = 150 + len(results_stats) * (rect.h+12)

    results_stats[stat] = ScoreStat(text, rect)

add_results_stat("highest_speed")
add_results_stat("wall_bounces")
add_results_stat("platform_bounces")


# Move player storing the position as a floating vector instead of a pixel perfect position
# This makes the movement smoother
def move_player_to(x:float|None = None, y:float|None = None):
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
    # Use update to avoid unnecessary global and reassignment 
    player_position.update(player_position + offset)

    player_rect.centerx = int(player_position.x)
    player_rect.centery = int(player_position.y)

def spawn_random_platform(dt:float|None = None, x:int|None = None, y:int|None = None):
    # Add variation to length and position
    height_index = random.randint(0, len(platform_spawn_heights) - 1)
    sprite_index = random.randint(0, len(platform_sprites) - 1)

    speed = platform_spawn_speeds[height_index]

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

    sprite = platform_sprites[sprite_index]

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
    global player_state, player_lives

    # Reset motion and position
    player_motion.update()
    move_player_to(screen.get_width()/2, screen.get_height()/2)
    # Set player sprite to the dead sprite and reset 500ms later
    player_state = "dead"
    player_lives -= 1
    pygame.time.set_timer(PLAYER_RESET_STATE, 500, 1)


def on_gameplay_events(event, dt:float):
    global _debug, player_state

    # Key presses
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_LEFT:
            input_vector.x += -1
        if event.key == pygame.K_RIGHT:
            input_vector.x += 1
        if event.key == pygame.K_DOWN:
            input_vector.y += -1
        # DEBUG
        if event.key == pygame.K_F3:
            _debug = not _debug
        if _debug and event.key == pygame.K_F2:
            platforms.clear()
    elif event.type == pygame.KEYUP:
        if event.key == pygame.K_LEFT:
            input_vector.x += 1
        if event.key == pygame.K_RIGHT:
            input_vector.x += -1
        if event.key == pygame.K_DOWN:
            input_vector.y += 1
    # On Spawn Platform
    elif event.type == SPAWN_PLATFORM:
        spawn_random_platform(dt)
    # Reset player's sprite
    elif event.type == PLAYER_RESET_STATE:
        player_state = "idle"

def on_gameplay_update(dt:float):
    global player_state
    ######
    ## On Mouse Clicked
    ##

    # DEBUG
    if _debug:
        if pygame.mouse.get_pressed()[0]: # Left Click
            rect = calculate_centered_rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], platform_sprites[1].get_width(), platform_sprites[1].get_height())

            cursor_motion = pygame.mouse.get_pos() - _previous_cursor_pos
            platforms.append(Platform(1, rect, cursor_motion/dt ))        
        _previous_cursor_pos.update(pygame.mouse.get_pos())
    # END DEBUG

    ######
    ## Physics Update
    ##
    player_motion.x += input_vector[0] * player_control_speed * dt
    player_motion.y += player_gravity * dt

    #global player_position
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

            #player_state = "bounce"
            #pygame.time.set_timer(PLAYER_BOUNCE_END, 500, 1)

def on_gameplay_draw():
    for platform in platforms:
        screen.blit(platform_sprites[platform.sprite_index], platform.rect.topleft)

    screen.blit(player_sprites[player_state], player_rect)

    ### Debug
    if _debug:
        pygame.draw.line(screen, (255,0,0), player_rect.center, player_motion + player_rect.center, 5)
        #pygame.draw.line(screen, (0,255,0), pygame.mouse.get_pos(), _previous_cursor_pos, 5)

        screen.blit(debug_font.render("Platforms %s" % len(platforms), True, (0,0,0)), (50,50))
        screen.blit(debug_font.render("{0.x:3.2f}; {0.y:3.2f}".format(player_motion), True, (0,0,0)), (50,75))
        screen.blit(debug_font.render("%3.2f; %3.2f" % player_rect.center, True, (0,0,0)), (50,100))

        #screen.blit(debug_font.render("%3.2f" % score_max_speed, True, (0,0,0)), (50,150))

def on_gameplay_hud_draw():
    x = 40
    y = 40
    offset = heart_sprites[1].get_width()
    for i in range(player_max_lives):
        position = (x + offset*i, y)
        if i < player_lives:
            screen.blit(heart_sprites[1], position)
        else:
            screen.blit(heart_sprites[0], position)



def draw_button(text:pygame.Surface, rect:Rect, mouse_pos):
    if pygame.Rect.collidepoint(rect, mouse_pos):
        pygame.draw.rect(screen, (100,100,100), rect, border_radius=5)
    else:
        pygame.draw.rect(screen, (0,0,0), rect, border_radius=5)
    
    text_rect = text.get_rect()
    text_rect.center = rect.center
    screen.blit(text, text_rect)

def on_title_draw(mouse_pos):
    screen.blit(title_text, (screen.get_width()/2 - title_text.get_width()/2,64))
    # Add quit and play buttons

    # Play Button
    draw_button(title_play, title_play_rect, mouse_pos)
    # Quit Button
    draw_button(title_quit, title_quit_rect, mouse_pos)
    
def on_paused_overlay_draw(mouse_pos):
    transparent_overlay.fill((0,0,0,50))
    screen.blit(transparent_overlay, (0,0))

    # Draw a background for the paused text with some padding
    pygame.draw.rect(screen, (0,0,0), paused_rect.scale_by(1.2,1.2))
    # Draw the paused text
    screen.blit(paused_text, paused_rect)
    # Add a quit button to corner to go to menu
    draw_button(paused_quit, paused_quit_rect, mouse_pos)

def on_results_draw(mouse_pos):
    # Add a quit button to corner to go to menu
    draw_button(results_quit, results_quit_rect, mouse_pos)
    # Add replay button
    draw_button(results_retry, results_retry_rect, mouse_pos)

    pygame.draw.rect(transparent_overlay, (0,0,0,150), results_page_rect, border_radius=10)
    screen.blit(transparent_overlay, (0,0))
    
    screen.blit(results_text, results_rect)

    for stat in results_stats:
        screen.blit(results_stats[stat].text, results_stats[stat].rect)
        
        if results_stats[stat].value is float:
            format_str = "%.2f"
        else:
            format_str = "%i"

        stat_text = debug_font.render(format_str%results_stats[stat].value, True, (255,255,255))
        stat_rect = stat_text.get_rect()
        stat_rect.centery = results_stats[stat].rect.centery
        stat_rect.right = results_page_rect.right - 25
        screen.blit(stat_text, stat_rect)


def populate_platforms():
    for i in range(5):
        x = random.randint(0, screen.get_width())

        spawn_random_platform(x=x)

def initialize_gameplay():
    global player_state, player_lives
    # Reset variables
    input_vector.update()
    player_motion.update()
    player_state = "idle"
    player_lives = player_max_lives

    move_player_to(screen.get_width()/2, screen.get_height()/2 - 100)

    platforms.clear()

    # Stats
    #score_max_speed = 0
    for stat in results_stats:
        results_stats[stat].value = 0

    # Initialization
    pygame.time.set_timer(SPAWN_PLATFORM, platform_spawn_rate)
    populate_platforms()

# Game Loop
while running:
    dt = clock.tick(60)/1000

    mouse_pos = pygame.mouse.get_pos()

    # Button clicks
    if pygame.mouse.get_pressed()[0]: # Left click
        if paused:
            # Quit to title btn
            if pygame.Rect.collidepoint(paused_quit_rect, mouse_pos):
                scene = 0
                paused = False
        elif scene == 0: # Title buttons
            # Quit
            if pygame.Rect.collidepoint(title_quit_rect, mouse_pos):
                running = False
                break
            # Play
            elif pygame.Rect.collidepoint(title_play_rect, mouse_pos):
                scene = 1
                initialize_gameplay()
        elif scene == 2: # End screen buttons
            # Return to title
            if pygame.Rect.collidepoint(results_quit_rect, mouse_pos):
                scene = 0
            # Replay
            elif pygame.Rect.collidepoint(results_retry_rect, mouse_pos):
                scene = 1
                initialize_gameplay()


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
                on_gameplay_events(event, dt)

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F4:
                scene = (scene+1)%3
                print("Changed scene to %i" % scene)

    ######
    ## On Update
    ##

    if scene == 1 and not paused:
        if player_lives <= 0:
            scene = 2
        else:
            on_gameplay_update(dt)

    ######
    ## On Draw
    ##
    ### Draw background
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