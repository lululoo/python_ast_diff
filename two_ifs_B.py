def fancy_add(x, y):
    c = y * 3
    b = x * 2

    if (y > 1 and x < 1):
        b = b - 10        

    if (y < 4 and x > 3):
        b = x * x

    return b + c + x