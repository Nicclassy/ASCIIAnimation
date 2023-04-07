import os
import json
from typing import Optional

from typing_extensions import Self

from text.character import ModifiedCharacter
from mechanics.constants import SPRITE_DIR, BLANK_CHARACTERS
from mechanics.types import CharacterList2D
from mechanics.movement.position import Position

# TODO: consider hierachcy of objects; last to be placed goes on top of the other objects
# TODO: cursor hiding/moving? force cursor to be next to selection???


class Sprite:

    """
    A class which stores textual representations of sprites within lists.
    """

    def __init__(self, data: str | CharacterList2D, position: Position):
        if type(data) is str:
            self._array = json.loads(open(os.path.join(SPRITE_DIR, data)).read())
        else:
            self._array = data
        self._array = [list(map(ModifiedCharacter, row)) for row in self._array]
        self._height, self._width = len(self._array), len(self._array[0])
        self._position = Position(*position)
        self._alive = True

    @property
    def position(self) -> Position:
        return self._position

    @position.setter
    def position(self, position: Position):
        self._position = position

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    @property
    def alive(self) -> bool:
        return self._alive

    @alive.setter
    def alive(self, value: bool):
        self._alive = value

    def __getitem__(self, index: int) -> str | list[ModifiedCharacter]:
        return self._array[index]

    def __str__(self) -> str:
        # Not generally used; more often the sprites are drawn onto the terrain
        string_output = "\n".join("".join(map(str, row)) for row in self._array)
        for blank_character in BLANK_CHARACTERS:
            string_output = string_output.replace(blank_character, " ")
        return string_output

    def transpose(self):
        previous_array = self._array.copy()
        for y in range(self._height):
            for x in range(self._width):
                self._array[y][x] = previous_array[x][y]

    def get_covered_coordinates(self) -> set:
        dy, dx = self._position
        return set((y + dy, x + dx) for y in range(self._height)
                   for x in range(self._width) if self[y][x] not in BLANK_CHARACTERS)

    def collide(self, other: Self) -> set[tuple[int, int]]:
        return self.get_covered_coordinates() & other.get_covered_coordinates()

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
                character = str(self._array[y][x])
                background_colour = colour_mapping["back"].get(character, "") or back_all
                foreground_colour = colour_mapping["fore"].get(character, "") or fore_all
                if background_colour or foreground_colour:
                    self._array[y][x] = ModifiedCharacter(character,
                                                          fore_colour_name=foreground_colour.upper(),
                                                          back_colour_name=background_colour.upper())
