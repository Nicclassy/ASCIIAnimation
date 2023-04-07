from time import perf_counter
from typing import Any, Optional, Literal

from mechanics.types import CharacterList2D, Numeric
from mechanics.movement.position import Position
from mechanics.movement.vectors import Vector
from mechanics.movement.jump import JumpMovement
from mechanics.sprites.sprite import Sprite


class MovableSpriteMixin(Sprite):
    pass


class UncollidableSpriteMixin:
    pass


class AllCharactersUncollidableMixin(Sprite, UncollidableSpriteMixin):

    def get_covered_coordinates(self) -> set:
        dy, dx = self._position
        return set((y + dy, x + dx) for y in range(self._height) for x in range(self._width))


class TimedDestructionSpriteMixin(Sprite):

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._destroy_after = kwargs["destroy_after"]
        self._time_elapsed = 0.0
        self._destroyed = False

    def record_time(self, time_elapsed: float):
        self._time_elapsed = time_elapsed

    def disappear(self) -> bool:
        self._destroyed = perf_counter() - self._time_elapsed >= self._destroy_after
        return self._destroyed


class CollisionDestructionMixin(Sprite):
    pass


class TerrainExitDestructionMixin(Sprite):
    pass


class GroundMixin:
    pass


class TimedPositionMovementMixin:

    def __init__(self):
        self._start_time = perf_counter()

    def reset_start_time(self):
        self._start_time = perf_counter()

    def get_position_at_time(self, time: Numeric, terrain_height: int, terrain_width: int) -> Position:
        pass


class VectorMovementMixin(Sprite):

    def apply_vector(self, vector: Vector):
        self._position += vector


class PositionMovementMixin(Sprite):

    def set_position(self, position: Position):
        self._position = position


class HealthMixin:

    def __init__(self, health: Numeric):
        self._health = health

    @property
    def health(self) -> int:
        return self._health

    @health.setter
    def health(self, value: int):
        self._health = value


class PlayerDamagingSpriteMixin(CollisionDestructionMixin, TerrainExitDestructionMixin):
    pass


class JumpMovementMixin(Sprite):

    def __init__(self, data: str | CharacterList2D, position: Position, max_height: Numeric,
                 time_of_flight: Numeric, projection_quadrant: Literal[1, 2, 3, 4]):
        super().__init__(data, position)
        # Projection quadrant is 2 since the jump movement can be considered a DIFFERENCE
        # rather than a position (i.e. a difference of (y, x) means adding that to the current position)
        self._jump_movement = JumpMovement(max_height, time_of_flight, projection_quadrant)
        self._jumpable = False
        self._jumping = False
        self._jump_delta = Vector.ZERO
        self._last_recorded_jump_time = float()

    @property
    def jumping(self) -> bool:
        return self._jumping

    @property
    def jumpable(self) -> bool:
        return self._jumpable

    @jumpable.setter
    def jumpable(self, value: bool):
        self._jumpable = value

    def get_vector_at_time(self, time: Numeric, terrain_height: int, terrain_width: int) -> Vector:
        if self._jumping:
            return self._jump_movement.get_vector_at_time(time - self._last_recorded_jump_time,
                                                          terrain_height, terrain_width)
        else:
            return Vector.ZERO

    def set_jump_state(self, state: bool, record_time: Optional[Numeric] = None):
        if state:
            self._jumping = True
            self._last_recorded_jump_time = record_time
        else:
            self._jumping = False


if __name__ == "__main__":
    jm = JumpMovement(6, 8, 2)
    for t in range(8):
        print(Position(*jm.get_vector_at_time(t, 10, 10))[::-1])
