import random
import sys
import pygame
import mapgen
import itertools

size = width, height = 900, 900
black = 0, 0, 0
white = 255, 255, 255

SCREENRECT = pygame.Rect(0, 0, width, height)

screen = pygame.display.set_mode(size)
clock = pygame.time.Clock()

camera_size = 22
camera_x, camera_y = 0, 0

dpi = width / camera_size

def loadify(path, size=0):
    global dpi
    return pygame.transform.scale(pygame.image.load(path), (dpi - size, dpi - size)).convert()

def inverse_direction(direction):
    return (-direction[0], -direction[1])

def translated_rect(rect):
    global camera_x, camera_y
    return pygame.Rect(rect.x - camera_x, rect.y - camera_y, rect.width, rect.height)

def check_adjacent(x, y, grid):
    for dx, dy in itertools.product((-1, 0, 1), (-1, 0, 1)):
        if (dx == 0 and dy == 0) or (x == 0 and dx == -1) or (y == 0 and dy == -1) or (x == len(grid[0]) - 1 and dx == 1) or (y == len(grid) - 1 and dy == 1):
            continue
        if grid[y + dy][x + dx] != ".":
            return True
    return False

class Wall(pygame.sprite.Sprite):
    def __init__(self, initial_position=None):
        super().__init__(self.containers)
        self.origin_rect = self.image.get_rect()
        if initial_position is None:
            initial_position = (0, 0)
        (self.origin_rect.x, self.origin_rect.y) = initial_position

    @property
    def rect(self):
        return translated_rect(self.origin_rect)

    def draw(self, screen):
        screen.blit(self.image, translated_rect(self.origin_rect))

class Floor(pygame.sprite.Sprite):
    def __init__(self, initial_position=None):
        super().__init__(self.containers)
        self.origin_rect = self.image.get_rect()
        if initial_position is None:
            initial_position = (0, 0)
        (self.origin_rect.x, self.origin_rect.y) = initial_position

    @property
    def rect(self):
        return translated_rect(self.origin_rect)

    def draw(self, screen):
        screen.blit(self.image, translated_rect(self.origin_rect))

class Player(pygame.sprite.Sprite):
    speed = 2

    def __init__(self, initial_position=None):
        super().__init__(self.containers)
        self.origin_rect = self.image.get_rect(center=SCREENRECT.center)
        if initial_position is not None:
            (self.origin_rect.x, self.origin_rect.y) = initial_position

    def move(self, direction):
        global camera_x, camera_y
        direction = tuple([self.speed * c for c in direction])
        camera_x += direction[0]
        camera_y += direction[1]
        self.origin_rect.move_ip(direction)
        if any(pygame.sprite.spritecollide(self, obstacle_group, False)):
            self.origin_rect.move_ip(inverse_direction(direction))
            camera_x -= direction[0]
            camera_y -= direction[1]

    @property
    def rect(self):
        return translated_rect(self.origin_rect)

    def draw(self, screen):
        screen.blit(self.image, translated_rect(self.origin_rect))


abstract_map = mapgen.Map(40, 40)
abstract_map.generate_random()
abstract_map.generate_random_circle()
abstract_map.make_paths()
abstract_map.display()

spawn_point = abstract_map.rooms[0].center

background = pygame.Surface(size)
pygame.display.flip()

all_sprites = pygame.sprite.OrderedUpdates()
obstacle_group = pygame.sprite.Group()

Player.containers = all_sprites
Floor.containers = all_sprites
Wall.containers = all_sprites, obstacle_group

Player.image = loadify("player.png", size=10)
Wall.image = loadify("wall.png")
Floor.image = loadify("floor1.png")

map_grid = abstract_map.grid()

for y, row in enumerate(map_grid):
    for x, elem in enumerate(row):
        if elem in ('%', '#'):
            Floor((x * dpi, y * dpi))
        elif elem == '.':
            if check_adjacent(x, y, map_grid):
                Wall((x * dpi, y * dpi))
            
player = Player(initial_position=(spawn_point.x * dpi, spawn_point.y * dpi))
camera_x = spawn_point.x * dpi - width / 2 + player.origin_rect.width // 2
camera_y = spawn_point.y * dpi - height / 2 + player.origin_rect.height // 2

while True:
    ticked = clock.tick(240)
    all_sprites.clear(screen, background)

    all_sprites.update()

    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_z]:
        direction = (0, (-1)*ticked)
        player.move(direction)
    if keys[pygame.K_q]:
        direction = ((-1)*ticked, 0)
        player.move(direction)
    if keys[pygame.K_s]:
        direction = (0, ticked*1)
        player.move(direction)
    if keys[pygame.K_d]:
        direction = (ticked*1, 0)
        player.move(direction)

    dirty = all_sprites.draw(screen)
    
    pygame.display.update(dirty)

    
