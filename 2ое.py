def to_easy(x):
    dels = []
    d = 2
    while d <= int(x**0.5)+1:
        if x % d == 0:
            dels.append(d)
            x = x // d
        else:
            d += 1
    dels.append(x)
    return dels

def is_prime(x):
    return all(x%d!=0 for d in range(2,x//2+1))

def f(x):
    d_set = set()
    for d in range(2,int(x**0.5)+1):
        if x%d == 0 and is_prime(d)==True:
            d_set.add(d)
            if is_prime(x//d)==True:
                d_set.add(x//d)
    return d_set

for x in range(7305679,10**10):
    d_set = [x for x in f(x)]
    d_set1 = to_easy(x)
    if len(d_set1)==4 and str(sum(d_set1))==str(sum(d_set1))[::-1]:
        print(x,sum(d_set1),d_set1)





