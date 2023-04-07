from typing import Literal

from typing_extensions import Self

from mechanics.types import Numeric


class Position:

    __slots__ = "_value"

    ORIGIN: "Position"

    def __init__(self, y: Numeric = 0, x: Numeric = 0):
        self._value = (y, x)

    def __repr__(self) -> str:
        return "{}({}, {})".format(self.__class__.__name__, *self._value)

    def __getitem__(self, index: int) -> int:
        return self._value[index]

    def __eq__(self, other: Self) -> bool:
        return self[:] == other[:]

    def __hash__(self) -> int:
        return hash((self._value,))

    def __add__(self, other: Self) -> Self:
        return type(self)(self[0] + other[0], self[1] + other[1])

    def __sub__(self, other: Self) -> Self:
        return type(self)(self[0] - other[0], self[1] - other[1])

    def __mul__(self, other: int) -> Self:
        return type(self)(self._value[0] * other, self._value[1] * other)

    def __floordiv__(self, other: Self) -> Self:
        return type(self)(self._value[0] // other[0], self._value[1] // other[1])

    def __truediv__(self, other: Self) -> Self:
        return type(self)(self._value[0] / other[0], self._value[1] / other[1])


class RelativePosition(Position):

    ORIGIN: "RelativePosition"

    def __init__(self, y: Numeric = 0, x: Numeric = 0):
        super().__init__(y, x)

    def from_bottom_left(self, terrain_height: int) -> Position:
        return Position(terrain_height - 1 - self._value[0], self._value[1])

    def from_bottom_right(self, terrain_height: int, terrain_width: int) -> Position:
        return Position(terrain_height - 1 - self._value[0], terrain_width - 1 - self._value[1])

    def from_top_left(self) -> Position:
        return Position(*self._value)

    def from_top_right(self, terrain_width: int) -> Position:
        return Position(self._value[0], terrain_width - 1 - self._value[1])

    def normalize(self, quadrant: Literal[1, 2, 3, 4], terrain_height: int, terrain_width: int) -> Position:
        match quadrant:
            case 1:
                return self.from_top_right(terrain_width)
            case 2:
                return self.from_top_left()
            case 3:
                return self.from_bottom_left(terrain_height)
            case 4:
                return self.from_bottom_right(terrain_height, terrain_width)

    def normalize_wrt_sprite(self, sprite_position: Position) -> Position:
        return Position(*(self + sprite_position))


Position.ORIGIN = Position(0, 0)
RelativePosition.ORIGIN = RelativePosition(0, 0)
