from json import dumps, loads
from sys import argv
from typing import Any
from dataclasses import dataclass, field
import numpy as np

"""
Directions:
  0 -> UP
  1 -> RIGHT
  2 -> DOWN
  3 -> LEFT
"""

@dataclass(eq=False)
class Wall:
    x1: float
    y1: float
    x2: float
    y2: float

    group: "set[Wall] | None" = None

    def get_width(self):
        return self.x2 - self.x1

    def set_width(self, value: float):
        if self.group is not None:
            for wall in self.group:
                wall.x2 = wall.x1 + value
        else:
            self.x2 = self.x1 + value

    def get_height(self):
        return self.y2 - self.y1

    def set_height(self, value: float):
        if self.group is not None:
            for wall in self.group:
                wall.y2 = wall.y1 + value
        else:
            self.y2 = self.y1 + value

    def is_horizontal(self):
        return self.get_width() > self.get_height()

    def translate(self, x: float, y: float):
        if self.group is not None:
            for wall in self.group:
                wall._translateSelf(x, y)
        else:
            self._translateSelf(x, y)
    
    def _translateSelf(self, x: float, y: float):
        self.x1 += x
        self.x2 += x
        self.y1 += y
        self.y2 += y

    def link(self, other: "Wall"):
        # If both walls are not in a group, create a new group with both of them
        if self.group is None and other.group is None:
            self.group = other.group = {self, other}
            return

        # If both walls are grouped, merge the group
        if self.group is not None and other.group is not None:

            new_list = {*self.group, *other.group}
            for wall in self.group:
                wall.group = new_list

            for wall in other.group:
                wall.group = new_list
        
        # If other is in a group add self to it
        if other.group is not None:
            self.group = other.group
            other.group.add(self)
            return

        # If self is in a group add other to it
        if self.group is not None:
            other.group = self.group
            self.group.add(other)
            return
        
        # Unreachable
        assert False
    
    def get_point(self, direction: int):
        if direction == 0:
            return np.array(((self.x1 + self.x2) / 2, self.y1), dtype=np.float)

        if direction == 1:
            return np.array((self.x2, (self.y1 + self.y2) / 2), dtype=np.float)

        if direction == 2:
            return np.array(((self.x1 + self.x2) / 2, self.y2), dtype=np.float)

        if direction == 3:
            return np.array((self.x1, (self.y1 + self.y2) / 2), dtype=np.float)
        
        # Illegal direction
        assert False
        

@dataclass
class Socket:
    wall: Wall
    direction: int
    original_position: Any = field(init=False)
    tolerance: float

    def __post_init__(self):
        self.original_position = self.wall.get_point(self.direction)

    @property
    def position(self):
        return self.wall.get_point(self.direction)

    def get_opposite(self):
        return (self.direction + 2) % 4
    
    def is_horizontal(self):
        return self.direction == 1 or self.direction == 3

def align_walls(walls: "list[Wall]"):
    sockets: "dict[int, list[Socket]]" = {
        0: [],
        1: [],
        2: [],
        3: [],
    }

    for wall in walls:
        horizontal = wall.is_horizontal()
        vertical = not horizontal

        # If the wall is close enough to a square, consider is horizontal and vertical at once
        if abs((wall.get_height() - wall.get_width()) / (wall.get_height() + wall.get_width())) < 0.15:
            horizontal = True
            vertical = True

        if horizontal:
            tolerance = wall.get_height()
            sockets[1].append(Socket(wall, 1, tolerance))
            sockets[3].append(Socket(wall, 3, tolerance))

        if vertical:
            tolerance = wall.get_width()
            sockets[0].append(Socket(wall, 0, tolerance))
            sockets[2].append(Socket(wall, 2, tolerance))
    
    for direction in [0, 1]:
        direction_sockets = sockets[direction]
        j = 0
        matches = 0

        while j < len(direction_sockets):
            socket = direction_sockets[j]
            j += 1
            
            opposite_sockets = sockets[socket.get_opposite()]

            # Find socket with opposite direction that is close enough
            for opposite_socket in opposite_sockets:
                distance = np.linalg.norm(socket.original_position - opposite_socket.original_position)

                if socket.is_horizontal():
                    distance += abs(socket.wall.get_height() - opposite_socket.wall.get_height())
                else:
                    distance += abs(socket.wall.get_width() - opposite_socket.wall.get_width())

                tolerance = min(socket.tolerance, opposite_socket.tolerance)
                if distance <= tolerance:
                    break
            else:
                opposite_socket = None
            
            if opposite_socket is None:
                continue
            
            matches += 1

            # Remove the matched sockets
            direction_sockets.remove(socket)
            opposite_sockets.remove(opposite_socket)

            # Rollback iteration to account for removed element
            j -= 1

            # Unify the thickness
            if socket.is_horizontal():
                value = (socket.wall.get_height() + opposite_socket.wall.get_height()) / 2
                socket.wall.set_height(value)
                opposite_socket.wall.set_height(value)
            else:
                value = (socket.wall.get_width() + opposite_socket.wall.get_width()) / 2
                socket.wall.set_width(value)
                opposite_socket.wall.set_width(value)

            # Offset for the opposite socket to be aligned with this
            center = (opposite_socket.position + socket.position) / 2

            correction = (socket.position - center) * -1
            socket.wall.translate(*correction)

            correction = (opposite_socket.position - center) * -1
            opposite_socket.wall.translate(*correction)

            # Join the two walls together
            opposite_socket.wall.link(socket.wall)

        print(f"For direction {direction} aligned {matches} pairs")

def walls_from_json(data: dict):
    walls: "list[Wall]" = []

    for point in data["points"]:
        walls.append(Wall(
            point["x1"], # type: ignore
            point["y1"],
            point["x2"],
            point["y2"],
        ))
    
    return walls

def walls_to_json(walls: "list[Wall]"):
    points = []

    for wall in walls:
        points.append({
            "x1": wall.x1,
            "y1": wall.y1,
            "x2": wall.x2,
            "y2": wall.y2,
        })

    return points

if __name__ == "__main__":
    with open(argv[1], 'rt') as file:
        content = file.read()

    data = loads(content)
    walls = walls_from_json(data)
    align_walls(walls)
    data["points"] = walls_to_json(walls)

    with open(argv[1] + ".new.json", "wt") as file:
        file.write(dumps(data, indent=4))

