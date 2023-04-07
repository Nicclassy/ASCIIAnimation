import math
from enum import Enum

from typing_extensions import Self

from mechanics.types import Numeric
from mechanics.movement.position import Position


class Vector(Position):

    ZERO: "Vector"

    def __init__(self, y: Numeric = 0, x: Numeric = 0):
        super().__init__(y, x)

    def __abs__(self) -> int:
        return int(math.sqrt(pow(self._value[0], 2) + pow(self._value[1], 2)))

    def __neg__(self) -> Self:
        return type(self)(-self._value[0], -self._value[1])

    def __hash__(self) -> int:
        return hash((self._value,))

    def __str__(self) -> str:
        output = ""
        y, x = self._value
        if x != 0:
            output += (str(x) if abs(x) != 1 else "") + "i"
        if y != 0:
            if len(output) > 0:
                output += " "
                if y < 0:
                    if "i" not in output:
                        y = abs(y)
                    sign = "- "
                else:
                    sign = "+ "
            else:
                sign = ""
            output += sign + (str(y) if abs(y) != 1 else "") + "j"
        return output or "0"


class UnitVectorEnum(Enum):
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4


class UnitVector(Vector):
    UP = Vector(-1, 0)
    DOWN = Vector(1, 0)
    LEFT = Vector(0, -1)
    RIGHT = Vector(0, 1)

    def __class_getitem__(cls, item: str | UnitVectorEnum) -> Vector:
        match item:
            case "up" | UnitVectorEnum.UP:
                return cls.UP
            case "down" | UnitVectorEnum.DOWN:
                return cls.DOWN
            case "left" | UnitVectorEnum.LEFT:
                return cls.LEFT
            case "right" | UnitVectorEnum.RIGHT:
                return cls.RIGHT


class VectorStream:

    def __init__(self):
        self._state = Vector.ZERO

    def get_vector(self):
        return self._state

    def set_vector(self, vector: Vector):
        self._state = vector

    def reset(self):
        self._state = Vector.ZERO


Vector.ZERO = Vector(0, 0)
