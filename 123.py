from turtle import *
screensize(5000,5000)
speed(100)
m = 30

for i in range(2):
    forward(14*m) # fd(14*m)
    left(270) # lt(270)
    back(12*m) # bk(12*m)
    right(90) # rt(90)
up()
fd(9*m)
right(90)
back(7*m)
left(90)
down()
for i in range(2):
    fd(13*m)
    rt(90)
    fd(6*m)
    rt(90)

up()
tracer(0)
for x in range(-50,50):
    for y in range(-50,50):
        goto(x*m,y*m)
        dot(4)

done()






