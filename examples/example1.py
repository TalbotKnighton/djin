import djin.math_objects as mo
import numpy as np

a = mo.VectorR3(data=(1, 0, 0))
b = mo.VectorR3.from_array(np.array([0, 1, 0]))
c = np.dot(a, b)

print(f"{a = }")
print(f"{b = }")
print(f"{c = }")
print(f"{a.model_dump_json() = }")
