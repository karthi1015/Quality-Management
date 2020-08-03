import random

for i in range(2500):
    print("calculating...", random.sample(range(0, 10), 10), random.sample(range(0, 10), 10), random.sample(range(0, 10), 10))

rand_int = random.randint(0,7)

print("----------------------------------")
if rand_int == 2:
    print("Yeah, allright")
else:
    print("Your design sucks")
