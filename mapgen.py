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
        return coord in self.points

    def add_point(self, coord):
        """Add new point to new path"""
        self.points.append(coord)

    def __repr__(self):
        return f"<mapgen.AbstractPath nb_points={len(self.points)}>"

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
        """Check x axis intersection between two rooms"""
        return other.top_left.y <= self.top_left.y <= other.bottom_right.y or other.top_left.y <= self.bottom_right.y <= other.bottom_right.y or self.top_left.y <= other.top_left.y <= self.bottom_right.y or self.top_left.y <= other.bottom_right.y <= self.bottom_right.y

    def intersect_y(self, other):
        """Check y axis intersection between two rooms"""
        return other.top_left.x <= self.top_left.x <= other.bottom_right.x or other.top_left.x <= self.bottom_right.x <= other.bottom_right.x or self.top_left.x <= other.top_left.x <= self.bottom_right.x or self.top_left.x <= other.bottom_right.x <= self.bottom_right.x

    def intersect_with(self, other):
        """Check intersection between two rooms"""
        return self.intersect_x(other) and self.intersect_y(other)

    def is_overlapping(self, room_list):
        """Check intersection between multiples rooms"""
        return any([self.intersect_with(room) for room in room_list])

class AbstractMap:
    def __init__(self, width, height, max_rooms=4):
        self.width = width
        self.height = height
        self.max_rooms = max_rooms
        self.rooms = []
        self.paths = []

    def __repr__(self):
        return f"<mapgen.AbstractMap width={self.width},height={self.height},nb_rooms={len(self.rooms)}>"

    def random_room(self):
        """Generate a random room"""
        x = random.randint(0, self.width - 3)
        y = random.randint(0, self.height - 3)
        width = random.randint(3, 8)
        height = random.randint(3, 8)
        return AbstractRoom(AbstractCoord(x, y), width, height)

    def random_map(self):
        """Fill map with random rooms"""
        for _ in range(self.max_rooms):
            room = self.random_room()
            if not room.is_overlapping(self.rooms):
                self.rooms.append(room)

    def make_paths(self):
        """Create paths between rooms"""
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
                path.add_point(position)
                position += direction
                path.add_point(position)

            if start.x > end.x:
                direction = AbstractCoord(-1, 0)
            else:
                direction = AbstractCoord(1, 0)

            for i in range(abs(end.x - start.x)):
                path.add_point(position)
                position += direction
                path.add_point(position)
            
            self.paths.append(path)

    def slice(self, top_left, width, height):
        raise NotImplementedError("slice not implemented")

    def display(self):
        """Display grid on stdout"""
        grid = self.grid()
        for line in grid:
            for elem in line:
                print(elem, end='')
            print("\n", end='')

    def grid(self):
        """Generate map grid"""
        is_room = lambda x, y: any([AbstractCoord(x, y) in room for room in self.rooms])
        is_path = lambda x, y: any([AbstractCoord(x, y) in path for path in self.paths])
        return [['#' if is_room(x, y) or is_path(x, y) else "." for x in range(self.height)] for y in range(self.width)]

