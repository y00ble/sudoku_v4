from typing import Counter


def read_puzzle(line_iter):
    line = ""
    while "-SOLUTION" not in line:
        line = next(line_iter)

    puzzle = []
    for row in range(1, 10):
        row_txt = next(line_iter)

        if row in {4, 7}:
            row_txt = next(line_iter)

        digits = [int(i) for i in row_txt.split() if i in "123456789"]
        puzzle.append(digits)

    return puzzle


def get_box_edge_idxs(box):
    br = ((box - 1) // 3) * 3 + 1
    bc = ((box - 1) % 3) * 3 + 1

    edge_offsets = [(0, 1), (1, 2), (2, 1), (1, 0)]

    return [(br + er, bc + ec) for er, ec in edge_offsets]


def box_violates_corners(puzzle, box, d1, d2):
    indices = get_box_edge_idxs(box)
    indices.append(indices[0])

    for (r1, c1), (r2, c2) in zip(indices, indices[1:]):
        digits = {puzzle[r1 - 1][c1 - 1], puzzle[r2 - 1][c2 - 1]}
        if digits == {d1, d2}:
            return True

    return False


BOX_VISIBILITY = {
    1: [2, 3, 4, 7],
    2: [1, 3, 5, 8],
    3: [1, 2, 6, 9],
    4: [5, 6, 1, 7],
    5: [2, 8, 4, 6],
    6: [4, 5, 3, 9],
    7: [8, 9, 1, 4],
    8: [7, 9, 2, 5],
    9: [7, 8, 3, 6],
}


def normalise_wheel(wheel):
    wheel_min_idx = min(i for i, val in enumerate(wheel) if val == min(wheel))
    return tuple([wheel[(wheel_min_idx + i) % 4] for i in range(4)])


all_wheels = []

try:
    with open("log.txt", "r") as fp:
        line_iter = iter(fp.readlines())
        while True:
            puzzle = read_puzzle(line_iter)

            violation_found = False
            for box in range(1, 10):
                (r1, c1), (r2, c2), (r3, c3), (r4, c4) = get_box_edge_idxs(box)
                for other_box in BOX_VISIBILITY[box]:
                    if box_violates_corners(
                        puzzle,
                        other_box,
                        puzzle[r1 - 1][c1 - 1],
                        puzzle[r3 - 1][c3 - 1],
                    ):
                        violation_found = True

                    if box_violates_corners(
                        puzzle,
                        other_box,
                        puzzle[r2 - 1][c2 - 1],
                        puzzle[r4 - 1][c4 - 1],
                    ):
                        violation_found = True

            if not violation_found:
                print("Yay")
                wheels = []
                for box in range(1, 10):
                    wheel = []
                    for r, c in get_box_edge_idxs(box):
                        wheel.append(puzzle[r - 1][c - 1])
                    wheels.append(normalise_wheel(wheel))
                all_wheels.append(tuple(wheels))
except StopIteration:
    pass
for wheels, count in Counter(all_wheels).items():
    if count != 1:
        continue
    print(wheels)
