from math import dist
f = open("27_A_23766.txt")

data = []

for s in f:
    x,y = [float(k) for k in s.split()]
    data.append([x,y])
print(len(data))
clusters = []
while data:
    clusters.append([data.pop(0)])
    for p in clusters[-1]:
        sosedi = [p1 for p1 in data if dist(p,p1)<1]
        clusters[-1].extend(sosedi)
        for p in sosedi:
            data.remove(p)

def centroid(cluster):
    m = []
    for p in cluster:
        sm = sum(dist(p,p1) for p1 in cluster)
        m.append([sm,p])
    return min(m)[1]

print(centroid(clusters[0]))
print(centroid(clusters[1][0]))


