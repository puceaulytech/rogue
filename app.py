import random
import math
import sys
import os
from matplotlib.pyplot import get
import pygame
import mapgen
import itertools
import time

size = width, height = 1280, 720
black = 0, 0, 0
white = 255, 255, 255
fps = 0
ticked = 0
winstyle = 0
fullscreen = False
player = None

pygame.init()

SCREENRECT = pygame.Rect(0, 0, width, height)

bestdepth = pygame.display.mode_ok(SCREENRECT.size, winstyle | pygame.DOUBLEBUF, 32)
screen = pygame.display.set_mode(
    SCREENRECT.size, winstyle | pygame.DOUBLEBUF, bestdepth
)
pygame.display.set_caption("ChadRogue")
pygame.mouse.set_visible(False)
pygame.mixer.music.load("assets/music.ogg")
pygame.mixer.music.play(-1)
clock = pygame.time.Clock()

plane = pygame.Surface((size), pygame.SRCALPHA)
camera_size = 20
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


def rotate_image(image, angle, x, y):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(center=(x, y)).center)
    return rotated_image, new_rect


def translated_rect(rect):
    global camera_x, camera_y
    return pygame.Rect(rect.x - camera_x, rect.y - camera_y, rect.width, rect.height)


def fill_open(x, y, grid):
    if x == 0:
        Wall((-1 * dpi, y * dpi))
    elif x == len(grid[0]):
        Wall((len(grid[0]) * dpi, y * dpi))
    elif y == 0:
        Wall((x * dpi, -1 * dpi))
    elif y == len(grid):
        Wall((x * dpi, len(grid) * dpi))


def check_adjacent(x, y, grid):
    for dx, dy in itertools.product((-1, 0, 1), (-1, 0, 1)):
        if (
            (dx == 0 and dy == 0)
            or (x == 0 and dx == -1)
            or (y == 0 and dy == -1)
            or (x == len(grid[0]) - 1 and dx == 1)
            or (y == len(grid) - 1 and dy == 1)
        ):
            continue
        if grid[y + dy][x + dx] != ".":
            return True
    return False

def get_player_pos_grid():
    return (round(player.origin_rect.x / dpi), round(player.origin_rect.y / dpi))

def move_player_to_spawn():
    global camera_x, camera_y, player
    spawn_point = game_logic.current_map.rooms[0].center

    camera_x = spawn_point.x * dpi - width / 2 + player.origin_rect.width // 2
    camera_y = spawn_point.y * dpi - height / 2 + player.origin_rect.height // 2

    (player.origin_rect.x, player.origin_rect.y) = (spawn_point.x * dpi, spawn_point.y * dpi)

def draw_map():
    for s in mapdependent_group.sprites():
        s.kill()
    mapdependent_group.clear(screen, SCREENRECT)
    mapdependent_group.empty()
    map_grid = game_logic.current_map.grid()

    creature_positions = []  # TODO: use layers

    for y, row in enumerate(map_grid):
        for x, elem in enumerate(row):
            if elem in ("%", "#", "x", "S"):
                Ground((x * dpi, y * dpi))
                fill_open(x, y, map_grid)
                if elem == "S":
                    Stairs((x * dpi, y * dpi))
                elif elem == "x":
                    creature_positions.append((x, y))
            elif elem == ".":
                if check_adjacent(x, y, map_grid):
                    Wall((x * dpi, y * dpi))

    for x, y in creature_positions:
        abstract_creature = list(
            filter(lambda c: c.position == mapgen.Coord(x, y), game_logic.current_map.creatures)
        )[0]
        Creature(
            (x * dpi, y * dpi),
            abstract_creature.id,
            abstract_creature.speed,
            abstract_creature.flying,
        )


def get_adjacent_case(x,y,grid):
    if x > 0 and x < len(grid[0]) and y > 0 and y < len(grid):
        res = []
        res.append(mapgen.Coord(x+1,y))
        res.append(mapgen.Coord(x-1,y))
        res.append(mapgen.Coord(x,y+1))
        res.append( mapgen.Coord(x,y-1))
        return res



def is_case_goodenough(coo,grid): 
    case = grid[coo.x][coo.y]
    if case in ["#", "%", "X","S","x"]:
        return True
    return False

def propagate(start,grid, max_recursive_depth = 5 ):
    visible = [] 
    to_iter = [start]
    to_iter_next = []
    current_recursion = []
    for i in range(max_recursive_depth):
        for j in to_iter:
            
            current_recursion = get_adjacent_case(j.x,j.y,grid)
            
            for k in current_recursion : 
                if k not in visible : 
                    visible.append(k)
                if is_case_goodenough(k,grid):
                    to_iter_next.append(k)
            current_recursion.clear()
        to_iter.clear()
        to_iter = to_iter_next.copy()
        to_iter_next.clear()
    print("visible :" + str(visible))
    return visible
















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
        self.rect = self.image.get_rect().move(
            0 + offset * dpi * 0.8, height - dpi * 0.8
        )


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
        self.image = random.choice(random.choices(self.images, [1, 50, 1, 1, 1, 1]))
        self.origin_rect = self.image.get_rect()
        if initial_position is None:
            initial_position = (0, 0)
        (self.origin_rect.x, self.origin_rect.y) = initial_position

    @property
    def rect(self):
        return translated_rect(self.origin_rect)

    def draw(self, screen):
        screen.blit(self.image, translated_rect(self.origin_rect))

class Stairs(pygame.sprite.Sprite):
    def __init__(self, initial_position=None):
        super().__init__(self.containers)
        self.origin_rect = self.image.get_rect()
        if initial_position is None:
            initial_position = (0, 0)
        (self.origin_rect.x, self.origin_rect.y) = initial_position

    @property
    def rect(self):
        return translated_rect(self.origin_rect)

class InventoryObject(pygame.sprite.Sprite):
    def __init__(self, initial_position, asset):
        super().__init__(self.containers)
        path, size = asset
        self.image = loadify(path, size=size)
        self.picked_up = False
        self.origin_rect = self.image.get_rect()
        (self.origin_rect.x, self.origin_rect.y) = initial_position

    @property
    def rect(self):
        return translated_rect(self.origin_rect)

    def move(self, direction, delta_time):
        direction = tuple([round(delta_time * c) for c in direction])
        self.rect.move_ip(inverse_direction(direction))


class Weapon(InventoryObject):
    def __init__(self, initial_position, asset, attack_cooldown, durability):
        super().__init__(initial_position, asset)
        self.attack_cooldown = attack_cooldown
        self.last_attack = 0
        self.durability = durability


class Potion(InventoryObject):
    def __init__(self, initial_position, asset):
        super().__init__(initial_position, asset)


class Spell(InventoryObject):
    def __init__(self, initial_position, asset):
        super().__init__(initial_position, asset)


class Sword(Weapon):
    def __init__(self, initial_position):
        super().__init__(
            initial_position,
            asset=("sword.png", 40),
            attack_cooldown=2,
            durability=math.inf,
        )


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
        for inventory_object in pygame.sprite.spritecollide(
            self, inventoryobject_group, False
        ):
            inventory_object.picked_up = True
        for stair_object in pygame.sprite.spritecollide(self, stairs_group, False):
            game_logic.move_up()
            draw_map()
            move_player_to_spawn()
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


class Particle:
    def __init__(self, coords, image=None, radius=None, lifetime=200):

        self.lifetime = lifetime

        self.image = image
        self.radius = radius
        if image != None:
            self.rect = self.image.get_rect()
            (self.rect.x, self.rect.y) = coords
        else:
            self.rect = pygame.Rect(coords, (radius, radius))

    def __repr__(self):
        return f"Particle at {(self.rect.x,self.rect.y)} with {self.lifetime} remaining , radius = {self.radius}, image = {self.image}"

    def move(self, direction_x, direction_y):
        self.rect.move_ip((direction_x, direction_y))

    def draw(self):
        if self.image != None:
            plane.blit(self.image, self.rect)
        else:
            pygame.draw.circle(
                plane,
                (255, 255, 255, self.lifetime),
                radius=random.randint(1, 3),
                center=(self.rect.x, self.rect.y),
            )


"""self.lifetime"""
"""self.radius"""


class ParticleEffect:
    def __init__(
        self, number=100, lifetime=200, images=None, forces=None, spawner=None
    ):
        self.number = number
        self.images = images or None
        self.forces = forces
        self.spawner = spawner
        self.lifetime = lifetime

        self.particle_list = []
        """
        for i in range(number):
            x = random.randint(spawner.x, spawner.width + spawner.x)
            y = random.randint(spawner.y, spawner.height + spawner.y)
            self.particle_list.append(
                Particle(
                    (x, y),self.images,10, self.lifetime + random.randint(-20, 20)
                )
            )
"""

    def update(self, delta):
        if len(self.particle_list) < self.number - 5:
            for j in range(random.randint(0, 1)):
                x = random.randint(self.spawner.x, self.spawner.width + self.spawner.x)
                y = random.randint(self.spawner.y, self.spawner.height + self.spawner.y)
                self.particle_list.append(
                    Particle(
                        (x, y), self.images, 10, self.lifetime + random.randint(-20, 20)
                    )
                )
        for i in range(len(self.particle_list)):
            if self.forces:
                x_delta = random.randint(-100,100) / 500
                y_delta = random.randint(-100,100) / 500
                self.particle_list[i].move(
                    (self.forces[0]+x_delta) * delta , (self.forces[1]+y_delta) * delta
                )
            self.particle_list[i].lifetime -= 1
            if self.particle_list[i].lifetime == 0:
                self.particle_list.pop(i)
                x = random.randint(self.spawner.x, self.spawner.width + self.spawner.x)
                y = random.randint(self.spawner.y, self.spawner.height + self.spawner.y)
                self.particle_list.append(
                    Particle(
                        (x, y), self.images, 10, self.lifetime + random.randint(-20, 20)
                    )
                )
            self.particle_list[i].draw()


class Creature(pygame.sprite.Sprite):
    def __init__(self, initial_position, assets, speed=0.1, flying=False):
        self.local_frame_index = random.randint(0, 100000)
        super().__init__(self.containers)
        self.health = 3
        self.flying = flying
        self.speed = speed
        self.last_attack = 0
        self.attack_cooldown = 1
        self.images = []
        self.currimage = 0
        for i in range(len(assets)):
            self.images.append(loadify(assets[i], 10, keep_ratio=True))
        self.image = self.images[self.currimage]
        self.origin_rect = self.image.get_rect()
        (self.origin_rect.x, self.origin_rect.y) = initial_position

    @property
    def rect(self):
        return translated_rect(self.origin_rect)

    def update(self):
        self.local_frame_index += 1
        if len(self.images) != 1:
            if self.local_frame_index % 20 == 0:
                self.currimage += 1
                if (self.currimage) >= len(self.images):
                    self.currimage = 0
                self.image = self.images[self.currimage]
        distance_to_player = math.sqrt(
            (self.origin_rect.x - player.origin_rect.x) ** 2
            + (self.origin_rect.y - player.origin_rect.y) ** 2
        )
        if distance_to_player < 5 * dpi:
            dx = (player.origin_rect.x - self.origin_rect.x) / (
                distance_to_player + 0.000001
            )
            dy = (player.origin_rect.y - self.origin_rect.y) / (
                distance_to_player + 0.000001
            )
            self.move((dx, dy), ticked)
            if (
                pygame.sprite.collide_rect(player, self)
                and time.time() - self.last_attack > self.attack_cooldown
            ):
                player.health -= 1
                if not player.health < 0:  # TODO: juste pour éviter le crash
                    healthbar_group.sprites()[-1].kill()
                self.last_attack = time.time()

    def move(self, direction, delta_time):
        direction = tuple([round(self.speed * delta_time * c) for c in direction])
        self.origin_rect.move_ip(direction)
        if not self.flying and any(
            pygame.sprite.spritecollide(self, obstacle_group, False)
        ):
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


game_logic = mapgen.Game(max_levels=3)
game_logic.current_map.display()


background = pygame.Surface(size)
pygame.display.flip()

all_sprites = pygame.sprite.LayeredUpdates()
mapdependent_group = pygame.sprite.Group()
stairs_group = pygame.sprite.Group()
obstacle_group = pygame.sprite.Group()
creature_group = pygame.sprite.Group()
hud_groud = pygame.sprite.Group()
healthbar_group = pygame.sprite.Group()
particle_group = pygame.sprite.Group()
inventoryobject_group = pygame.sprite.Group()

Player.containers = all_sprites
InventoryObject.containers = all_sprites, inventoryobject_group, mapdependent_group
Ground.containers = all_sprites, mapdependent_group
Stairs.containers = all_sprites, mapdependent_group, stairs_group
Background.containers = all_sprites
Wall.containers = all_sprites, obstacle_group, mapdependent_group
Creature.containers = all_sprites, creature_group, mapdependent_group
Cursor.containers = all_sprites, hud_groud
FPSCounter.containers = all_sprites, hud_groud
HealthIcon.containers = all_sprites, hud_groud, healthbar_group


Player.image = loadify("terro.png", size=-10)
Wall.image = loadify("stonebrick_cracked.png")
Ground.images = [
    loadify("floor1.png"),
    loadify("deepslate.png"),
    loadify("floor3.png"),
    loadify("floor4.png"),
    loadify("floor5.png"),
    loadify("floor6.png"),
]
Stairs.image = loadify("portal.png", size=20)
Background.image = loadify("background.png", keep_ratio=True, size=2000)
Cursor.image = loadify("cursor.png", size=10)
HealthIcon.image = loadify("heart.png", size=-25)

Player._layer = 2
Wall._layer = 1
Ground._layer = 1
Stairs._layer = 2
Background._layer = 0
Cursor._layer = 2
FPSCounter._layer = 2
HealthIcon._layer = 2
Creature._layer = 2

background_sprite = Background()

player = Player(initial_position=(0, 0))

draw_map()

move_player_to_spawn()

Cursor()
FPSCounter()

for i in range(player.health):
    HealthIcon(offset=i)
particle_system = ParticleEffect(100,200,spawner=screen.get_rect(),forces= [0.1,0.05])
frame_index = 0
player_grid_pos = get_player_pos_grid()
print(propagate(mapgen.Coord(player_grid_pos[0],player_grid_pos[1]),game_logic.current_map.grid()))
###########################################   MAIN LOOP  ###########################################
while True:
    frame_index += 1
    if frame_index % 5 == 0:
        pass
        plane.fill((0,0,0,0))
    ticked = clock.tick(360)
    all_sprites.clear(screen, background)

    all_sprites.update()

    if player.health <= 0:
        player.kill()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_e:
                game_logic.move_up()
                draw_map()
                move_player_to_spawn()
            elif event.key == pygame.K_f:
                if not fullscreen:
                    screen_backup = screen.copy()
                    screen = pygame.display.set_mode(
                        SCREENRECT.size,
                        winstyle | pygame.FULLSCREEN | pygame.DOUBLEBUF,
                        bestdepth,
                    )
                    screen.blit(screen_backup, (0, 0))
                else:
                    screen_backup = screen.copy()
                    screen = pygame.display.set_mode(
                        SCREENRECT.size, winstyle | pygame.DOUBLEBUF, bestdepth
                    )
                    screen.blit(screen_backup, (0, 0))
                pygame.display.flip()
                fullscreen = not fullscreen

    keys = pygame.key.get_pressed()
    if keys[pygame.K_ESCAPE]:
        sys.exit(0)
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

    dirty = all_sprites.draw(screen)
    particle_system.update(ticked)
    screen.blit(plane,(0,0))
    pygame.display.update(dirty)

    print(get_player_pos_grid())

    fps = clock.get_fps()
