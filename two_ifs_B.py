def fancy_add(x, y):
    b = x * 2

    if (y > 10 and x < 4):
        b = b + 10

    if (y < 2):
        b = x * x

    c = y * 3

    return b + c