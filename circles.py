import itertools
from collections import defaultdict

from tqdm import tqdm as tq

from sudoku.constraints import NoX, RegionCountConstraint
from sudoku.exceptions import SudokuContradiction
from sudoku.puzzle import Puzzle

unique_circle_solutions = []

for flip_left, flip_right, flip_top_and_bottom in tq(
    itertools.product([True, False], repeat=3)
):
    grouped_by_circle_pattern = defaultdict(list)
    puzzle = Puzzle()
    NoX(puzzle)

    l1, l2 = 1, 2
    r1, r2 = 8, 9
    t1, t2 = 1, 2
    b1, b2 = 8, 9

    if flip_left:
        l1, l2 = l2, l1
    if flip_right:
        r1, r2 = r2, r1
    if flip_top_and_bottom:
        t1, t2 = t2, t1
    if flip_top_and_bottom:
        b1, b2 = b2, b1

    corner_circles = [
        (t1, l2),
        (t1, r2),
        (t2, l2),
        (b1, r1),
        (b2, l1),
        (b2, r2),
    ]
    puzzle[t1, l1] = [2, 3]
    puzzle[t1, l2] = [6, 7, 8]
    puzzle[t1, r1] = 9
    puzzle[t1, r2] = [6, 7, 8]
    puzzle[t2, l1] = 9
    puzzle[t2, l2] = [6, 7, 8]
    puzzle[t2, r1] = [2, 3]
    puzzle[t2, r2] = 1
    puzzle[b1, l1] = 1
    puzzle[b1, l2] = [2, 3]
    puzzle[b1, r1] = [6, 7, 8]
    puzzle[b1, r2] = 9
    puzzle[b2, l1] = [6, 7, 8]
    puzzle[b2, l2] = 9
    puzzle[b2, r1] = 1
    puzzle[b2, r2] = [6, 7, 8]

    # Digits to constrain the outside boxes
    puzzle[t1, 5] = 2
    puzzle[b2, 5] = 7

    RegionCountConstraint(
        puzzle,
        [
            (1, 1),
            (1, 2),
            (1, 8),
            (1, 9),
            (2, 1),
            (2, 2),
            (2, 8),
            (2, 9),
            (8, 1),
            (8, 2),
            (8, 8),
            (8, 9),
            (9, 1),
            (9, 2),
            (9, 8),
            (9, 9),
        ],
        {1: 3, 2: 2, 3: 1, 6: 1, 7: 2, 8: 3, 9: 4},
    )

    # Coverees to make 9s feasible on the phisomephel ring
    for cell_collection in [
        [(3, 4), (3, 5), (3, 6)],
        [(4, 3), (5, 3), (6, 3)],
        [(7, 4), (7, 5), (7, 6)],
        [(4, 7), (5, 7), (6, 7)],
    ]:
        coveree = []
        for cell in cell_collection:
            row, column = cell
            for digit in [6, 7, 8]:
                coveree.append(puzzle.possible_index(row, column, digit))
        puzzle.add_coveree(coveree)

    try:
        puzzle.solve()
    except SudokuContradiction:
        continue

    solutions_list = list(puzzle.solutions)
    for solution_idx, solution in enumerate(solutions_list):
        circle_cells = []
        for row in range(3, 8):
            for col in range(3, 8):
                circle = False
                for digit in range(5, 9):
                    index = puzzle.possible_index(row, col, digit)
                    if solution[index]:
                        circle = True

                if circle:
                    circle_cells.append((row, col))
        grouped_by_circle_pattern[tuple(circle_cells)].append(solution_idx)

    print("Solutions grouped by circle pattern:")
    for pattern, indices in grouped_by_circle_pattern.items():
        print(indices, ":", pattern)
        if len(indices) == 1:
            unique_circle_solutions.append(solutions_list[indices[0]])

for solution in unique_circle_solutions:
    puzzle = Puzzle()
    print("-" * 30)
    puzzle.simple_draw(solution)
