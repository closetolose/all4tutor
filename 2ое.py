from ipaddress import ip_network
net = ip_network("172.16.96.0/255.255.224.0",0).hosts()
k = 0
for x in net:
    x = bin(int(x))[2:].zfill(32)
    if x.count("1")%2==0:
        k = k+1
        print(x)
