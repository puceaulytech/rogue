import random
import sys
import pygame
import mapgen

m = mapgen.Map(30, 30, max_rooms=9)
m.generate_random()
camera_size = 12

size = width, height = 900, 900
black = 0, 0, 0
white = 255, 255, 255

dpi = width / camera_size
screen = pygame.display.set_mode(size)

wall = pygame.image.load("wall.png")
wall = pygame.transform.scale(wall, (dpi, dpi))

floor1 = pygame.image.load("floor1.png")
floor1 = pygame.transform.scale(floor1, (dpi, dpi))

floor2 = pygame.image.load("floor2.png")
floor2 = pygame.transform.scale(floor2, (dpi, dpi))

pos_x, pos_y = 0, 0

def clamp_pos():
    global pos_x, pos_y
    if pos_x < 0:
        pos_x = 0
    if pos_y < 0:
        pos_y = 0

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z:
                pos_y -= 1
                clamp_pos()
            if event.key == pygame.K_q:
                pos_x -= 1
                clamp_pos()
            if event.key == pygame.K_s:
                pos_y += 1
                clamp_pos()
            if event.key == pygame.K_d:
                pos_x += 1
                clamp_pos()

    screen.fill(black)
    view = m.slice(mapgen.Coord(pos_x, pos_y), camera_size + 1, camera_size + 1)

    for y, row in enumerate(view):
        for x, elem in enumerate(row):
            to_draw = None
            is_color = False
            if elem == '.':
                to_draw = wall
            else:
                to_draw = floor1
            if is_color:
                screen.fill(to_draw, pygame.Rect(x * dpi, y * dpi, dpi, dpi))
            else:
                screen.blit(to_draw, pygame.Rect(x * dpi, y * dpi, dpi, dpi))

    pygame.display.flip()
