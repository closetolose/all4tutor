s = [int(x) for x in open("17_19249.txt")]
max_s = max(x for x in s if len(str(abs(x)))==5 and abs(x)%100==43)
k = 0
min_sum = 10**20
for i in range(len(s)-2):
    if (len(str(abs(s[i])))==5 and abs(s[i])%100==43)+(len(str(abs(s[i+1])))==5 and abs(s[i+1])%100==43)+(len(str(abs(s[i+2])))==5 and abs(s[i+2])%100==43)>=1:
        if s[i]**2 + s[i+1]**2 + s[i+2]**2 <= max_s**2:
            k = k + 1
            min_sum = min(min_sum,s[i]**2 + s[i+1]**2 + s[i+2]**2)
print(k,min_sum)

