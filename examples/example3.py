from itertools import product
from djin import math_objects as mo

u = mo.Quaternion(data=(0, 0, 0, 1))
i = mo.Quaternion(data=(1, 0, 0, 0))
j = mo.Quaternion(data=(0, 1, 0, 0))
k = mo.Quaternion(data=(0, 0, 1, 0))

sequence = [i, j, k, u]


def identify(q: mo.Quaternion) -> str:
    if q == i:
        return "i"
    if q == -i:
        return "-i"
    if q == j:
        return "j"
    if q == -j:
        return "-j"
    if q == k:
        return "k"
    if q == -k:
        return "-k"
    if q == u:
        return "1"
    if q == -u:
        return "-1"
    raise ValueError


for q1, q2 in product(sequence, sequence):
    print(f"{identify(q1)}*{identify(q2)}={identify(q1 * q2)}")

print(0 * i + 1 * j + 2 * k + 3 * u)
print(u + u)
