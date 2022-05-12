import random

class AbstractCoord:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __str__(self):
        return f"({self.x},{self.y})"

    def __repr__(self):
        return f"<mapgen.AbstractCoord x={self.x},y={self.y}>"

    def __add__(self, other):
        return AbstractCoord(self.x + other.x, self.y + other.y)

class AbstractRoom:
    def __init__(self, top_left, width, height):
        self.top_left = top_left
        self.width = width
        self.height = height

    @property
    def bottom_right(self):
        return self.top_left + AbstractCoord(self.width, self.height)

    def __repr__(self):
        return f"<mapgen.AbstractRoom top_left={self.top_left},width={self.width},height={self.height}>"

    def __contains__(self, coord):
        if not isinstance(coord, AbstractCoord):
            raise TypeError("Not an AbstractCoord")
        correct_x = self.top_left.x <= coord.x <= self.top_left.x + self.width
        correct_y = self.top_left.y <= coord.y <= self.top_left.y + self.height
        return correct_x and correct_y

    def intersect_with(self, other):
        return self.top_left in other or self.bottom_right in other or AbstractCoord(self.top_left.x, self.bottom_right.y) in other or AbstractCoord(self.bottom_right.x, self.top_left.y) in other or other.top_left in self or other.bottom_right in self

    def is_overlapping(self, room_list):
        return any([self.intersect_with(room) for room in room_list])

class AbstractMap:
    def __init__(self, width, height, nb_rooms=4):
        self.width = width
        self.height = height
        self.nb_rooms = nb_rooms
        self.rooms = []

    def __repr__(self):
        return f"<mapgen.AbstractMap width={self.width},height={self.height},nb_rooms={self.nb_rooms}>"

    def random_room(self):
        x = random.randint(0, self.width - 3)
        y = random.randint(0, self.height - 3)
        width = random.randint(3, 8)
        height = random.randint(3, 8)
        return AbstractRoom(AbstractCoord(x, y), width, height)

    def random_map(self):
        for _ in range(self.nb_rooms):
            room = self.random_room()
            if not room.is_overlapping(self.rooms):
                self.rooms.append(room)

    def slice(self, top_left, width, height):
        result = [['.' for _ in range(height)] for __ in range(width)]

    def display(self):
        grid = self.grid()
        for line in grid:
            for elem in line:
                print(elem, end='')
            print("\n", end='')

    def grid(self):
        return [['#' if any([AbstractCoord(x, y) in room for room in self.rooms]) else "." for x in range(self.height)] for y in range(self.width)]

