from hashlib import new
import random
import math
import sys
import os
import pygame
import mapgen
import itertools
import time

size = width, height = 1920, 1080
black = 0, 0, 0
white = 255, 255, 255
fps = 0
ticked = 0
winstyle = 0
fullscreen = False

pygame.init()

SCREENRECT = pygame.Rect(0, 0, width, height)

bestdepth = pygame.display.mode_ok(SCREENRECT.size, winstyle | pygame.DOUBLEBUF, 32)
screen = pygame.display.set_mode(SCREENRECT.size, winstyle | pygame.DOUBLEBUF, bestdepth)
pygame.display.set_caption("ChadRogue")
pygame.mouse.set_visible(False)
pygame.mixer.music.load("assets/music.ogg")
pygame.mixer.music.play(-1)
clock = pygame.time.Clock()

plane = pygame.Surface((size), pygame.SRCALPHA)
camera_size = 14
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












class Particle():
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
    def move(self, direction_x,direction_y):
        self.rect.move_ip((direction_x,direction_y))

    def draw(self):
        if self.image != None:
            plane.blit(self.image, self.rect)
        else:
            pygame.draw.circle(
                plane,
                (255, 255, 255, self.lifetime),
                radius=random.randint(1,3),
                center=(self.rect.x, self.rect.y),
            )
"""self.lifetime"""
"""self.radius""",
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
        if len(self.particle_list) < self.number-10 :
            for j in range(random.randint(0,1)):
                x = random.randint(self.spawner.x, self.spawner.width + self.spawner.x)
                y = random.randint(self.spawner.y, self.spawner.height + self.spawner.y)
                self.particle_list.append(Particle(
                    (x, y), self.images, 10, self.lifetime + random.randint(-20, 20)
                ))
        for i in range(len(self.particle_list)):
            if self.forces:
                self.particle_list[i].move(self.forces[0] * delta,self.forces[1]* delta)
            self.particle_list[i].lifetime -= 1
            if self.particle_list[i].lifetime == 0:
                self.particle_list.pop(i)
                x = random.randint(self.spawner.x, self.spawner.width + self.spawner.x)
                y = random.randint(self.spawner.y, self.spawner.height + self.spawner.y)
                self.particle_list.append(Particle(
                    (x, y), self.images, 10, self.lifetime + random.randint(-20, 20)
                ))
            self.particle_list[i].draw()














class Creature(pygame.sprite.Sprite):
    def __init__(self, initial_position, asset, speed=0.1):
        super().__init__(self.containers)
        self.health = 3
        self.speed = speed
        self.last_attack = 0
        self.attack_cooldown = 1
        self.image = loadify(asset, size=-30)
        self.origin_rect = self.image.get_rect()
        (self.origin_rect.x, self.origin_rect.y) = initial_position

    @property
    def rect(self):
        return translated_rect(self.origin_rect)

    def update(self):
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
inventoryobject_group = pygame.sprite.Group()

Player.containers = all_sprites
InventoryObject.containers = all_sprites, inventoryobject_group
Ground.containers = all_sprites
Background.containers = all_sprites
Wall.containers = all_sprites, obstacle_group
Creature.containers = all_sprites, creature_group
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
Background.image = loadify("background.png", keep_ratio=True, size=2000)
Cursor.image = loadify("cursor.png", size=10)
HealthIcon.image = loadify("heart.png", size=-25)

background_sprite = Background()

map_grid = abstract_map.grid()

creature_positions = []  # TODO: use layers

for y, row in enumerate(map_grid):
    for x, elem in enumerate(row):
        if x in (0, len(row) - 1) or y in (0, len(map_grid) - 1):
            Wall((x * dpi, y * dpi))
        elif elem in ("%", "#", "x"):
            Ground((x * dpi, y * dpi))
            if elem == "x":
                creature_positions.append((x, y))
        elif elem == ".":
            if check_adjacent(x, y, map_grid):
                Wall((x * dpi, y * dpi))

for x, y in creature_positions:
    abstract_creature = list(
        filter(lambda c: c.position == mapgen.Coord(x, y), abstract_map.creatures)
    )[0]
    Creature((x * dpi, y * dpi), abstract_creature.id, abstract_creature.speed)

player = Player(initial_position=(spawn_point.x * dpi, spawn_point.y * dpi))
camera_x = spawn_point.x * dpi - width / 2 + player.origin_rect.width // 2
camera_y = spawn_point.y * dpi - height / 2 + player.origin_rect.height // 2

Cursor()
FPSCounter()
Sword((spawn_point.x * dpi, spawn_point.y * dpi))

for i in range(player.health):
    HealthIcon(offset=i)
particle_system = ParticleEffect(100,200,spawner=screen.get_rect(),forces= [0,-0.1])
frame_index = 0
###########################################   MAIN LOOP  ###########################################
while True:
    frame_index+=1
    if frame_index%5 == 0:

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
            if event.key == pygame.K_f:
                if not fullscreen:
                    screen_backup = screen.copy()
                    screen = pygame.display.set_mode(
                        SCREENRECT.size, winstyle | pygame.FULLSCREEN | pygame.DOUBLEBUF, bestdepth
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

    
    fps = clock.get_fps()
