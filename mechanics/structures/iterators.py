import operator
from abc import ABC, abstractmethod
from typing import Any, Callable

from mechanics.constants import BLANK_CHARACTER, SENTINEL_CHARACTER
from mechanics.types import CharacterList2D


class ValueIterator(ABC):

    @property
    @abstractmethod
    def exhausted(self) -> bool:
        pass

    @abstractmethod
    def reset_iterator(self):
        pass

    @abstractmethod
    def next_update(self) -> Any:
        pass


class CoordinateIterator(ValueIterator):

    def __init__(self, array: CharacterList2D, sentence_length: int):
        self.__array = array
        self.__sentence_length = sentence_length
        self.__sentence_amount = len(array)
        self.__exhausted = False
        self.__started = False
        self.__list_y, self.__list_x = None, None

    @property
    def exhausted(self) -> bool:
        return self.__exhausted

    def reset_iterator(self):
        self.__exhausted = False
        self.__started = False
        self.__list_y, self.__list_x = None, None

    def next_update(self) -> tuple[int, int, bool]:
        if not self.__started:
            self.__started = True
            self.__list_y, self.__list_x = 0, 0
        elif not self.__exhausted:
            if self.__list_x == self.__sentence_length - 1 and self.__list_y == self.__sentence_amount - 1:
                self.__exhausted = True
            elif self.__list_x == self.__sentence_length - 1:
                self.__list_x = 0
                self.__list_y += 1
            elif (next_character := self.__array[self.__list_y][self.__list_x]) == BLANK_CHARACTER:
                self.__list_x = 0
                self.__list_y += 1
            elif next_character == SENTINEL_CHARACTER:
                self.__exhausted = True
            else:
                self.__list_x += 1
        return self.__list_y, self.__list_x, self.__exhausted


class FunctionValueIterator(ValueIterator):

    def __init__(self, function: Callable, exhausted_condition: Callable):
        self.__function = function
        self.__function_value = function()
        self.__exhausted_condition = exhausted_condition
        self.__exhausted = False

    @property
    def exhausted(self) -> bool:
        return self.__exhausted

    def reset_iterator(self):
        self.__exhausted = False

    def next_update(self) -> Any:
        if self.__exhausted_condition(function_value := self.__function()) and not self.__exhausted:
            self.__exhausted = True
            self.__function_value = function_value
        elif not self.__exhausted:
            self.__function_value = function_value
        return self.__function_value


class ListValueIterator(ValueIterator):

    def __init__(self, value_list: list, exhausted_value: str):
        self.__intial_value_list = value_list.copy()
        self.__value_list = iter(self.__intial_value_list)
        self.__current_value = next(self.__value_list)
        self.__exhausted_value = exhausted_value
        self.__exhausted = False

    @property
    def exhausted(self) -> bool:
        return self.__exhausted

    def reset_iterator(self):
        self.__value_list = iter(self.__intial_value_list)
        self.__exhausted = False

    def next_update(self) -> Any:
        if (next_value := next(self.__value_list, None)) is None:
            self.__exhausted = True
            self.__current_value = self.__exhausted_value
        else:
            self.__current_value = next_value
        return self.__current_value


class ValueIteratorList:

    def __init__(self, value_iterators: list[ValueIterator]):
        self.__value_iterators = value_iterators

    def get_next_values(self) -> list[str]:
        return list(map(operator.methodcaller("next_update"), self.__value_iterators))
