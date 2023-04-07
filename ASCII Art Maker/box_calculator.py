s = 0.2

# For x = 8, y = 13, s = 0.2, D = 4
# 8w + 7/5 = 3.3
w = (3.3 - 7 / 5) / 8
# 13h = 2
h = 2 / 13


def get_height_ratio(y: int) -> float:
    x = (w * y + (y - 1) * s) / h
    return int(x + (int(x) != x))


height = 25
print("Character height: {}\nCharacter width: {}".format(h, w))
print("{} characters tall, {} characters wide".format(height, get_height_ratio(height)))
