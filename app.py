
import random
from collections import defaultdict
import math
import sys
import os


import pygame
import mapgen
import itertools
import time
import abc

size = width, height = 1280, 720
black = 0, 0, 0
white = 255, 255, 255
fps = 0
ticked = 0
winstyle = 0
fullscreen = False
player = None
dialog = None

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

hit_sound = pygame.mixer.Sound("assets/hitted.ogg")
clock = pygame.time.Clock()

plane = pygame.Surface((size), pygame.SRCALPHA)
camera_size = 20
camera_x, camera_y = 0, 0

dpi = width / camera_size


already_drawn = []

def loadify(path, size=0, keep_ratio=False, keep_size=False):
    global dpi
    good_path = os.path.join("assets", path)
    image = pygame.image.load(good_path).convert_alpha()
    if keep_size:
        return image
    ratio = image.get_width() / image.get_height() if keep_ratio else 1
    return pygame.transform.scale(image, ((dpi + size) * ratio, dpi + size))

def sign(x):
    if x == 0:
        return 0
    elif x > 0:
        return 1
    elif x < 0:
        return -1


def inverse_direction(direction):
    return (-direction[0], -direction[1])
def get_angle(x1,x2,y1,y2):
    dx = x1-x2
    dy = y1-y2
    return((math.atan2( -dy,dx) * 180 /math.pi)-90)

def rotate_image(image, angle):
    rotated_image = pygame.transform.rotate(image, angle)
    
    return rotated_image

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
    center = player.origin_rect.center
    return (math.floor(center[0] / dpi), math.floor(center[1] / dpi))

def get_creature_pos_grid(creature):
    center = creature.origin_rect.center
    return (math.floor(center[0] / dpi), math.floor(center[1] / dpi))

def move_player_to_spawn():
    global camera_x, camera_y, player
    spawn_point = game_logic.current_map.rooms[0].center

    camera_x = spawn_point.x * dpi - width / 2 + player.origin_rect.width // 2
    camera_y = spawn_point.y * dpi - height / 2 + player.origin_rect.height // 2

    (player.origin_rect.x, player.origin_rect.y) = (spawn_point.x * dpi, spawn_point.y * dpi)

def update_map_near_player():
    player_grid_pos = get_player_pos_grid()
    coords = propagate(mapgen.Coord(player_grid_pos[0], player_grid_pos[1]), map_grid)
    for c in coords:
        x, y = c
        elem = game_logic.current_map.get_character_at(c)

        if elem in ("%", "#", "x", "S","w","L","P", "T", "€"):
            if (x, y) not in already_drawn:
                g = Ground((x * dpi, y * dpi), trapped=(elem == "T"))
                if elem == "S":
                    Stairs((x * dpi, y * dpi))
                elif elem == "€":
                    Treasure(game_logic.current_map.treasure.item, (x * dpi, y * dpi))
                elif elem == "T":
                    traps_group.add(g)
                already_drawn.append((x, y))
        elif elem == ".":
            if (x, y) not in already_drawn:
                Wall((x * dpi, y * dpi))
                already_drawn.append((x, y))

    for creature in creature_group.sprites():
        if get_creature_pos_grid(creature) in already_drawn:
            all_sprites.add(creature)
        else:
            all_sprites.remove(creature)

    for item in inventoryobject_group.sprites():
        if get_creature_pos_grid(item) in already_drawn:
            all_sprites.add(item)
        else:
            all_sprites.remove(item)


def draw_map():
    global map_grid
    for s in mapdependent_group.sprites():
        s.kill()
    mapdependent_group.clear(screen, SCREENRECT)
    mapdependent_group.empty()
    map_grid = game_logic.current_map.grid()
    already_drawn.clear()

    for y, row in enumerate(map_grid):
        for x, elem in enumerate(row):
            if elem == "x":
                for abstract_creature in game_logic.current_map.creatures:
                    if abstract_creature.position == mapgen.Coord(x, y):
                        c = Creature(
                            (x * dpi, y * dpi),
                            abstract_creature.id,
                            abstract_creature.speed,
                            abstract_creature.flying,
                            key = abstract_creature.has_key
                        )
                        c.health_bar = CreatureHealthBar()
                        c.health_bar.creature = c
            elif elem == "w":
                for abstract_weapon in game_logic.current_map.weapon:
                    if abstract_weapon.position == mapgen.Coord(x, y):
                        Weapon(
                            (x * dpi, y * dpi),
                            id=abstract_weapon.id,
                            subid=abstract_weapon.sub_id,
                            durability=abstract_weapon.durability,
                            damage=abstract_weapon.damage,
                            reach=abstract_weapon.reach,
                            attack_cooldown=abstract_weapon.attack_cooldown
                        )
            elif elem == "L":
                for abstract_spell in game_logic.current_map.spell:
                    if abstract_spell.position == mapgen.Coord(x,y):
                        Spell(
                            (x*dpi,y*dpi),
                            id=abstract_spell.id,
                            subid=abstract_spell.sub_id,
                            damage=abstract_spell.damage,
                            radius=abstract_spell.radius,
                            speed=abstract_spell.speed,
                            attack_cooldown=abstract_spell.attack_cooldown
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
    case = grid[coo.y][coo.x]
    if case in ["#", "%","S","x","w","L","P", "€"]:
        return True
    return False

def propagate(start,grid, max_recursive_depth = 5 ):


    visible = [] 
    to_iter = [start]
    to_iter_next = []
    current_recursion = []
    already_itered = []
    for i in range(max_recursive_depth):
        for j in to_iter:
            current_recursion = get_adjacent_case(j.x,j.y,grid)
            
            for k in current_recursion : 
                if k not in visible : 
                    visible.append(k)
                if is_case_goodenough(k,grid) and k not in already_itered:
                    to_iter_next.append(k)
            current_recursion.clear()
        already_itered.extend(to_iter_next)
        to_iter.clear()
        to_iter = to_iter_next.copy()
        to_iter_next.clear()

    return visible


def get_neighbours(position):
    x, y = position
    return [
        (x+1, y),
        (x-1, y),
        (x, y+1),
        (x, y-1)
    ]


def bfs(creature, grid):
    start = get_creature_pos_grid(creature)
    goal = get_player_pos_grid()

    queue = [start]
    visited = [start]
    parents = defaultdict(lambda: None)

    while len(queue) != 0:
        current = queue.pop(0)

        if current == goal:
            path = []
            while current:
                path.insert(0, current)
                current = parents[current]
            return path

        neighbours = get_neighbours(current)
        for n in neighbours:
            if is_case_goodenough(mapgen.Coord(n[0], n[1]), grid) and n not in visited:
                visited.append(n)
                parents[n] = current
                queue.append(n)

class Mask(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(self.containers)
        self.image = loadify("mask.png", keep_ratio=True, keep_size=True)
        self.rect = self.image.get_rect()
        (self.rect.x, self.rect.y) = (0, 0)

class Animation:
    def __init__(self, spritelist, rate): 
        self.spritelist = spritelist
        self.rate = rate
        self.frame_index = 0 
        self.curr_sprite = 0
    def update_animation(self,frame):
        if frame % self.rate == 0:
            self.curr_sprite += 1 
        if self.curr_sprite >= len(self.spritelist):
            self.curr_sprite = 0
        return self.spritelist[self.curr_sprite]
    def rotate_animation(self,frame):
        if frame % self.rate == 0:
            print('roted')
            img = rotate_image(self.spritelist[self.curr_sprite],45)
            return img
        else : return self.spritelist[self.curr_sprite]
class FPSCounter(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(self.containers)
        self.font = pygame.font.Font("assets/Retro_Gaming.ttf", 20)
        self.color = "white"
        self.update()
        self.rect = self.image.get_rect().move(0, 0)

    def update(self):
        self.image = self.font.render(f"FPS: {round(fps)}", False, self.color)

class Dialog(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(self.containers)
        self.font = pygame.font.Font("assets/Retro_Gaming.ttf", 20)
        self.color = "red"
        self.message = ""
        self.update()
        self.origin_rect = self.image.get_rect().move(width / 2, 0)

    @property
    def rect(self):
        return translated_rect(self.origin_rect)

    def move(self, coord):
        (self.origin_rect.x, self.origin_rect.y) = coord

    def update(self):
        self.image = self.font.render(self.message, False, self.color)


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
    def __init__(self, initial_position=None, trapped=False):
        super().__init__(self.containers)
        self.image = random.choice(random.choices(self.images, [1, 50, 1, 1, 1, 1]))
        self.origin_rect = self.image.get_rect()
        self.trapped = trapped
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

class Treasure(pygame.sprite.Sprite):
    def __init__(self, item, initial_position=None):
        super().__init__(self.containers)
        self.origin_rect = self.image.get_rect()
        if initial_position is None:
            initial_position = (0, 0)
        (self.origin_rect.x, self.origin_rect.y) = initial_position
        self.item = item

    @property
    def rect(self):
        return translated_rect(self.origin_rect)

class InventoryObject(pygame.sprite.Sprite,metaclass=abc.ABCMeta):
    def __init__(self, initial_position):
        super().__init__(self.containers)
        self.picked_up = False
        self.origin_rect = self.image.get_rect()
        (self.origin_rect.x, self.origin_rect.y) = initial_position

    def __bool__(self):
      return True

    @property
    def rect(self):
        return self.origin_rect if self in player_inv_group.sprites() else translated_rect(self.origin_rect)

    def move(self, direction, delta_time):
        direction = tuple([round(delta_time * c) for c in direction])
        self.rect.move_ip(inverse_direction(direction))

    def update(self):
        if pygame.sprite.collide_rect(player, self):
            offset = player.inventory.first_empty_slot()
            if player.take(self):
                self.kill()
                self.origin_rect = pygame.Rect(player_inv_group.sprites()[offset].rect[0:2],self.rect[2:4])
                self.image = pygame.transform.scale(self.image,(40,40))
                player_inv_group.add(self)

    @abc.abstractmethod
    def use(self):
        pass
class Projectile(pygame.sprite.Sprite):
    def __init__(self,position,sprites,speed,direction,dmg,particle = None):
        super().__init__(self.containers)
        
        self.speed = speed
        self.direction = direction
        self.dmg = dmg

        angle = math.atan2(self.direction[0],self.direction[1])
        angle = angle * (180/math.pi)
        rot_sprites = []
        for i in sprites : 
            rot_sprites.append(rotate_image(i,angle+180+45))
        self.sprites = rot_sprites
        self.anim = Animation(self.sprites,2)
        self.image = self.anim.update_animation(0)
        self.origin_rect = self.image.get_rect()
        self.origin_rect.center = position
        if particle != None : 
            self.has_particles = True
            self.particle_sys = ParticleEffect(100,200,None,[0,0.1],translated_rect(self.origin_rect),color = (255,200,0))
        else : 
            self.has_particles = False
        self.frame_index = 0
    @property
    def rect(self):
        return translated_rect(self.origin_rect)
    def update(self):
        if self.has_particles : 
            self.particle_sys.spawner = self.rect
            self.particle_sys.update(ticked)
        self.frame_index+=1

        self.image = self.anim.update_animation(self.frame_index)
        self.move(self.direction,ticked)
        colliding_creatures = pygame.sprite.spritecollide(self,creature_group,False)
        if len(colliding_creatures) != 0  : 
            colliding_creatures[0].health -= self.dmg
            self.kill()
        colliding_walls = []
        for i in obstacle_group.sprites():
            if i.origin_rect.collidepoint(self.origin_rect.center):
                colliding_walls.append(i)

        if len(colliding_walls) != 0 : 
            self.kill()
        if mapgen.Coord(player.origin_rect.center[0],player.origin_rect.center[1]).distance(mapgen.Coord(self.origin_rect.center[0],self.origin_rect.center[1])) > 20*dpi : 
            self.kill()
    def move(self,direction,delta_time):
        direction = tuple([round(self.speed * delta_time * c) for c in direction])
        self.origin_rect.move_ip(direction[0],direction[1])






class Weapon(InventoryObject):
    def __init__(self, initial_position, id, subid, durability, damage, reach, attack_cooldown):
        self.id = id
        self.durability = durability
        self.attack_cooldown = attack_cooldown
        self.subid = subid
        self.damage = damage
        self.reach = reach * dpi
        if self.id == "sword":
            self.image = loadify("sword.png", 10, True) 
            if subid == "diamond_sword" : 
                self.image = loadify("diamond_sword.png", 10, True) 
            if subid == "emerald_sword" : 
                self.image = loadify("emerald_sword.png", 10, True) 
            if subid == "amber_sword" : 
                self.image = loadify("amber_sword.png", 10, True) 
        if self.id == "bow":
            self.image = loadify("bow.png", 10, True) 
        self.last_attack = 0
        super().__init__(initial_position)

    def use(self):
        if not (time.time() - self.last_attack > self.attack_cooldown):
            return
        if self.id == "sword":
            pos = pygame.mouse.get_pos()
            cos45 = 1 / math.sqrt(2)
            mouse_cos = (pos[0] - player.rect.center[0]) / math.sqrt((pos[0] - player.rect.center[0])**2 + (pos[1] - player.rect.center[1])**2)
            for creature in creature_group.sprites():
                distance = math.sqrt((creature.rect.center[0] - player.rect.center[0])**2 + (creature.rect.center[1] - player.rect.center[1])**2)
                cos = (creature.rect.center[0] - player.rect.center[0]) / distance
                if (
                    (cos > cos45 and mouse_cos > cos45)
                    or (cos < -cos45 and mouse_cos < -cos45)
                    or (creature.rect.center[1] > player.rect.center[1] and pos[1] > player.rect.center[1])
                    or (creature.rect.center[1] <= player.rect.center[1] and pos[1] <= player.rect.center[1])
                ) and distance <= self.reach:
                    creature.health -= self.damage
                    
        if self.id == "bow":
            mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
            player_pos = pygame.math.Vector2(player.rect.center)
            direction = (mouse_pos - player_pos).normalize()
            Projectile(player.origin_rect.center,[loadify("arrow.png",-35,True)],1,direction, self.damage)

        self.last_attack = time.time()

class Key(InventoryObject):
    def __init__(self, initial_position):
        self.image = loadify("key.png", 5, True)
        super().__init__(initial_position)

    def use(self):
        self.kill()
        player.inventory.remove(self)

class Potion(InventoryObject):
    def __init__(self, initial_position):
        super().__init__(initial_position)

class Spell(InventoryObject):
    def __init__(self, initial_position, id, subid, damage, radius, speed, attack_cooldown):
        self.id = id 
        self.subid = subid
        self.damage = damage
        self.radius = radius
        self.speed = speed
        self.attack_cooldown = attack_cooldown
        if self.id == "fireball" : 
            self.image = loadify("fireball_spell.png",10,True)
            #self.origin_rect = self.image.get_rect()
        self.last_attack = 0
        super().__init__(initial_position)
    def use(self):
        if not (time.time() - self.last_attack > self.attack_cooldown):
            return
        if self.id == "fireball":
            mouse_pos = pygame.math.Vector2(pygame.mouse.get_pos())
            player_pos = pygame.math.Vector2(player.rect.center)
            direction = (mouse_pos - player_pos).normalize()
            Projectile(player.origin_rect.center,[loadify("fireball.png",-25,True)],1,direction, self.damage,particle=1)
        self.last_attack = time.time()


class Player(pygame.sprite.Sprite):
    speed = 0.35
    inventory_size = 8

    def __init__(self, initial_position=None):
        super().__init__(self.containers)
        self.images = [loadify(i, size=-10) for i in self.assets]
        self.currimage = 0
        self.image = self.images[self.currimage]
        self.health = 8
        self.origin_rect = self.image.get_rect(center=SCREENRECT.center)
        self.last_trapped = 0
        if initial_position is not None:
            (self.origin_rect.x, self.origin_rect.y) = initial_position
        self.inventory = Inventory([None for i in range(Player.inventory_size)])

    def take_damage(self, amount):
        player.health -= amount
        hit_sound.play()
        for _ in range(amount):
            if not player.health < 0:  # TODO: juste pour éviter le crash
                healthbar_group.sprites()[-1].kill()

    def move(self, direction, delta_time):
        global camera_x, camera_y
        origin_direction = direction
        direction = tuple([round(self.speed * delta_time * c) for c in direction])
        camera_x += direction[0]
        camera_y += direction[1]
        self.origin_rect.move_ip(direction)
        background_sprite.move(origin_direction, delta_time)
        dialog.message = ""
        for stair_object in pygame.sprite.spritecollide(self, stairs_group, False):
            dialog.message = "Press E to go up"
            dialog.move((stair_object.origin_rect.x, stair_object.origin_rect.y - 0.5 * dpi))
        for treasure_object in pygame.sprite.spritecollide(self, treasures_group, False):
            if isinstance(self.inventory.picked_item,Key):
                item = treasure_object.item
                if isinstance(treasure_object.item,mapgen.Weapon):
                    Weapon(treasure_object.origin_rect[:2],item.id, subid=item.sub_id, durability=item.durability, damage=item.damage, reach=item.reach, attack_cooldown=item.attack_cooldown)
                elif isinstance(treasure_object.item,mapgen.Spell):
                    Spell(treasure_object.origin_rect[:2],treasure_object.item.id, subid=item.sub_id, damage=item.damage, radius=item.radius, speed=item.speed, attack_cooldown=item.attack_cooldown)
                all_sprites.remove(treasure_object)
                treasures_group.remove(treasure_object)
                self.inventory.picked_item.use()
        if any(pygame.sprite.spritecollide(self, traps_group, False)):
            if time.time() - self.last_trapped > 5:
                self.take_damage(1)
                self.last_trapped = time.time()
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

    def update(self):
        if any(list(i.picked_up for i in self.inventory if i is not None)):
            self.currimage = 1
        else:
            self.currimage = 0
        self.image = self.images[self.currimage]

    def take(self,thing):
     if isinstance(thing,InventoryObject):
       return self.inventory.add(thing)
     raise TypeError("Not an item")

class Text(pygame.sprite.Sprite):
    def __init__(self, text, color, position):
        super().__init__(self.containers)
        self.text = str(text)
        self.color = color
        self.font = pygame.font.Font("assets/Retro_Gaming.ttf",30)
        self.image = self.font.render(self.text, False, self.color)
        self.rect = self.image.get_rect(topleft = position)

class Stats_gui:
    def __init__(self,item):
        self.attributes = []
        self.update(item)

    def update(self, item):
        self.kill()
        if item:
            if isinstance(item,Weapon) or isinstance(item,Spell):
                self.name = Text(item.id, (0,0,0), (width - 4*dpi,height - 3*dpi))
                self.damage = Text(item.damage, (0,0,0), (width - 4*dpi,height - 2*dpi))
                self.other = Text(item.durability, (0,0,0), (width - 4*dpi,height - dpi)) if isinstance(item,Weapon) else Text(item.radius, (0,0,0), (width - 4*dpi,height - dpi))
                self.attributes = [self.name, self.damage, self.other]
                 
    def kill(self):
        for i in self.attributes:
            i.kill()
            del i
        self.attributes = []

class InvSlot(pygame.sprite.Sprite):
    def __init__(self, offset, total_nb):
        super().__init__(self.containers)
        self.has_picked_item = False
        self.image = loadify("slot.png", size=-20)
        center_p = (width/2,height-2)
        self.rect = self.image.get_rect(center = center_p)
        self.rect.move_ip(self.rect[2]*(offset - total_nb//2),-self.rect[3]/2)
        if total_nb%2 == 0:
            self.rect.move_ip(self.rect[2]/2,0)

    def update(self):
        self.image = loadify("selected_slot.png", size=-20) if self.has_picked_item else loadify("slot.png", size=-20)

class Inventory:
    def __init__(self,items):
        self.items = items
        self.size = len(self.items)
        for i in range(self.size):
            InvSlot(i, self.size)
        self.gui = Stats_gui(self.picked_item)

    def __repr__(self):
        return str(self.items)

    def __getitem__(self,key):
        return self.items[key]

    def __setitem__(self,key,value):
        self.items[key] = value
    
    def has_empty_slot(self):
        return None in self.items

    def first_empty_slot(self):
        return min(list(i for i in range(len(self.items)) if self[i] is None)) if self.has_empty_slot() else None

    def add(self,thing):
        if self.has_empty_slot():
            self[self.first_empty_slot()] = thing
            return True
        return False

    def remove(self,thing):
        i = self.items.index(thing)
        self.items[i] = None

    def update(self):
        self.gui.update(self.picked_item)
        for i in player_inv_group.sprites():
            all_sprites.add(i)
        [x.update() for x in player_inv_group.sprites() if isinstance(x, InvSlot)]

    @property
    def picked_item(self):
        picked_items = [x for x in self.items if x is not None and x.picked_up]
        return picked_items[0] if picked_items else None

    @property
    def picked_item_index(self):
        return self.items.index(self.picked_item) if self.picked_item else None

class Particle:
    def __init__(self, coords, image=None, radius=None, lifetime=200,color = (255,255,255)):

        self.lifetime = lifetime
        self.color = color 
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
                (self.color[0], self.color[1],self.color[2], self.lifetime),
                radius=random.randint(1, 3),
                center=(self.rect.x, self.rect.y),
            )


"""self.lifetime"""
"""self.radius"""


class ParticleEffect:
    def __init__(
        self, number=100, lifetime=200, images=None, forces=None, spawner=None , color = (255,255,255)
    ):
        self.number = number
        self.images = images or None
        self.forces = forces
        self.spawner = spawner
        self.lifetime = lifetime
        self.color = color
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
                        (x, y), self.images, 10, self.lifetime + random.randint(-20, 20),color=self.color
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
                        (x, y), self.images, 10, self.lifetime + random.randint(-20, 20),color=self.color
                    )
                )
            self.particle_list[i].draw()


class Creature(pygame.sprite.Sprite):
    def __init__(self, initial_position, assets, speed=0.1, flying=False, hp = None, key = False):
        self.local_frame_index = random.randint(0, 100000)
        super().__init__(self.containers)
        self.angle = 0
        self.max_health = hp or random.randint(3, 10)
        self.health = self.max_health
        self.flying = flying
        self.speed = speed + random.randint(-100,100)/1000
        self.last_attack = 0
        self.attack_cooldown = 1
        self.images = []
        self.currimage = 0
        self.path_to_player = []
        self.collisions_rect = []
        self.direction = (0, 0)
        self.has_key = key
        
        for i in range(len(assets)):
            self.images.append(loadify(assets[i], size=-30, keep_ratio=True))
        self.anim = Animation(self.images,20)
        self.image = self.anim.update_animation(1)
        self.origin_rect = self.image.get_rect(center=initial_position)
    @property
    def rect(self):
        return translated_rect(self.origin_rect)


    def update(self):
        if self.health <= 0:
            self.kill()
            self.health_bar.kill()
            if self.has_key:
                Key(self.origin_rect[:2])
        
        self.local_frame_index += 1
        self.image = self.anim.update_animation(self.local_frame_index)
        

        distance_to_player = math.sqrt(
            (self.origin_rect.x - player.origin_rect.x) ** 2
            + (self.origin_rect.y - player.origin_rect.y) ** 2
        )
        if distance_to_player < 10 * dpi:
            self.path_to_player = bfs(self, map_grid)
            if self.path_to_player is not None and len(self.path_to_player) > 1:
                if (self.direction[0] == 0 and self.direction[1] == 0) or any([rect.collidepoint(self.origin_rect.center) for rect in self.collisions_rect]):
                    self.collisions_rect.clear()
                    for point in self.path_to_player[1:]:
                        x = (point[0] * dpi) + dpi / 2
                        y = (point[1] * dpi) + dpi / 2
                        rect = pygame.Rect((x - 7, y - 7), (14, 14))
                        self.collisions_rect.append(rect)
                    start = pygame.math.Vector2(self.origin_rect.center)
                    end = pygame.math.Vector2(self.collisions_rect[0].center)
                    self.direction = (end - start).normalize()
                if self.local_frame_index %50 == 0 : 
                    start = pygame.math.Vector2(self.origin_rect.center)
                    end = pygame.math.Vector2(self.collisions_rect[0].center)
                    self.direction = (end - start).normalize()
                self.move(self.direction, ticked)
            
            if (
                pygame.sprite.collide_rect(player, self)
                and time.time() - self.last_attack > self.attack_cooldown
            ):
                player.take_damage(1)
                self.last_attack = time.time()
        if distance_to_player <10*dpi:
             playerx = player.origin_rect.center[0]
             playery = player.origin_rect.center[1]
             angle_towards_player = get_angle(playerx,self.origin_rect.center[0],playery,self.origin_rect.center[1])
             if abs(angle_towards_player)>10 : 

                 self.image = rotate_image(self.anim.spritelist[self.anim.curr_sprite],angle_towards_player)

        #         self.origin_rect = self.image.get_rect(center = self.origin_rect.center)

    def move(self, direction, delta_time):
        direction = tuple([round(self.speed * delta_time * c) for c in direction])
        self.origin_rect.move_ip(direction)
        if not self.flying and any(
            pygame.sprite.spritecollide(self, obstacle_group, False)
        ):
            self.origin_rect.move_ip(inverse_direction(direction))
        (self.health_bar.origin_rect.x, self.health_bar.origin_rect.y) = (self.origin_rect.x, self.origin_rect.y - 20)

class CreatureHealthBar(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(self.containers)
        self.origin_image = pygame.Surface((70, 5))
        self.origin_image.fill((0, 255, 0))
        self.origin_rect = self.image.get_rect()

    @property
    def rect(self):
        return translated_rect(self.origin_rect)

    @property
    def image(self):
        if hasattr(self, 'creature'):
            pv_size = 70 / self.creature.max_health
            if self.creature.health <= 0:
                return pygame.Surface((0, 0))
            im = pygame.Surface((pv_size * self.creature.health, 5))
            im.fill((0, 255, 0))
            return im
        return self.origin_image
        

class Cursor(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(self.containers)
        self.rect = self.image.get_rect()
        self.update_pos()

    def update_pos(self):
        (self.rect.x, self.rect.y) = pygame.mouse.get_pos()
        self.rect.x -= self.rect[2]/2
        self.rect.y -= self.rect[3]/2

    def update(self):
        self.update_pos()


game_logic = mapgen.Game(max_levels=3)
map_grid = None
game_logic.current_map.display()



background = pygame.Surface(size)
pygame.display.flip()

all_sprites = pygame.sprite.LayeredUpdates()
mapdependent_group = pygame.sprite.Group()
toredraw_group = pygame.sprite.Group()
stairs_group = pygame.sprite.Group()
treasures_group = pygame.sprite.Group()
traps_group = pygame.sprite.Group()
obstacle_group = pygame.sprite.Group()
creature_group = pygame.sprite.Group()
hud_group = pygame.sprite.Group()
healthbar_group = pygame.sprite.Group()
particle_group = pygame.sprite.Group()
inventoryobject_group = pygame.sprite.Group()
player_inv_group = pygame.sprite.Group()
inv_slot_group = pygame.sprite.Group()
projectile_group = pygame.sprite.Group()

Projectile.containers = projectile_group, all_sprites
Player.containers = all_sprites
InventoryObject.containers = all_sprites, inventoryobject_group, mapdependent_group
InvSlot.containers = all_sprites, player_inv_group, inv_slot_group
Ground.containers = all_sprites, mapdependent_group, toredraw_group
Stairs.containers = all_sprites, mapdependent_group, stairs_group
Treasure.containers = all_sprites, mapdependent_group, treasures_group
Background.containers = all_sprites
Wall.containers = all_sprites, obstacle_group, mapdependent_group, toredraw_group
Creature.containers = all_sprites, creature_group, mapdependent_group
CreatureHealthBar.containers = all_sprites, hud_group
Cursor.containers = all_sprites, hud_group
FPSCounter.containers = all_sprites, hud_group
HealthIcon.containers = all_sprites, hud_group, healthbar_group
Dialog.containers = all_sprites, hud_group
Mask.containers = all_sprites, hud_group
Text.containers = all_sprites, hud_group

Player.assets = ["terro.png", "terro_but_mad.png"]
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
Treasure.image = loadify("chest.png", size=3)
Background.image = loadify("background.png", keep_ratio=True, size=2000)
Cursor.image = loadify("cursor.png", size=60)
HealthIcon.image = loadify("heart.png", size=-25)

Player._layer = 2
Wall._layer = 1
Ground._layer = 1
Stairs._layer = 2
Treasure._layer = 2
Background._layer = 0
Mask._layer = 2
Cursor._layer = 3 
FPSCounter._layer = 2
Dialog._layer = 2
HealthIcon._layer = 2
Creature._layer = 2
CreatureHealthBar._layer = 3
InventoryObject._layer = 2
InvSlot._layer = 2
Projectile._layer = 3
Text._layer = 2
background_sprite = Background()
Mask()

player = Player(initial_position=(0, 0))

draw_map()

move_player_to_spawn()

Cursor()
FPSCounter()
dialog = Dialog()
dialog.message = "MEGA CHEVALIER"

for i in range(player.health):
    HealthIcon(offset=i)
particle_system = ParticleEffect(10,200,spawner=screen.get_rect(),forces= [0.1,0.05])
frame_index = 0

Key(player.origin_rect[:2])
###########################################   MAIN LOOP  ###########################################

while True:
    if frame_index%5 ==0: 
        update_map_near_player()
        
    frame_index += 1
    if frame_index % 5 == 0:
        pass
        plane.fill((0,0,0,0))
    ticked = clock.tick(360)
    all_sprites.clear(screen, background)

    all_sprites.update()
    player.inventory.update()

    if player.health <= 0:
        player.kill()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            nums = (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0)
            if event.key == pygame.K_e:
                for _ in pygame.sprite.spritecollide(player, stairs_group, False):
                    game_logic.move_up()
                    draw_map()
                    move_player_to_spawn()
                    dialog.message = ""
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
            elif event.key in nums[:Player.inventory_size]:
                clicked_slot_item = player.inventory.items[nums.index(event.key)]
                if clicked_slot_item is not None:
                    old_state = clicked_slot_item.picked_up
                for s in player.inventory.items:
                    if s is not None:
                        s.picked_up = False
                for s in inv_slot_group.sprites():
                    s.has_picked_item = False
                if clicked_slot_item is not None:
                    clicked_slot_item.picked_up = not old_state
                if player.inventory.picked_item:
                    inv_slot_group.sprites()[player.inventory.picked_item_index].has_picked_item = True

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            # quand un item est récup on scale son image or ça ne change pas son rect donc je test les collisions avec le rect de l'image avec les topleft superposés
            clicked_inv_sprites = [s for s in player.inventory.items if s is not None and s.image.get_rect(topleft = s.rect.topleft).collidepoint(pos)]
            if clicked_inv_sprites:
                old_state = clicked_inv_sprites[0].picked_up
                for s in player.inventory.items:
                    if s is not None:
                        s.picked_up = False
                for s in inv_slot_group.sprites():
                    s.has_picked_item = False
                clicked_inv_sprites[0].picked_up = not old_state
                inv_slot_group.sprites()[player.inventory.picked_item_index].has_picked_item = True
            picked_item = player.inventory.picked_item
            if picked_item and not isinstance(picked_item,Key):
                picked_item.use()

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


