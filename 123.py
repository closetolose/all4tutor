def to_easy(x):
    dels = []
    d = 2
    while d <= int(x**0.5)+1:
        if x % d == 0:
            dels.append(d)
            x = x // d
        else:
            d += 1
    dels.append(d)
    return dels

print(to_easy(97))