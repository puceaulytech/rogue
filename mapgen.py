import random
import copy
import math


class Element:
    def __init__(self, elem_id, position, difficulty):
        self.id = elem_id
        self.position = position
        self.difficulty = difficulty

    def __repr__(self):
        return f"<mapgen.Element id={self.id},position={self.position},difficulty={self.difficulty}>"


class Creature(Element):
    creatures = (["sprite_0.png", "sprite_1.png"], 1, 0.1, True), (
        ["dragon.png"],
        2,
        0.2,
        False,
    )

    def __init__(self, elem_id, position, difficulty, speed, flying):
        super().__init__(elem_id, position, difficulty)
        self.speed = speed
        self.flying = flying


class Item(Element):
    def __init__(self, elem_id, position, difficulty):
        super().__init__(elem_id, position, difficulty)


class Coord:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __getitem__(self, key):
        if key in (0, 1):
            return (self.x, self.y)[key]
        raise IndexError("Invalid key")

    def __setitem__(self, key, value):
        if key == 0:
            self.x = value
        elif key == 1:
            self.y = value
        else:
            raise IndexError("Invalid key")

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __str__(self):
        return f"({self.x},{self.y})"

    def __repr__(self):
        return f"<mapgen.Coord x={self.x},y={self.y}>"

    def __add__(self, other):
        return Coord(self.x + other.x, self.y + other.y)

    def distance(self, other):
        if not isinstance(other, Coord):
            raise TypeError("Not a coord")
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)


class Path:
    def __init__(self):
        self.points = []

    def __contains__(self, coord):
        if not isinstance(coord, Coord):
            raise TypeError("Not an Coord")
        return coord in self.points

    def __getitem__(self, key):
        return self.points[key]

    def __setitem__(self, key, value):
        self.points[key] = value

    def __len__(self):
        return len(self.points)

    def __repr__(self):
        return f"<mapgen.Path nb_points={len(self.points)}>"

    def add_point(self, coord):
        """Add new point to new path"""
        self.points.append(coord)


class CircleRoom:
    def __init__(self, center, radius):
        self.center = center
        self.radius = radius

    def __repr__(self):
        return f"<mapgen.CircleRoom center={self.center},radius={self.radius}>"

    def __contains__(self, coord):
        if not isinstance(coord, Coord):
            raise TypeError("Not an Coord")
        return self.center.distance(coord) <= self.radius

    def intersect_circle(self, other):
        """Check intersection with other circle room"""
        return self.center.distance(other.center) <= self.radius + other.radius

    def intersect_rect(self, other):
        return self.center.distance(other.center) <= self.radius + math.sqrt(
            (other.width**2 + other.height**2)
        )

    def intersect_with(self, other):
        if isinstance(other, CircleRoom):
            return self.intersect_circle(other)
        return self.intersect_rect(other)

    def is_overlapping(self, room_list):
        return any([self.intersect_with(room) for room in room_list])


class Room:
    def __init__(self, top_left, width, height):
        self.top_left = top_left
        self.width = width
        self.height = height

    @property
    def bottom_right(self):
        return self.top_left + Coord(self.width - 1, self.height - 1)

    @property
    def center(self):
        return Coord(
            (self.top_left.x + self.bottom_right.x) // 2,
            (self.top_left.y + self.bottom_right.y) // 2,
        )

    def __repr__(self):
        return f"<mapgen.Room top_left={self.top_left},width={self.width},height={self.height}>"

    def __contains__(self, coord):
        if not isinstance(coord, Coord):
            raise TypeError("Not an Coord")
        correct_x = self.top_left.x <= coord.x <= self.top_left.x + self.width - 1
        correct_y = self.top_left.y <= coord.y <= self.top_left.y + self.height - 1
        return correct_x and correct_y

    def intersect_x(self, other):
        """Check x axis intersection between two rooms"""
        return (
            other.top_left.y <= self.top_left.y <= other.bottom_right.y
            or other.top_left.y <= self.bottom_right.y <= other.bottom_right.y
            or self.top_left.y <= other.top_left.y <= self.bottom_right.y
            or self.top_left.y <= other.bottom_right.y <= self.bottom_right.y
        )

    def intersect_y(self, other):
        """Check y axis intersection between two rooms"""
        return (
            other.top_left.x <= self.top_left.x <= other.bottom_right.x
            or other.top_left.x <= self.bottom_right.x <= other.bottom_right.x
            or self.top_left.x <= other.top_left.x <= self.bottom_right.x
            or self.top_left.x <= other.bottom_right.x <= self.bottom_right.x
        )

    def intersect_with(self, other):
        """Check intersection between two rooms"""
        return self.intersect_x(other) and self.intersect_y(other)

    def is_overlapping(self, room_list):
        """Check intersection between multiples rooms"""
        return any([self.intersect_with(room) for room in room_list])


class Map:
    def __init__(self, width, height, max_rooms=4):
        self.width = width
        self.height = height
        self.max_rooms = max_rooms
        self.max_exot_rooms = 50
        self.rooms = []
        self.paths = []
        self.creatures = []
        self.items = []

    def __repr__(self):
        return f"<mapgen.Map width={self.width},height={self.height},nb_rooms={len(self.rooms)}>"

    def random_room(self):
        """Generate a random room"""
        x = random.randint(0, self.width - 3)
        y = random.randint(0, self.height - 3)
        width = random.randint(3, 8)
        height = random.randint(3, 8)
        return Room(Coord(x, y), width, height)

    def random_circle_room(self):
        x = random.randint(0, self.width - 3)
        y = random.randint(0, self.height - 3)
        radius = random.randint(3, 5)
        return CircleRoom(Coord(x, y), radius)

    def generate_random(self):
        """Fill map with random rooms"""
        for _ in range(self.max_rooms):
            room = self.random_room()
            if not room.is_overlapping(self.rooms):
                self.rooms.append(room)

    def find_valid_random_coord(self, room):
        valid_coord = False
        position = None
        while not valid_coord:
            if isinstance(room, Room):
                abs_pos_x = random.randint(0, room.width - 1)
                abs_pos_y = random.randint(0, room.height - 1)
                position = Coord(
                    room.top_left.x + abs_pos_x, room.top_left.y + abs_pos_y
                )
            elif isinstance(room, CircleRoom):
                distance = random.randint(0, room.radius)
                angle = random.uniform(0, 2 * math.pi)
                abs_pos_x = round(distance * math.cos(angle))
                abs_pos_y = round(distance * math.sin(angle))
                position = Coord(room.center.x + abs_pos_x, room.center.y + abs_pos_y)
            valid_coord = all(
                [
                    position != element.position
                    for element in self.creatures + self.items
                ]
            )
        return position

    def fill_with_elements(self):
        for room in self.rooms[1:]:
            nb_creatures = random.randint(0, 2)
            weights = list(map(lambda c: 1 / c[1], Creature.creatures))
            for _ in range(nb_creatures):
                position = self.find_valid_random_coord(room)
                attribs = copy.copy(random.choices(Creature.creatures, weights, k=1)[0])
                asset_id, difficulty, speed, flying = attribs
                creature = Creature(
                    asset_id, None, difficulty=difficulty, speed=speed, flying=flying
                )
                creature.position = position
                self.creatures.append(creature)
            # nb_items = random.randint(0, 2)
            # for _ in range(nb_items):
            #     position = self.find_valid_random_coord(room)
            #     item = copy.copy(random.choice(self.available_items))
            #     item.position = position
            #     self.items.append(item)

    def generate_random_circle(self):
        for i in range(self.max_exot_rooms):
            room = self.random_circle_room()
            if not room.is_overlapping(self.rooms):
                self.rooms.append(room)

    def make_paths(self):
        """Create paths between rooms"""
        for i in range(len(self.rooms) - 1):
            first = self.rooms[i]
            second = self.rooms[i + 1]
            start = first.center
            end = second.center
            direction = None
            position = Coord(start.x, start.y)
            path = Path()

            if start.y > end.y:
                direction = Coord(0, -1)
            else:
                direction = Coord(0, 1)

            for i in range(abs(end.y - start.y)):
                path.add_point(position)
                position += direction
                path.add_point(position)

            if start.x > end.x:
                direction = Coord(-1, 0)
            else:
                direction = Coord(1, 0)

            for i in range(abs(end.x - start.x)):
                path.add_point(position)
                position += direction
                path.add_point(position)

            self.paths.append(path)

    def slice(self, top_left, width, height):
        original_grid = self.grid()
        result = []
        for row in original_grid[top_left.y : top_left.y + width - 1]:
            result.append(row[top_left.x : top_left.x + height - 1])
        return result

    def display(self, custom_grid=None):
        """Display grid on stdout"""
        grid = self.grid() if custom_grid is None else custom_grid
        for line in grid:
            for elem in line:
                print(elem, end="")
            print("\n", end="")

    def get_character_at(self, coord):
        if any([coord == creature.position for creature in self.creatures]):
            return "x"
        elif any([coord == item.position for item in self.items]):
            return "o"
        elif any([coord in room for room in self.rooms]):
            return "#"
        elif any([coord in path for path in self.paths]):
            return "%"
        return "."

    def grid(self):
        """Generate map grid"""
        return [
            [self.get_character_at(Coord(x, y)) for x in range(self.height)]
            for y in range(self.width)
        ]
