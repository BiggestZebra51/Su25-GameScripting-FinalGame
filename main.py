import pygame
import math

from pygame import Vector2
from pygame.rect import Rect
from pygame.color import Color

half_pi = math.pi / 2


pygame.init()


# Scene
scene = 1



# Screen
screen = pygame.display.set_mode((1024, 512))
pygame.display.set_caption("Test Game")

bounce_factor = pygame.Vector2(0.8, 1)

input_vector = pygame.Vector2(0)
motion = pygame.Vector2(0)
player_pos = pygame.Vector2(screen.get_width()/2, screen.get_height()/2)

player_radius = 20
width_max = screen.get_width() - player_radius
height_max = screen.get_height() - player_radius



clock = pygame.time.Clock()

running = True


platforms:list[tuple[Color, Rect]] = []

def calculate_rect(position:Vector2, width:int, height:int):
    return Rect(position.x - width/2, position.y - height/2, width, height)


def on_gameplay_events(event):
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

def on_gameplay_update(dt):
    ######
    ## On Mouse Clicked
    ##
    if pygame.mouse.get_pressed()[0]: # Left Click
        rect = calculate_rect(Vector2(pygame.mouse.get_pos()), 100, 40)
        box = (Color(200, 100, 100), rect)
        platforms.append(box)


    ######
    ## Physics Update
    ##
    motion.x += input_vector[0]* 20 * dt
    motion.y += 50 * dt

    global player_pos
    player_pos += motion*dt

    # IF outside of screen
    # Clamp X axis and bounce
    if(player_pos.x >= width_max or player_pos.x <= player_radius):
        player_pos.x = max(player_radius, min(player_pos.x, width_max))
        motion.x *= -bounce_factor.x
    # Clamp Y axis and bounce
    if(player_pos.y >= height_max or player_pos.y <= player_radius):
        player_pos.y = max(player_radius, min(player_pos.y, height_max))
        motion.y *= -bounce_factor.y
    
    # Calculate ball position from last frame
    previous_pos = player_pos - motion * dt # Vector2(pygame.mouse.get_pos())

    for platform in platforms:
        rect = platform[1]

        # If inside of platform
        # Move ball out of rect and bounce on the hit axis
        # TODO look into rect.collide and potentially change to a rect collider for the player
        if(player_pos.x >= rect.topleft[0] - player_radius and player_pos.x <= rect.bottomright[0] + player_radius and \
           player_pos.y >= rect.topleft[1] - player_radius and player_pos.y <= rect.bottomright[1] + player_radius):

            # Get direction the collision happened
            vector = previous_pos - rect.center
            #print(rect.w, rect.width)
            # Rescale direction vector to a square with assumption platform will always be wider than tall
            scaled_vector = pygame.Vector2(vector.x/rect.width, vector.y/rect.height)
            
            # Angle in the range of 0 -> Tau
            angle = math.atan2(scaled_vector.y, scaled_vector.x) + math.pi

            # Divide by tau instead of pi to get specific face
            axis = (round(angle / half_pi) * half_pi / math.tau) % 1

            if(axis < 0.25):   # Left
                motion.x *= -bounce_factor.x
                player_pos.x = rect.topleft[0] - player_radius - 1
            elif(axis < 0.5):  # Up
                motion.y *= -bounce_factor.y
                player_pos.y = rect.topleft[1] - player_radius - 1
            elif(axis < 0.75): # Right
                motion.x *= -bounce_factor.x
                player_pos.x = rect.bottomright[0] + player_radius + 1
            else: # Down
                motion.y *= -bounce_factor.y
                player_pos.y = rect.bottomright[1] + player_radius + 1

            #print('Hit')
        #break

def on_gameplay_draw():
    screen.fill("black")
    for platform in platforms:
        pygame.draw.rect(screen, platform[0], platform[1])

    pygame.draw.circle(screen, (255,255,255), player_pos, player_radius)

while running:
    dt = clock.tick(60)/1000

    # poll for events
    # pygame.QUIT event means the user clicked X to close your window
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if scene == 1:
            on_gameplay_events(event)

    ######
    ## On Update
    ##
    if scene == 1:
        on_gameplay_update(dt)

    ######
    ## On Draw
    ##

    if scene == 1:
        on_gameplay_draw()

    pygame.display.update()