from colorama import Fore, Back

from mechanics.constants import EXTRA_COLOUR

FORE_COLOUR_LIST = [attr for attr in dir(Fore) if attr.isupper() and attr.isalpha()]
BACK_COLOUR_LIST = [attr for attr in dir(Back) if attr.isupper() and attr.isalpha()]
EXTRA_FORE_COLOURS = [attr for attr in dir(Fore) if EXTRA_COLOUR.match(attr)]
EXTRA_BACK_COLOURS = [attr for attr in dir(Back) if EXTRA_COLOUR.match(attr)]
FORE_COLOUR_LIST.extend(EXTRA_FORE_COLOURS)
BACK_COLOUR_LIST.extend(EXTRA_BACK_COLOURS)


def _get_colour(colour_type: type[Fore] | type[Back], colour_name: str) -> str:
    return getattr(colour_type, colour_name)


def _format_colour_name(colour_name: str) -> str:
    if EXTRA_COLOUR.match(colour_name):
        return colour_name[:-3]
    else:
        return colour_name


FORE_COLOUR_MAPPING = {
    _format_colour_name(colour_name): _get_colour(Fore, colour_name) for colour_name in FORE_COLOUR_LIST
}
BACK_COLOUR_MAPPING = {
    _format_colour_name(colour_name): _get_colour(Back, colour_name) for colour_name in BACK_COLOUR_LIST
}
FORE_COLOUR_MAPPING[""] = ""
BACK_COLOUR_MAPPING[""] = ""


def colour_name_to_fore_colour(colour_name: str):
    return FORE_COLOUR_MAPPING[colour_name]


def colour_name_to_back_colour(colour_name: str):
    return BACK_COLOUR_MAPPING[colour_name]
