import os
import json
from typing import Optional, Literal

from text.character import ModifiedCharacter
from mechanics.constants import BLANK_CHARACTER, NO_DATA_REPLACEMENT, TERRAIN_DIR, BLANK_CHARACTERS
from mechanics.types import CharacterList2D, Numeric
from mechanics.movement.vectors import Vector, UnitVectorEnum, UnitVector
from mechanics.movement.position import Position
from mechanics.sprites.sprite import Sprite
from mechanics.sprites.mixins import (
    UncollidableSpriteMixin, VectorMovementMixin, PositionMovementMixin, TimedPositionMovementMixin,
    AllCharactersUncollidableMixin, TerrainExitDestructionMixin, CollisionDestructionMixin, JumpMovementMixin,
    HealthMixin, PlayerDamagingSpriteMixin
)
from mechanics.sprites.updateablesprite import IntervalFrameUpdateMixin, UpdateableSprite
from mechanics.sprites.gamesprites import PlayerSprite


# TODO: add a "start" coordinate when entering a terrain; make player's coordinate that


class TerrainFragment:

    __slots__ = ("_modified_character", "_uncollidable")

    def __init__(self, character: ModifiedCharacter | str, uncollidable: bool):
        self._modified_character = character if type(character) is ModifiedCharacter \
            else ModifiedCharacter(character)
        self._uncollidable = uncollidable

    def __repr__(self) -> str:
        return f"TerrainFragment({self._modified_character!r})"

    def __str__(self) -> str:
        return NO_DATA_REPLACEMENT if str(self._modified_character) in BLANK_CHARACTERS \
            else self._modified_character.coloured()

    @property
    def character(self) -> str:
        return self._modified_character.character

    @property
    def uncollidable(self) -> bool:
        return self._uncollidable


class Terrain:

    def __init__(self, filename: str, player_sprite: PlayerSprite, uncollidable_characters: Optional[set[str]] = None,
                 ground_characters: Optional[set[str]] = None,
                 player_starting_position: Position = Position.ORIGIN, wall_passing: bool = False):
        self._initial_array = json.loads(open(os.path.join(TERRAIN_DIR, filename)).read())
        self._initial_array = [list(map(ModifiedCharacter, row)) for row in self._initial_array]
        self._uncollidable_characters = uncollidable_characters or set()
        self._ground_characters = ground_characters or set()
        self._array = Terrain.parse_terrain(self._initial_array, self._uncollidable_characters)
        self._height, self._width = len(self._array), len(self._array[0])
        self._player_sprite = player_sprite
        self._player_starting_position = player_starting_position
        self._wall_passing = wall_passing  # All objects can wall pass
        self._player_sprite_shown = True  # TODO: Make useful
        self._sprites: list[Sprite] = []

    def __str__(self) -> str:
        return "\n".join("".join(map(str, row)) for row in self._array)

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def player_sprite(self) -> PlayerSprite:
        return self._player_sprite

    @property
    def sprites(self) -> list[Sprite]:
        return self._sprites

    @staticmethod
    def parse_terrain(terrain: CharacterList2D, uncollidable_characters: set[str]) -> list[list[TerrainFragment]]:
        parsed_terrain = []
        for row in terrain:
            parsed_row = []
            for character in row:
                assert type(character) is ModifiedCharacter
                parsed_row.append(TerrainFragment(character, character in uncollidable_characters))
            parsed_terrain.append(parsed_row)
        return parsed_terrain

    def add_sprite(self, sprite: Sprite,
                   position_above: int | Literal[False] = False,
                   position_below: int | Literal[False] = False,
                   position_left: int | Literal[False] = False,
                   position_right: int | Literal[False] = False):
        # Positions are from the top left corner
        sprite_differences = [position_above, position_below, position_left, position_right]
        assert all(abs(value) == value for value in sprite_differences), "Positive integers only"
        previous_sprite = self._sprites[-1]
        previous_sprite_position = previous_sprite.position
        p_sprite_y, p_sprite_x = previous_sprite_position
        previous_sprite_left, previous_sprite_right = p_sprite_x, p_sprite_x + previous_sprite.width
        previous_sprite_top, previous_sprite_bottom = p_sprite_y, p_sprite_y + previous_sprite.height
        previous_sprite_differences = [
            (previous_sprite_top - 1, previous_sprite_left),
            (previous_sprite_bottom, previous_sprite_left),
            (previous_sprite_top, previous_sprite_left - 1),
            (previous_sprite_top, previous_sprite_right)
        ]
        unit_vector_enums = UnitVectorEnum.__members__.values()
        position = Position.ORIGIN
        for sd, psd, unit_vector_enum in zip(sprite_differences, previous_sprite_differences, unit_vector_enums):
            # sd is short for sprite difference, psd is short for previous sprite difference
            if sd:
                position += Vector(*psd) + UnitVector[unit_vector_enum] * sd  # type: ignore
        sprite.position = position
        self._sprites.append(sprite)

    def remove_sprite(self, sprite: Sprite):
        sprite.alive = False
        self._sprites.remove(sprite)

    def get_sprite_coverage(self, exclude_sprite: Optional[Sprite] = None) -> set[Position]:
        all_sprites = self._sprites + [self._player_sprite]
        if isinstance(exclude_sprite, Sprite):
            all_sprites.remove(exclude_sprite)
        return set(Position(*coordinate) for sprite in all_sprites for coordinate in sprite.get_covered_coordinates())

    def set_position_to(self, position: Position, value: str):
        y, x = position
        self._initial_array[y][x] = ModifiedCharacter(value)
        self.reset()

    def position_outside(self, position: Position) -> bool:
        y, x = position
        if y < 0 or y >= self._height:
            return True
        elif x < 0 or x >= self._width:
            return True
        else:
            return False

    def reposition_outside_position(self, position: Position) -> Position:
        y, x = position
        if y < 0:
            y += self._height
        if x < 0:
            x += self._width
        if y >= self._height:
            y -= self._height
        if x >= self._width:
            x -= self._width
        return Position(y, x)

    def movable_sprite(self, sprite: Sprite, position: Position | Vector) -> bool:
        if isinstance(position, Vector):
            dy, dx = sprite.position + position
        else:
            dy, dx = position

        sprite_coverage = self.get_sprite_coverage(exclude_sprite=sprite)
        for j in range(sprite.height):
            for i in range(sprite.width):
                y, x = j + dy, i + dx
                if self.position_outside(Position(y, x)):
                    if self._wall_passing:
                        sprite.position = self.reposition_outside_position(Position(dy, dx))
                        return True
                    else:
                        self.on_exit(sprite)
                        return False
                elif self._array[y][x].uncollidable or Position(y, x) in sprite_coverage:
                    health_player_sprite = (y, x) in self._player_sprite.get_covered_coordinates()
                    damageable = isinstance(sprite, PlayerDamagingSpriteMixin)
                    if health_player_sprite and isinstance(self._player_sprite, HealthMixin) and damageable:
                        self._player_sprite.health -= 1
                    self.on_collision(sprite)
                    return False
        else:
            return True

    def move_sprite(self, sprite: Sprite, position: Position | Vector):
        if self.movable_sprite(sprite, position):
            if isinstance(sprite, PositionMovementMixin):
                sprite.set_position(position)
            elif isinstance(sprite, VectorMovementMixin):
                sprite.apply_vector(position)

    def draw_sprite(self, sprite: Sprite):
        uncollidable = isinstance(sprite, UncollidableSpriteMixin)
        all_characters_allowed = isinstance(sprite, AllCharactersUncollidableMixin)
        dy, dx = sprite.position
        for j in range(sprite.height):
            for i in range(sprite.width):
                position = Position(j + dy, i + dx)
                if self.position_outside(position) and self._wall_passing:
                    y, x = self.reposition_outside_position(position)
                else:
                    y, x = position
                if str(sprite_character := sprite[j][i]) not in BLANK_CHARACTER:
                    # Prevent characters from being replaced by the non-printable character
                    self._array[y][x] = TerrainFragment(sprite_character, uncollidable)
                elif all_characters_allowed:
                    self._array[y][x] = TerrainFragment(self._array[y][x].character, True)

    def update_sprites(self, time: float):
        for sprite in self._sprites:
            updateable = True
            if isinstance(sprite, UpdateableSprite):
                if isinstance(sprite, IntervalFrameUpdateMixin):
                    if sprite.updateable(time):
                        sprite.record_time(time)
                    else:
                        updateable = False
                if updateable:
                    sprite.update_array()

    def move_timed_sprites(self, time: Numeric):
        for sprite in self._sprites:
            if isinstance(sprite, TimedPositionMovementMixin):
                position = sprite.get_position_at_time(time, self._height, self._width)
                # Make the type-checker happy
                sprite: Sprite
                self.move_sprite(sprite, position)

    def draw_sprites(self):
        for sprite in self._sprites:
            self.draw_sprite(sprite)

    def sleep_updateable_sprites(self):
        for sprite in self._sprites:
            if hasattr(sprite, "do_sleep"):
                sprite.do_sleep()

    def move_player_sprite(self, position: Position | Vector):
        if self.movable_sprite(self._player_sprite, position):
            if type(position) is Position:
                self._player_sprite.set_position(position)
            elif type(position) is Vector:
                self._player_sprite.apply_vector(position)

    def check_jumpable(self):
        # Applies for both start and stop
        for sprite in self._sprites + [self._player_sprite]:
            if isinstance(sprite, JumpMovementMixin):
                bottom_sprite_row = sprite.position[0] + sprite.height - 1
                if sprite.jumping:
                    jumpable = False
                elif bottom_sprite_row == self._height:
                    jumpable = True
                else:
                    #  bottom_sprite_row + 1 —> the row below the bottom row
                    characters_on_bottom_row = [
                        x + sprite.position[1] for x in range(sprite.width)
                        if sprite[sprite.height - 1][x] not in BLANK_CHARACTERS
                    ]
                    for x, value in enumerate(self._array[bottom_sprite_row + 1]):
                        valid_character = x + sprite.position[1] in characters_on_bottom_row
                        if value.character in self._ground_characters and valid_character:
                            jumpable = True
                            break
                    else:
                        jumpable = False
                sprite.jumpable = jumpable

    def draw_player_sprite(self):
        self.draw_sprite(self._player_sprite)

    def on_collision(self, sprite: Sprite):
        if isinstance(sprite, CollisionDestructionMixin):
            self.remove_sprite(sprite)

    def on_exit(self, sprite: Sprite):
        if isinstance(sprite, TerrainExitDestructionMixin):
            self.remove_sprite(sprite)

    def reset(self):
        self._array = Terrain.parse_terrain(self._initial_array, self._uncollidable_characters)

    def paint(self, mapping: Optional[dict] = None, fore_all: str = "", back_all: str = ""):
        assert mapping or fore_all or back_all
        mapping = mapping or {}
        colour_mapping = {
            "fore": {},
            "back": {},
        }
        for colour_type in ("fore", "back"):
            if (colours := mapping.get(colour_type)) is not None:
                for key, value in colours.items():
                    if type(value) is list:
                        colour_mapping[colour_type].update({letter: key for letter in value})
                    else:
                        colour_mapping[colour_type][key] = value

        for y in range(self._height):
            for x in range(self._width):
                modified_character = self._initial_array[y][x]
                character = str(modified_character)
                background_colour = colour_mapping["back"].get(character, "") or back_all
                foreground_colour = colour_mapping["fore"].get(character, "") or fore_all
                if background_colour or foreground_colour:
                    self._initial_array[y][x] = ModifiedCharacter(character,
                                                                  fore_colour_name=foreground_colour.upper(),
                                                                  back_colour_name=background_colour.upper()
                                                                  )
        self.reset()


if __name__ == "__main__":
    s = PlayerSprite([["/", "–", "\\"], ["|", "0", "|"], ["\\", "-", "/"]], Position.ORIGIN)
    # print(s.get_covered_coordinates())

    # t = Terrain("bx2.json", s)
    # t.draw_sprite(s)
    # print(t)
    # print()
    # t.draw_sprite(s, UnitVector.UP)
    # print(t)
    # print()
    # t.reset()
    # t.draw_sprite(s, UnitVector.DOWN)
    # print(t)
    # print()
    # t.reset()
    # t.draw_sprite(s, UnitVector.DOWN)
    # print(t)
    # print()
    # t.reset()
    # t.draw_sprite(s, UnitVector.RIGHT)
    # print(t)
    # print()
    # t.reset()
    # t.draw_sprite(s, UnitVector.RIGHT)
    # print(t)
    # print()
