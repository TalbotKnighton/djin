import numpy as np
from djin import math_objects as mo

xhat = mo.VectorR3(data=(1, 0, 0))
yhat = mo.VectorR3(data=(0, 1, 0))
zhat = mo.VectorR3(data=(0, 0, 1))

rx = mo.Rotation.from_euler(
    seq="xyz",
    angles=(90, 0, 0),
    degrees=True,
)
ry = mo.Rotation.from_euler(
    seq="xyz",
    angles=(0, 90, 0),
    degrees=True,
)
rz = mo.Rotation.from_euler(
    seq="xyz",
    angles=(0, 0, 90),
    degrees=True,
)

q_rx = mo.Quaternion.from_rotation(rx)
q_ry = mo.Quaternion.from_rotation(ry)
q_rz = mo.Quaternion.from_rotation(rz)

# Show rotation matrices
print("rx(+90 deg):\n", rx.as_matrix().astype(int))
print("ry(+90 deg):\n", ry.as_matrix().astype(int))
print("rz(+90 deg):\n", rz.as_matrix().astype(int))

# Test them against the VectorR3 objects
print("rx(+90 deg)@xhat:", np.array(rx.as_matrix() @ xhat).astype(int))
print("ry(+90 deg)@xhat:", np.array(ry.as_matrix() @ xhat).astype(int))
print("rz(+90 deg)@xhat:", np.array(rz.as_matrix() @ xhat).astype(int))
print("rx(+90 deg)@yhat:", np.array(rx.as_matrix() @ yhat).astype(int))
print("ry(+90 deg)@yhat:", np.array(ry.as_matrix() @ yhat).astype(int))
print("rz(+90 deg)@yhat:", np.array(rz.as_matrix() @ yhat).astype(int))
print("rx(+90 deg)@zhat:", np.array(rx.as_matrix() @ zhat).astype(int))
print("ry(+90 deg)@zhat:", np.array(ry.as_matrix() @ zhat).astype(int))
print("rz(+90 deg)@zhat:", np.array(rz.as_matrix() @ zhat).astype(int))

# Show the corresponding quaternions
print(f"{q_rx = }")
print(f"{q_ry = }")
print(f"{q_rz = }")

# Test the quaternion multiplication
print(
    "q_rx@xhat@q_rx.conj():",
    np.array((q_rx * xhat * q_rx.conj()).vector).astype(int),
)
print(
    "q_ry@xhat@q_ry.conj():",
    np.array((q_ry * xhat * q_ry.conj()).vector).astype(int),
)
print(
    "q_rz@xhat@q_rz.conj():",
    np.array((q_rz * xhat * q_rz.conj()).vector).astype(int),
)
print(
    "q_rx@yhat@q_rx.conj():",
    np.array((q_rx * yhat * q_rx.conj()).vector).astype(int),
)
print(
    "q_ry@yhat@q_ry.conj():",
    np.array((q_ry * yhat * q_ry.conj()).vector).astype(int),
)
print(
    "q_rz@yhat@q_rz.conj():",
    np.array((q_rz * yhat * q_rz.conj()).vector).astype(int),
)
print(
    "q_rx@zhat@q_rx.conj():",
    np.array((q_rx * zhat * q_rx.conj()).vector).astype(int),
)
print(
    "q_ry@zhat@q_ry.conj():",
    np.array((q_ry * zhat * q_ry.conj()).vector).astype(int),
)
print(
    "q_rz@zhat@q_rz.conj():",
    np.array((q_rz * zhat * q_rz.conj()).vector).astype(int),
)
