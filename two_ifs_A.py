def fancy_add(x, y):
    b = x * 2

    if (y > 10 and x < 1):
        b = b + 10

    if (y < 2 and x > 3):
        b = x * x

    c = y * 3

    return b + c