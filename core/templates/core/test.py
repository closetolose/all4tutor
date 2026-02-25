from itertools import product
k=0
n=0
for x in product (sorted('СОЛНЦЕ'), repeat=6):
    x=''.join(x)
    n=n+1
    if x.count('Ц')==2 and x[0]!='О' and x[0]!='Е' and n%2==0:
        k=k+1
print(k)


from itertools import product
k=0
n=0
for x in product(sorted('ЛОГАРИФМ'), repeat=5):
    x=''.join(x)
    n=n+1
    if n%2==0 and x[:2]!='ЛМ' and x.count('И')>=2:
        k=k+1
print(k)

from itertools import product
k=0
n=0
for x in product(sorted('КОМПЬЮТЕР'), repeat=5):
    x=''.join(x)
    n=n+1
    if n%2==1 and x[0]!='Ь' and x.count('К')==2:
        k=k+1
        print(k, n) #58979

from itertools import product
k=0
n=0
for x in product(sorted('ЦАПЛЯ'), repeat=5):
    x=''.join(x)
    n=n+1
    if x.count('Ц')==2 and x.count('А')<=1 and x.count('Л')==0:
        k=k+1
        print(k, n) #319

from itertools import product
k=0
n=0
for x in product(sorted('ГРАНИТ'), repeat=6):
    x=''.join(x)
    n=n+1
    if n%2==1 and (x[0]!='А' and x[0]!='И' and x[0]!='Г') and x.count('А')==1:
        k=k+1
        print(k, n) #23589

from itertools import product
k=0
n=0
for x in product(sorted('СТРОКА'), repeat=5):
    x=''.join(x)
    n=n+1
    if n%2==0 and (x[0]!='А' and x[0]!='С' and x[0]!='Т') and x.count('О')==2:
        k=k+1
        print(k, n) #5058

from itertools import product
k=0
n=0
for x in product(sorted('ЦИФЕРБЛАТ'), repeat=5):
    x=''.join(x)
    n=n+1
    if n%2==1 and (x[0]!='И' and x[0]!='Е' and x[0]!='А') and x.count('Ц')==x.count('Ф'):
        k=k+1
print(k)