import random
import math
import sys
import os
import pygame
import mapgen
import itertools
import time

size = width, height = 900, 900
black = 0, 0, 0
white = 255, 255, 255
fps = 0
ticked = 0

pygame.init()

SCREENRECT = pygame.Rect(0, 0, width, height)

screen = pygame.display.set_mode(size)
pygame.display.set_caption("ChadRogue")
pygame.mouse.set_visible(False)
pygame.mixer.music.load("assets/music.ogg")
pygame.mixer.music.play(-1)
clock = pygame.time.Clock()


camera_size = 12
camera_x, camera_y = 0, 0

dpi = width / camera_size

def loadify(path, size=0, keep_ratio=False):
    global dpi
    good_path = os.path.join("assets", path)
    image = pygame.image.load(good_path).convert_alpha()
    ratio = image.get_width() / image.get_height() if keep_ratio else 1
    return pygame.transform.scale(image, ((dpi + size) * ratio, dpi + size))

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

class FPSCounter(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(self.containers)
        self.font = pygame.font.SysFont("Consolas", 20)
        self.color = "white"
        self.update()
        self.rect = self.image.get_rect().move(0, 0)

    def update(self):
        self.image = self.font.render(f"FPS: {round(fps)}", False, self.color)

class HealthIcon(pygame.sprite.Sprite):
    def __init__(self, offset):
        super().__init__(self.containers)
        self.rect = self.image.get_rect().move(0 + offset * 50, height - 50)

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

class Background(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(self.containers)
        self.rect = self.image.get_rect(center=SCREENRECT.center)

    def move(self, direction, delta_time):
        direction = tuple([round(0.05 * delta_time * c) for c in direction])
        self.rect.move_ip(inverse_direction(direction))

    def draw(self, screen):
        screen.blit(self.image, translated_rect(self.rect))

class Ground(pygame.sprite.Sprite):
    def __init__(self, initial_position=None):
        super().__init__(self.containers)
        self.image = random.choice(random.choices(self.images,[1,50,1,1,1,1]))
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
    speed = 0.35

    def __init__(self, initial_position=None):
        super().__init__(self.containers)
        self.health = 5
        self.origin_rect = self.image.get_rect(center=SCREENRECT.center)
        if initial_position is not None:
            (self.origin_rect.x, self.origin_rect.y) = initial_position

    def move(self, direction, delta_time):
        global camera_x, camera_y
        origin_direction = direction
        direction = tuple([round(self.speed * delta_time * c) for c in direction])
        camera_x += direction[0]
        camera_y += direction[1]
        self.origin_rect.move_ip(direction)
        background_sprite.move(origin_direction, delta_time)
        if any(pygame.sprite.spritecollide(self, obstacle_group, False)):
            camera_x -= direction[0]
            camera_y -= direction[1]
            self.origin_rect.move_ip(inverse_direction(direction))
            background_sprite.move(inverse_direction(origin_direction), delta_time)

    @property
    def rect(self):
        return translated_rect(self.origin_rect)

    def draw(self, screen):
        screen.blit(self.image, translated_rect(self.origin_rect))

class Particle(pygame.sprite.Sprite):
    def __init__(self,coords,image = None,radius = None,lifetime = 100): 

        self.lifetime= lifetime
        super().__init__(self.containers)
        self.image = image
        self.radius = radius
        if image != None : 
            self.origin_rect = self.image.get_rect()
            (self.origin_rect.x, self.origin_rect.y) = coords
        else : 
            self.origin_rect = pygame.Rect(coords, (radius,radius))
    def move(self, direction): 
        self.origin_rect.move_ip(direction)
    def draw(self): 
        if self.image != None : 
            screen.blit(self.image, self.origin_rect)
        else : 
            pygame.draw.circle(screen,(100,100,100,self.lifetime),radius=self.radius,center=(self.origin_rect.x,self.origin_rect.y))
class ParticleEffect:
    def __init__(self,number = 100, lifetime = 100,images = None, forces = None, spawner = None):
        self.number  = number
        self.images = images
        self.forces = forces
        self.spawner = spawner
        self.lifetime = lifetime
        Particle.containers = self.containers
        self.particle_list = []
        for i in range(number) : 
            x = random.randint(spawner.x, spawner.width + spawner.x)
            y = random.randint(spawner.y, spawner.height + spawner.y)
            self.particle_list.append(Particle((x,y),self.images,2,self.lifetime+ random.randint(-20,20)))
            
    def update(self,delta):
        for i in range(len(self.particle_list)):
            if self.forces : 
                self.particle_list[i].move(self.forces*delta)
            self.particle_list[i].lifetime -= 1
            if self.particle_list[i].lifetime == 0:
                self.particle_list[i] = Particle((x,y),self.images,2,self.lifetime+ random.randint(-20,20))
    def draw(self):
        for part in self.particle_list:
            part.draw()




class BlackCreature(pygame.sprite.Sprite):
    speed = 0.1

    def __init__(self, initial_position=None):
        super().__init__(self.containers)
        self.health = 3
        self.last_attack = 0
        self.attack_cooldown = 1
        self.origin_rect = self.image.get_rect()
        if initial_position is not None:
            (self.origin_rect.x, self.origin_rect.y) = initial_position

    @property
    def rect(self):
        return translated_rect(self.origin_rect)

    def update(self):
        distance_to_player = math.sqrt((self.origin_rect.x - player.origin_rect.x)**2 + (self.origin_rect.y - player.origin_rect.y)**2)
        if distance_to_player < 5 * dpi:
            dx = (player.origin_rect.x - self.origin_rect.x) / (distance_to_player + 0.000001)
            dy = (player.origin_rect.y - self.origin_rect.y) / (distance_to_player + 0.000001)
            self.move((dx, dy), ticked)
            if pygame.sprite.collide_rect(player, self) and time.time() - self.last_attack > self.attack_cooldown:
                player.health -= 1
                if not player.health < 0: # TODO: juste pour éviter le crash
                    healthbar_group.sprites()[-1].kill()
                self.last_attack = time.time()

    def move(self, direction, delta_time):
        direction = tuple([round(self.speed * delta_time * c) for c in direction])
        self.origin_rect.move_ip(direction)
        if any(pygame.sprite.spritecollide(self, obstacle_group, False)):
            self.origin_rect.move_ip(inverse_direction(direction))

class Cursor(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(self.containers)
        self.rect = self.image.get_rect()
        self.update_pos()

    def update_pos(self):
        (self.rect.x, self.rect.y) = pygame.mouse.get_pos()

    def update(self):
        self.update_pos()

abstract_map = mapgen.Map(40, 40)
abstract_map.generate_random()
abstract_map.generate_random_circle()
abstract_map.make_paths()
abstract_map.fill_with_elements()
abstract_map.display()

spawn_point = abstract_map.rooms[0].center

background = pygame.Surface(size)
pygame.display.flip()

all_sprites = pygame.sprite.OrderedUpdates()
obstacle_group = pygame.sprite.Group()
creature_group = pygame.sprite.Group()
hud_groud = pygame.sprite.Group()
healthbar_group = pygame.sprite.Group()
particle_group = pygame.sprite.Group()
ParticleEffect.containers = all_sprites, particle_group
Player.containers = all_sprites
Ground.containers = all_sprites
Background.containers = all_sprites
Wall.containers = all_sprites, obstacle_group
BlackCreature.containers = all_sprites, creature_group
Cursor.containers = all_sprites, hud_groud
FPSCounter.containers = all_sprites, hud_groud
HealthIcon.containers = all_sprites, hud_groud, healthbar_group

Player.image = loadify("terro.png", size=-10)
Wall.image = loadify("stonebrick_cracked.png")
Ground.images = [loadify("floor1.png"), loadify("deepslate.png"),loadify("floor3.png"),loadify("floor4.png"),loadify("floor5.png"),loadify("floor6.png")]
BlackCreature.image = loadify("monster.png", size=-30)
Background.image = loadify("background.png", keep_ratio=True, size=2000)
Cursor.image = loadify("cursor.png", size=-20)
HealthIcon.image = loadify("heart.png", size=-25)

background_sprite = Background()

map_grid = abstract_map.grid()

creature_positions = [] # TODO: use layers

for y, row in enumerate(map_grid):
    for x, elem in enumerate(row):
        if elem in ('%', '#', 'x'):
            Ground((x * dpi, y * dpi))
            if elem == 'x':
                creature_positions.append((x * dpi, y * dpi))
        elif elem == '.':
            if check_adjacent(x, y, map_grid):
                Wall((x * dpi, y * dpi))

for pos in creature_positions:
    BlackCreature(pos)
            
player = Player(initial_position=(spawn_point.x * dpi, spawn_point.y * dpi))
camera_x = spawn_point.x * dpi - width / 2 + player.origin_rect.width // 2
camera_y = spawn_point.y * dpi - height / 2 + player.origin_rect.height // 2

Cursor()
FPSCounter()

for i in range(player.health):
    HealthIcon(offset=i)
parts = ParticleEffect(100,100,spawner=screen.get_rect())

while True:
    ticked = clock.tick(60)
    all_sprites.clear(screen, background)
    parts.update(ticked)
    
    all_sprites.update()

    print(f"HP: {player.health}")
    if player.health <= 0:
        player.kill()

    for event in pygame.event.get():
        if event.type == pygame.QUIT: sys.exit()

    keys = pygame.key.get_pressed()
    if keys[pygame.K_z]:
        direction = (0, -1)
        player.move(direction, ticked)
    if keys[pygame.K_q]:
        direction = (-1, 0)
        player.move(direction, ticked)
    if keys[pygame.K_s]:
        direction = (0, 1)
        player.move(direction, ticked)
    if keys[pygame.K_d]:
        direction = (1, 0)
        player.move(direction, ticked)
    parts.draw()
    dirty = all_sprites.draw(screen)
    pygame.display.update(dirty)
    fps = clock.get_fps()
    
