from constants import NO_DATA, PERMITTED_CHARACTER_UNICODES

SHIFTED_KEYS = {
    "1": "!", "2": "@", "3": "#",
    "4": "$", "5": "%", "6": "^",
    "7": "&", "8": "*", "9": "(",
    "0": ")", "-": "_", "=": "+",
    "[": "{", "]": "}", "\\": "|",
    ";": ":", "'": '"', ",": "<",
    ".": ">", "/": "?", "`": "~",
}

SHIFTED_KEYS.update({chr(unicode + 32): chr(unicode) for unicode in range(65, 91)})

ALT_KEYS = "`¡™£¢∞§¶•ªº–≠œ∑´´†¥¨ˆˆπ“‘«åß∂ƒ©˙∆˚¬…æΩ≈ç√∫˜˜≤≥ç"
ALT_KEY_EQUIVALENTS = "`1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./"
SHIFT_ALT_KEYS = "`⁄€‹›ﬁﬂ‡°·‚—±Œ„´‰ˇÁ¨ˆØ∏”’»ÅÍÎÏ˝ÓÔÒÚÆ¸˛Ç◊ı˜Â¯˘¿"

ALTED_KEYS = dict(zip(ALT_KEY_EQUIVALENTS, ALT_KEYS))
SHIFT_ALTED_KEYS = dict(zip(ALT_KEY_EQUIVALENTS, SHIFT_ALT_KEYS))

PERMITTED_CHARACTER_UNICODES.extend(map(ord, ALT_KEYS + SHIFT_ALT_KEYS))


def shift_key(key: str) -> str:
    return SHIFTED_KEYS.get(key, NO_DATA)


def alt_key(key: str) -> str:
    return ALTED_KEYS.get(key, NO_DATA)


def shift_alt_key(key: str) -> str:
    return SHIFT_ALTED_KEYS.get(key, NO_DATA)
