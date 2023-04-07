import time
import threading
import itertools
from abc import abstractmethod, ABC
from typing import Literal

from mechanics.constants import BLANK_CHARACTER, SENTINEL_CHARACTER, PAUSE_UPDATE_CHARACTERS
from mechanics.movement.vectors import Numeric
from mechanics.movement.position import Position
from mechanics.structures.iterators import CoordinateIterator, ValueIteratorList
from mechanics.sprites.sprite import CharacterList2D, Sprite

"""
Module responsible for updating the visual representation of the sprite.
"""


def format_string_to_array(string: str, sentinel: bool = False,
                           sentence_length: bool = True) -> tuple[int, CharacterList2D] | CharacterList2D:
    sentences = string.split("\n")
    longest_sentence_length = max(map(len, sentences))
    character_array = []
    for sentence in sentences:
        array_row = list(sentence)
        row_length = len(array_row)
        if sentence == sentences[-1] and row_length < longest_sentence_length:
            array_row.extend([SENTINEL_CHARACTER if sentinel else BLANK_CHARACTER]
                             + [BLANK_CHARACTER] * (longest_sentence_length - row_length - 2))
        elif row_length < longest_sentence_length:
            array_row.extend([BLANK_CHARACTER] * (longest_sentence_length - row_length - 1))
        character_array.append(array_row)
    return (character_array, longest_sentence_length) if sentence_length else character_array


def format_values_into_array(array: CharacterList2D, value_list: list[list[str] | str]) -> CharacterList2D:
    format_values = []
    for value in value_list:
        if type(value) is str:
            format_values.append(value)
        elif type(value) is list:
            format_values.extend(value)
    array_string = "\n".join("".join(row) for row in array).format(*format_values)
    return format_string_to_array(array_string, sentinel=False, sentence_length=False)


class IntervalFrameUpdateMixin:

    def __init__(self, update_interval: Numeric):
        self._update_interval = update_interval
        self._last_recorded_interval = 0.0

    def updateable(self, time_elapsed: float) -> bool:
        return time_elapsed - self._last_recorded_interval >= self._update_interval

    def record_time(self, time_elapsed: float):
        self._last_recorded_interval = time_elapsed


class UpdateableSprite(Sprite, ABC):

    @abstractmethod
    def update_array(self):
        pass


class CyclicUpdateSprite(UpdateableSprite):

    def __init__(self, sprite_frames: list[CharacterList2D], position: Position):
        super().__init__(next(sprite_frames := itertools.cycle(sprite_frames)), position)
        self._sprite_frames = sprite_frames

    def update_array(self):
        self._array = next(self._sprite_frames)


class SequentialTextUpdateSprite(UpdateableSprite):

    def __init__(self, text: str,
                 disappear_on_exhaust: Numeric | Literal[False],
                 sleep_at_newline: Numeric | Literal[False],
                 sleep_at_punctuation_character: Numeric | Literal[False],
                 position: Position):
        self._full_array, self._sentence_length = format_string_to_array(text, sentinel=True)
        self._array_iterator = CoordinateIterator(self._full_array, self._sentence_length)
        self._disappear_on_exhaust = disappear_on_exhaust
        self._sleep_at_newline = sleep_at_newline
        self._sleep_on_punctuation_character = sleep_at_punctuation_character
        self._sleep_to_do = 0
        self._sleeping = False
        self._exhausted = False
        self.set_array_blank()
        super().__init__(self._array, position)

    @property
    def sleeping(self) -> bool:
        return self._sleeping

    @property
    def exhausted(self) -> bool:
        return self._array_iterator.exhausted

    def send_sleep(self, sleep_time: Numeric):
        self._sleep_to_do = sleep_time

    def sleep_thread_function(self):
        time.sleep(self._sleep_to_do)
        self._sleep_to_do = 0
        self._sleeping = False
        if self._disappear_on_exhaust and self._array_iterator.exhausted:
            self.set_array_blank()

    def do_sleep(self):
        if self._sleep_to_do:
            self._sleeping = True
            sleep_thread = threading.Thread(target=self.sleep_thread_function)
            sleep_thread.start()

    def update_array(self):
        if not self._sleeping:
            y, x, exhausted = self._array_iterator.next_update()
            if not exhausted:
                self._array = []
                last_printable_row = False
                for sentence_number in range(len(self._full_array)):
                    array_row = self._full_array[sentence_number]
                    if sentence_number == y:  # If the current sentence is the last
                        last_printable_row = True
                        self._array.append(array_row[:x + 1] + [BLANK_CHARACTER] * (self._sentence_length - x - 1))
                        if self._sleep_on_punctuation_character:
                            filtered_array_row = [
                                character for character in self._array[-1] if character not in (BLANK_CHARACTER, SENTINEL_CHARACTER)
                            ]
                            if PAUSE_UPDATE_CHARACTERS.search("".join(filtered_array_row)):
                                self.send_sleep(self._sleep_on_punctuation_character)
                    elif not last_printable_row:
                        self._array.append(array_row + [BLANK_CHARACTER] * (self._sentence_length - len(array_row)))
                    else:
                        self._array.append([BLANK_CHARACTER] * self._sentence_length)
                    if (x == self._sentence_length - 1 or self._full_array[y][x] == BLANK_CHARACTER) and self._sleep_at_newline:
                        self.send_sleep(self._sleep_at_newline)
            elif self._disappear_on_exhaust:
                self.send_sleep(self._disappear_on_exhaust)

    def set_array_blank(self):
        self._array = [[BLANK_CHARACTER] * self._sentence_length for _ in range(len(self._full_array))]


class FunctionInputTextSprite(UpdateableSprite):

    def __init__(self, text: str, sentence_length: int, value_iterator_list: ValueIteratorList,
                 position: Position):
        self._value_iterator_list = value_iterator_list
        self._format_values = value_iterator_list.get_next_values()
        self._initial_array = format_string_to_array(text, sentence_length=False)
        self._sentence_length = sentence_length
        self.update_array()
        super().__init__(self._array, position)

    def update_array(self):
        self._array = format_values_into_array(self._initial_array, self._value_iterator_list.get_next_values())
