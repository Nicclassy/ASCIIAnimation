import os
import re
import math

SENTINEL_CHARACTER = "\x1e"
BLANK_CHARACTER = "\x1f"
BLANK_CHARACTERS = (BLANK_CHARACTER, SENTINEL_CHARACTER)
NO_DATA_REPLACEMENT = " "

MECHANICS_DIR = os.path.realpath(os.path.dirname(__file__))
PROJECT_DIR = os.path.realpath(os.path.join(__file__, "..", ".."))
SPRITE_DIR = os.path.join(PROJECT_DIR, "sprites")
TERRAIN_DIR = os.path.join(PROJECT_DIR, "terrains")

INTEGER_PATTERN = re.compile(r"-?\d+")
FLOAT_PATTERN = re.compile(r"-?\d+\.\d+")

# Expression substitutions
REPLACE_EXPONENT_SIGN = re.compile(r"(?<=[\w)(])\^(?=[\d(])", flags=re.IGNORECASE)
ADD_MULTIPLICATION_OPERATOR = re.compile(r"(?<=[\d)])(?=[\w(])", flags=re.IGNORECASE)
ADD_PARAMETER_PATTERN = r"(?<=[ +\d-]){}(?=\^\d)?"
FUNCTION_SUBSTITUTIONS = {"cos": math.cos, "sin": math.sin}

TERM_MATCH = re.compile(r"^-?\d+(\.\d+)?\w?(\^\d)?$")
EXTRA_COLOUR = re.compile(r"^[A-Z]+_EX$")

# Formulae
MAX_HEIGHT_FORMULA = ("(V^2 * (sin(θ))^2) / (2g)", "(V^2 * sin(2 * θ)) / (2g)")
HORIZONTAL_RANGE_FORMULA = ("0", "(V^2 * sin(2 * θ)) / g")

# Stop characters
PAUSE_UPDATE_CHARACTERS = re.compile(r"[:.?!] $")
