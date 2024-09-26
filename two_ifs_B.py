def fancy_add(x, y):
    c = y * 3
    b = x * 2

    if (y > 10 and x < 1):
        b = b - 10
        b = b + 2

    if (y < 4):
        b = x * x

    return b