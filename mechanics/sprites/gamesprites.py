from typing import Literal

from mechanics.constants import BLANK_CHARACTER
from mechanics.sprites.projectile import StandardProjectileSprite, LinearEquationSprite, StraightLineEquationSprite
from mechanics.sprites.sprite import Sprite
from mechanics.types import CharacterList2D, Numeric
from mechanics.movement.position import Position
from mechanics.sprites.mixins import (
    MovableSpriteMixin, VectorMovementMixin, PositionMovementMixin, UncollidableSpriteMixin, JumpMovementMixin,
    CollisionDestructionMixin, TerrainExitDestructionMixin, PlayerDamagingSpriteMixin, HealthMixin,
)
from mechanics.structures.iterators import FunctionValueIterator, ValueIteratorList
from mechanics.structures.functions import Timer
from mechanics.sprites.updateablesprite import (
    IntervalFrameUpdateMixin, FunctionInputTextSprite, CyclicUpdateSprite, SequentialTextUpdateSprite, UpdateableSprite
)
from text.character import ModifiedCharacter


class PlayerSprite(MovableSpriteMixin, PositionMovementMixin, VectorMovementMixin):

    def __init__(self, data: str | CharacterList2D, position: Position = Position.ORIGIN):
        super().__init__(data, position)


class HealthPlayerSprite(PlayerSprite, HealthMixin):

    def __init__(self, data: str | CharacterList2D, position: Position, health: int):
        super().__init__(data, position)
        HealthMixin.__init__(self, health)


class JumpablePlayerSprite(JumpMovementMixin, PlayerSprite):

    def __init__(self, data: str | CharacterList2D, max_height: Numeric, time_of_flight: Numeric,
                 projection_quadrant: Literal[1, 2, 3, 4] = 2, position: Position = Position.ORIGIN):
        super().__init__(data, position, max_height, time_of_flight, projection_quadrant)


class StaticSprite(Sprite, UncollidableSpriteMixin):
    pass


class CharacterStreamSprite(SequentialTextUpdateSprite, IntervalFrameUpdateMixin):

    def __init__(self, text: str, position: Position,
                 update_interval: Numeric = 0.05,
                 sleep: bool = True,
                 disappear_on_exhaust: Numeric | bool = 1.5,
                 sleep_at_newline: Numeric | bool = 2,
                 sleep_at_punctuation_character: Numeric | bool = 0.75):
        args = [disappear_on_exhaust, sleep_at_newline, sleep_at_punctuation_character] if sleep else [False] * 3
        super().__init__(text, *args, position)
        IntervalFrameUpdateMixin.__init__(self, update_interval)
        self.sleepable = sleep


class TimerSprite(StaticSprite, FunctionInputTextSprite):

    def __init__(self, position: Position, minutes: Numeric = 0, seconds: Numeric = 0):
        self._timer = Timer(minutes=minutes, seconds=seconds)
        self._ended = False
        super().__init__("———————\n│{}:{}│\n———————",
                         7,
                         ValueIteratorList(
                             [
                                 FunctionValueIterator(self._timer, self.timer_ended)
                             ]),
                         position)

    @property
    def timer(self) -> Timer:
        return self._timer

    def get_seconds_passed(self) -> int:
        minutes, seconds = self._timer.get_current_time()
        return self._timer.seconds_to_count - (minutes * 60 + seconds) - 1

    def timer_ended(self, time_values: list[str, str]) -> bool:
        minutes, seconds = time_values
        # Minutes is a floating point value with no trailing decimal values;
        # if there are 0.000009 seconds left we still consider that finished (unfortunately)
        if int(minutes) <= 0 and int(seconds) <= 0:
            self._ended = True
        return self._ended


class LoadingSprite(StaticSprite, CyclicUpdateSprite, IntervalFrameUpdateMixin):

    def __init__(self, position: Position, update_interval: Numeric = 0.5):
        sprite_frames = [
                         [["|"]],
                         [["/"]],
                         [["—"]],
                         [["\\"]],
                        ]
        super().__init__(sprite_frames, position)
        IntervalFrameUpdateMixin.__init__(self, update_interval)


class EllipsisLoadingSprite(StaticSprite, CyclicUpdateSprite, IntervalFrameUpdateMixin):

    def __init__(self, position: Position, length: int = 3,
                 update_interval: Numeric = 0.43, reverse_order: bool = False):
        sprite_frames = [[["."] * amount + [BLANK_CHARACTER] * (length - amount)] for amount in range(1, length + 1)]
        if reverse_order:
            sprite_frames.reverse()
        super().__init__(sprite_frames, position)
        IntervalFrameUpdateMixin.__init__(self, update_interval)


class HealthBarSprite(UpdateableSprite, StaticSprite):

    def __init__(self, health: int, position: Position, player_sprite: PlayerSprite):
        assert isinstance(player_sprite, HealthMixin)
        self.__health = health
        self.__max_health = health
        self.__player_sprite = player_sprite
        self.__updateable = False
        super().__init__([list("—" * (health + 2)), list("│" + " " * health + "│"), list("—" * (health + 2))], position)
        self.paint({"back": {" ": "lightgreen"}})

    def set_health(self):
        self.__updateable = self.__health == self.__player_sprite.health
        self.__health = self.__player_sprite.health

    def update_array(self):
        if self.__player_sprite.health <= 0:
            for i in range(1, self.__max_health + 1):
                self._array[1][i] = ModifiedCharacter(BLANK_CHARACTER)
        elif self.__updateable:
            for i in range(self.__health + 1, self.__max_health + 1):
                self._array[1][i] = ModifiedCharacter(BLANK_CHARACTER)
                self.__updateable = False


class BasketballSprite(StandardProjectileSprite, CollisionDestructionMixin, TerrainExitDestructionMixin):
    pass


class DiagonalSprite(LinearEquationSprite, PlayerDamagingSpriteMixin):
    pass


class ArrowSprite(StraightLineEquationSprite, PlayerDamagingSpriteMixin):
    pass


class BallSprite(StandardProjectileSprite, PlayerDamagingSpriteMixin):
    pass


class ShieldSprite(StaticSprite):

    def __init__(self, character: str, position: Position):
        super().__init__([[character]], position)


if __name__ == "__main__":
    import os
    import time
    start = time.perf_counter()
    cs = CharacterStreamSprite("Hi. Well, this took ages to get right.\nI'm glad it's done. Is it cool??? Maybe.\nGoodbye...",
                               Position.ORIGIN, 0.05, sleep_at_newline=2,
                               sleep_at_punctuation_character=1, disappear_on_exhaust=5, sleep=True)
    while 1:
        ctime = time.perf_counter() - start
        if cs.updateable(ctime):
            cs.update_array()
            cs.record_time(ctime)
        print(cs)
        os.system("clear")
        cs.do_sleep()

        # For each sprite: if isinstance(sprite, IntervalFrameUpdateMixin): do.... else: update
