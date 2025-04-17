import numpy as np
from helpers.transform import Transform

np.set_printoptions(precision=3, suppress=True)

def print_matrix(label, matrix):
    print(f"\n{label}:")
    print(matrix)

def main():
    # Translation Test
    trans = Transform.translation(1.0, 2.0, 3.0)
    print_matrix("Translation Matrix", trans)

    # Rotation Test (90 deg around X)
    rot = Transform.rotation(90, 0, 0)
    print_matrix("Rotation Matrix (90 deg X)", rot)

    # Scale Test
    scale = Transform.scale(2.0, 2.0, 2.0)
    print_matrix("Scale Matrix", scale)

    # Matrix Multiplication Test
    combined = Transform.multiply(trans, Transform.multiply(rot, scale))
    print_matrix("Combined Matrix (T * R * S)", combined)

    # Inverse Test
    inv = Transform.inverse(combined)
    print_matrix("Inverse of Combined Matrix", inv)

    # Identity check
    identity = Transform.multiply(combined, inv)
    print_matrix("Combined * Inverse (Should be Identity)", identity)

    # Compose Test
    composed = Transform.compose((1, 2, 3), (90, 0, 0), (2, 2, 2))
    print_matrix("Composed Matrix (via compose)", composed)

    # Look At Matrix
    look = Transform.look_at((0, 0, 0), (0, 0, -1))
    print_matrix("LookAt Matrix", look)

    # Perspective Matrix
    perspective = Transform.perspective(np.pi / 2, 1.0, 0.1, 100.0)
    print_matrix("Perspective Projection Matrix", perspective)

    # Orthographic Matrix
    ortho = Transform.orthographic(-1, 1, -1, 1, 0.1, 100.0)
    print_matrix("Orthographic Projection Matrix", ortho)

if __name__ == "__main__":
    main()
