import pygame
import random
import math
# Pygame
from pygame import Vector2
from pygame.rect import Rect
from pygame.color import Color
# Internal
from Platform import Platform

pygame.init()

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

# Rescale background images to fit screen height, assuming the images are square
for i in range(len(background_sprites)):
    background_sprites[i] = pygame.transform.scale(background_sprites[i], (screen.get_height(), screen.get_height()))

global_platform_scale = 0.75
for i in range(len(platform_sprites)):
    sprite = platform_sprites[i]
    platform_sprites[i] = pygame.transform.scale(sprite, (sprite.get_width() * global_platform_scale, sprite.get_height() * global_platform_scale))


pygame.font.init() # you have to call this at the start, 
                   # if you want to use this module.
font = pygame.font.SysFont('Comic Sans MS', 16)

clock = pygame.time.Clock()

running = True

# Constants
half_pi = math.pi / 2
platform_spawn_rate = 1000
player_gravity = 200
player_control_speed = 500
#player_radius = 20

bounce_factor = pygame.Vector2(0.8, 1)

platform_spawn_heights = [340, 395, 450]
platform_spawn_speeds = [-200, 400, -150]

# Events
SPAWN_PLATFORM  = pygame.USEREVENT + 1
PLAYER_RESET_STATE  = pygame.USEREVENT + 2

# Variables
scene = 1
background = random.randint(0, len(background_sprites)-1)
_debug = False

input_vector = pygame.Vector2(0)
player_motion = pygame.Vector2(0)
player_state = "idle"

_previous_cursor_pos = Vector2()

# We are going to use floating points for position for smoother velocity application
player_position:Vector2 = pygame.Vector2(screen.get_width()/2, screen.get_height()/2)
player_rect = player_sprites["idle"].get_rect().move(player_position)

platforms:list[Platform] = []

score_max_speed = 0


# Move player storing the position as a floating vector instead of a pixel perfect position
# This makes the movement smoother
def move_player_to(x:float|None = None, y:float|None = None):
    global player_position
    if(x is not None and y is not None):
        player_position = Vector2(x, y)
    else:
        if(x is not None):
            player_position.x = x
        if(y is not None):
            player_position.y = y

    player_rect.centerx = int(player_position.x)
    player_rect.centery = int(player_position.y)
def move_player_by(offset:Vector2):
    global player_position
    player_position += offset

    player_rect.centerx = int(player_position.x)
    player_rect.centery = int(player_position.y)

def calculate_sprite_rect(x:int, y:int, sprite:pygame.Surface):
    width = sprite.get_width()
    height = sprite.get_height()

    return Rect(x - width/2, y - height/2, width, height)

def spawn_random_platform(dt:float|None = None, x:int|None = None, y:int|None = None):
    # Add variation to length and position
    height_index = random.randint(0, len(platform_spawn_heights) - 1)
    sprite_index = random.randint(0, len(platform_sprites) - 1)

    speed = platform_spawn_speeds[height_index]

    if(x is None):
        if(speed < 0):
            x = screen.get_width()
        else:
            x = 0
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
    rect = calculate_sprite_rect(spawn_offset, y, sprite)
    platforms.append(Platform(sprite_index, rect, Vector2(speed,0)))

def respawn_player():
    global player_motion, player_state

    # Reset motion and position
    player_motion = pygame.Vector2()
    move_player_to(screen.get_width()/2, screen.get_height()/2)
    player_state = "dead"
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
    elif event.type == PLAYER_RESET_STATE:
        player_state = "idle"


def on_gameplay_update(dt:float):
    global player_position, player_state, _previous_cursor_pos, score_max_speed
    ######
    ## On Mouse Clicked
    ##
    if pygame.mouse.get_pressed()[0]: # Left Click
        rect = calculate_sprite_rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], platform_sprites[1])

        cursor_motion = pygame.mouse.get_pos() - _previous_cursor_pos
        platforms.append(Platform(1, rect, cursor_motion/dt ))
        
    _previous_cursor_pos = Vector2(pygame.mouse.get_pos())

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
        player_motion.x *= -bounce_factor.x
        # Step movement again to avoid getting stuck in wall
        move_player_by(player_motion*dt)
    
    # Screen hit top
    if(player_rect.top <= 0):
        move_player_to(y=max(player_rect.height/2, min(player_position.y, screen.get_height())))
        player_motion.y *= -bounce_factor.y
        # Step movement again to avoid getting stuck in wall
        move_player_by(player_motion*dt)
    
    # Update max speed after motion updates but before respawn check
    score_max_speed = max(score_max_speed, player_motion.magnitude())

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
                player_motion.x *= -bounce_factor.x
                if(platform.motion.x < 0): # If platform is moving left
                    player_motion.x += platform.motion.x
                player_position.x = platform.rect.topleft[0] - player_rect.width/2 - 1
            elif(axis < 0.5):  # Up
                player_motion.y *= -bounce_factor.y
                if(platform.motion.y < 0): # If platform is moving up
                    player_motion.y = (player_motion.y + platform.motion.y) * 0.8
                player_position.y = platform.rect.topleft[1] - player_rect.height/2 - 1
            elif(axis < 0.75): # Right
                player_motion.x *= -bounce_factor.x
                if(platform.motion.x > 0): # If platform is moving right
                    player_motion.x += platform.motion.x
                player_position.x = platform.rect.bottomright[0] + player_rect.width/2 + 1
            else: # Down
                player_motion.y *= -bounce_factor.y
                if(platform.motion.y > 0): # If platform is moving down
                    player_motion.y += (player_motion.y + platform.motion.y) * 0.8
                player_position.y = platform.rect.bottomright[1] + player_rect.height/2 + 1

            #player_state = "bounce"
            #pygame.time.set_timer(PLAYER_BOUNCE_END, 500, 1)

def on_gameplay_draw():
    screen.fill("black")

    # Get the current background
    bg = background_sprites[background]
    # Determine the amount of times to tile the background based on width
    background_tile_count = math.ceil(screen.get_width() / bg.get_width())
    # Tile the background to fill the screen
    for i in range(background_tile_count):
        screen.blit(bg, (bg.get_width()*i, 0))

    for platform in platforms:
        screen.blit(platform_sprites[platform.sprite_index], platform.rect.topleft)

    screen.blit(player_sprites[player_state], player_rect)

    ### Debug
    if _debug:
        pygame.draw.line(screen, (255,0,0), player_rect.center, player_motion + player_rect.center, 5)
        #pygame.draw.line(screen, (0,255,0), pygame.mouse.get_pos(), _previous_cursor_pos, 5)

        screen.blit(font.render("Platforms %s" % len(platforms), True, (0,0,0)), (50,50))
        screen.blit(font.render("{0.x:3.2f}; {0.y:3.2f}".format(player_motion), True, (0,0,0)), (50,75))
        screen.blit(font.render("%3.2f; %3.2f" % player_rect.center, True, (0,0,0)), (50,100))

        screen.blit(font.render("%3.2f" % score_max_speed, True, (0,0,0)), (50,150))
        

        

def populate_platforms():
    for i in range(5):
        x = random.randint(0, screen.get_width())

        spawn_random_platform(x=x)


# Initialization
pygame.time.set_timer(SPAWN_PLATFORM, platform_spawn_rate)
populate_platforms()

# Game Loop
while running:
    dt = clock.tick(60)/1000

    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if scene == 1:
            on_gameplay_events(event, dt)

    ######
    ## On Update
    ##
    if scene == 1:
        #print(dt)
        on_gameplay_update(dt)

    ######
    ## On Draw
    ##

    if scene == 1:
        on_gameplay_draw()

    pygame.display.update()