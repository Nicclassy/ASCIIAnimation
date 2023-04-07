from typing import Any

from colorama import Style

from text.colours import colour_name_to_fore_colour, colour_name_to_back_colour


class ModifiedCharacter:

    """Class used to store 'coloured' strings."""

    __slots__ = ("_character", "_fore_colour", "_back_colour")

    def __init__(self, character: str, fore_colour_name: str = "", back_colour_name: str = ""):
        self._character = character
        self._fore_colour = colour_name_to_fore_colour(fore_colour_name)
        self._back_colour = colour_name_to_back_colour(back_colour_name)

    def __hash__(self) -> int:
        return hash(self._character)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            return self._character == other
        else:
            return False

    def __repr__(self) -> str:
        return repr(self.coloured())

    def __str__(self) -> str:
        return self._character

    def coloured(self) -> str:
        return self._fore_colour + self._back_colour + self._character + Style.RESET_ALL

    @property
    def character(self) -> str:
        return self._character


# a = ModifiedCharacter("y", "GREEN", "RED")
# b = ModifiedCharacter("x")
# print(a, b)
