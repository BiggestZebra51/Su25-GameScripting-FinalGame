import pygame
import math

from pygame import Vector2
from pygame.rect import Rect
from pygame.color import Color

from Platform import Platform



half_pi = math.pi / 2


pygame.init()


# Scene
scene = 1



# Screen
screen = pygame.display.set_mode((1024, 512))
pygame.display.set_caption("Test Game")

pygame.font.init() # you have to call this at the start, 
                   # if you want to use this module.
font = pygame.font.SysFont('Comic Sans MS', 30)

bounce_factor = pygame.Vector2(0.8, 1)

player_control_speed = 200
player_gravity = 200
input_vector = pygame.Vector2(0)
player_motion = pygame.Vector2(0)
player_position = pygame.Vector2(screen.get_width()/2, screen.get_height()/2)
player_radius = 20

width_max = screen.get_width() - player_radius
height_max = screen.get_height() - player_radius

clock = pygame.time.Clock()

running = True

# Events
SPAWN_PLATFORM = pygame.USEREVENT + 1


platforms:list[Platform] = []

def calculate_rect(x:int, y:int, width:int, height:int):
    return Rect(x - width/2, y - height/2, width, height)

def respawn_player():
    global player_motion, player_position
    # Reset motion and position
    player_motion = pygame.Vector2(0)
    player_position = pygame.Vector2(screen.get_width()/2, screen.get_height()/2)

def on_gameplay_events(event, dt:float):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_LEFT:
            input_vector.x += -1
        if event.key == pygame.K_RIGHT:
            input_vector.x += 1
        if event.key == pygame.K_DOWN:
            input_vector.y += -1
    elif event.type == pygame.KEYUP:
        if event.key == pygame.K_LEFT:
            input_vector.x += 1
        if event.key == pygame.K_RIGHT:
            input_vector.x += -1
        if event.key == pygame.K_DOWN:
            input_vector.y += 1

    elif event.type == SPAWN_PLATFORM:
        ######
        ## Spawn platforms
        ##
        # Add variation to length and position
        rect = calculate_rect(int(screen.get_width()+50 - (200*dt)), 350, 100, 20)
        platforms.append(Platform(rect, Color(200, 150, 100), Vector2(-200,0)))

def on_gameplay_update(dt:float):
    ######
    ## On Mouse Clicked
    ##
    if pygame.mouse.get_pressed()[0]: # Left Click
        rect = calculate_rect(pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1], 100, 40)

        platforms.append(Platform(rect, Color(200, 100, 100)))

    ######
    ## Physics Update
    ##
    player_motion.x += input_vector[0] * player_control_speed * dt
    player_motion.y += player_gravity * dt

    global player_position
    player_position += player_motion*dt

    # IF outside of screen
    # Clamp X axis and bounce
    if(player_position.x >= width_max or player_position.x <= player_radius):
        player_position.x = max(player_radius, min(player_position.x, width_max))
        player_motion.x *= -bounce_factor.x
    # Clamp Y axis and bounce
    if(player_position.y <= player_radius):
        player_position.y = max(player_radius, min(player_position.y, height_max))
        player_motion.y *= -bounce_factor.y
    
    # If hit ground respawn player
    if(player_position.y >= height_max):
        respawn_player()

    # Calculate ball position from last frame
    previous_pos = player_position - player_motion * dt # Vector2(pygame.mouse.get_pos())

    for platform in platforms:
        # Move Platform
        platform.rect = platform.rect.move(platform.motion * dt)
        print(platform.rect.topleft, platform.motion * dt)
        # If platform is out of bounds of screen then remove it
        if(not platform.rect.colliderect(screen.get_rect())):
            print("Platform out of bounds, removing")
            platforms.remove(platform)

        # If inside of platform
        # Move ball out of rect and bounce on the hit axis
        # TODO look into rect.collide and potentially change to a rect collider for the player
        if(player_position.x >= platform.rect.topleft[0] - player_radius and player_position.x <= platform.rect.bottomright[0] + player_radius and \
           player_position.y >= platform.rect.topleft[1] - player_radius and player_position.y <= platform.rect.bottomright[1] + player_radius):

            # Get direction the collision happened
            vector = previous_pos - platform.rect.center
            #print(rect.w, rect.width)
            # Rescale direction vector to a square with assumption platform will always be wider than tall
            scaled_vector = pygame.Vector2(vector.x/platform.rect.width, vector.y/platform.rect.height)
            
            # Angle in the range of 0 -> Tau
            angle = math.atan2(scaled_vector.y, scaled_vector.x) + math.pi

            # Divide by tau instead of pi to get specific face
            axis = (round(angle / half_pi) * half_pi / math.tau) % 1

            if(axis < 0.25):   # Left
                player_motion.x *= -bounce_factor.x
                player_position.x = platform.rect.topleft[0] - player_radius - 1
            elif(axis < 0.5):  # Up
                player_motion.y *= -bounce_factor.y
                player_position.y = platform.rect.topleft[1] - player_radius - 1
            elif(axis < 0.75): # Right
                player_motion.x *= -bounce_factor.x
                player_position.x = platform.rect.bottomright[0] + player_radius + 1
            else: # Down
                player_motion.y *= -bounce_factor.y
                player_position.y = platform.rect.bottomright[1] + player_radius + 1

            #print('Hit')
        #break

def on_gameplay_draw():
    screen.fill("black")
    for platform in platforms:
        pygame.draw.rect(screen, platform.color, platform.rect)

    pygame.draw.circle(screen, (255,255,255), player_position, player_radius)



    ### Debug
    screen.blit(font.render("Platforms %s" % len(platforms), True, (255,255,255)), (50,50))

# Initialization
pygame.time.set_timer(SPAWN_PLATFORM, 1000)

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