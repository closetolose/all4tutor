def f(s,h):
    if s>=67:
        return h%2==0
    if h==0:
        return 0
    m = [f(s+1,h-1), f(s+4,h-1), f(s*3,h-1)]
    return any(m) if h%2!=0 else all(m)
for s in range(1,67):
    if f(s,2)==1:
        print(s)