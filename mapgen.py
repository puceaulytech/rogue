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

class AbstractPath:
    def __init__(self):
        self.points = []

    def __contains__(self, coord):
        if not isinstance(coord, AbstractCoord):
            raise TypeError("Not an AbstractCoord")
        return coord in points

    def __repr__(self):
        return f"<mapgen.AbstractPath points={self.points}>"

class AbstractRoom:
    def __init__(self, top_left, width, height):
        self.top_left = top_left
        self.width = width
        self.height = height

    @property
    def bottom_right(self):
        return self.top_left + AbstractCoord(self.width - 1, self.height - 1)
    
    def center(self):
        return AbstractCoord((self.top_left.x + self.bottom_right.x) // 2, (self.top_left.y + self.bottom_right.y) // 2)

    def __repr__(self):
        return f"<mapgen.AbstractRoom top_left={self.top_left},width={self.width},height={self.height}>"

    def __contains__(self, coord):
        if not isinstance(coord, AbstractCoord):
            raise TypeError("Not an AbstractCoord")
        correct_x = self.top_left.x <= coord.x <= self.top_left.x + self.width - 1
        correct_y = self.top_left.y <= coord.y <= self.top_left.y + self.height - 1
        return correct_x and correct_y

    def intersect_x(self, other):
        return other.top_left.y <= self.top_left.y <= other.bottom_right.y or other.top_left.y <= self.bottom_right.y <= other.bottom_right.y or self.top_left.y <= other.top_left.y <= self.bottom_right.y or self.top_left.y <= other.bottom_right.y <= self.bottom_right.y

    def intersect_y(self, other):
        return other.top_left.x <= self.top_left.x <= other.bottom_right.x or other.top_left.x <= self.bottom_right.x <= other.bottom_right.x or self.top_left.x <= other.top_left.x <= self.bottom_right.x or self.top_left.x <= other.bottom_right.x <= self.bottom_right.x

    def intersect_with(self, other):
        return self.intersect_x(other) and self.intersect_y(other)

    def is_overlapping(self, room_list):
        return any([self.intersect_with(room) for room in room_list])

class AbstractMap:
    def __init__(self, width, height, nb_rooms=4):
        self.width = width
        self.height = height
        self.nb_rooms = nb_rooms
        self.rooms = []
        self.paths = []

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

    def make_paths(self):
        for i in range(len(self.rooms) - 1):
            first = self.rooms[i]
            second = self.rooms[i + 1]
            start = first.center()
            end = second.center()
            direction = None
            position = AbstractCoord(start.x, start.y)
            path = AbstractPath()

            if start.y > end.y:
                direction = AbstractCoord(0, -1)
            else:
                direction = AbstractCoord(0, 1)

            for i in range(abs(end.y - start.y)):
                path.points.append(position)
                position += direction
                path.points.append(position)

            if start.x > end.x:
                direction = AbstractCoord(-1, 0)
            else:
                direction = AbstractCoord(1, 0)

            for i in range(abs(end.x - start.x)):
                path.points.append(position)
                position += direction
                path.points.append(position)
            
            self.paths.append(path)

    def slice(self, top_left, width, height):
        result = [['.' for _ in range(height)] for __ in range(width)]

    def display(self):
        grid = self.grid()
        for line in grid:
            for elem in line:
                print(elem, end='')
            print("\n", end='')

    def grid(self):
        is_room = lambda x, y, rooms: any([AbstractCoord(x, y) in room for room in rooms])
        is_path = lambda x, y, paths: any([AbstractCoord(x, y) in path.points for path in paths])
        return [['#' if is_room(x, y, self.rooms) or is_path(x, y, self.paths) else "." for x in range(self.height)] for y in range(self.width)]

