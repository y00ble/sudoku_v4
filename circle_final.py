import time
from collections import defaultdict

from sudoku.constraints import CountingCircles, NoX, RegionCountConstraint
from sudoku.puzzle import Puzzle

puzzle = Puzzle()

puzzle[1, 5] = 2
puzzle[9, 5] = 7

NoX(puzzle)
CountingCircles(
    puzzle,
    [
        (1, 1),
        (1, 9),
        (2, 1),
        (3, 1),
        (3, 2),
        (3, 4),
        (3, 7),
        (3, 8),
        (3, 9),
        (4, 1),
        (4, 2),
        (4, 3),
        (4, 6),
        (4, 8),
        (4, 9),
        (5, 1),
        (5, 2),
        (5, 6),
        (5, 7),
        (5, 8),
        (5, 9),
        (6, 1),
        (6, 2),
        (6, 4),
        (6, 6),
        (6, 8),
        (6, 9),
        (7, 1),
        (7, 2),
        (7, 3),
        (7, 5),
        (7, 8),
        (7, 9),
        (8, 8),
        (9, 2),
        (9, 9),
    ],
)

# RegionCountConstraint(
#     puzzle,
#     [
#         (1, 1),
#         (1, 2),
#         (1, 8),
#         (1, 9),
#         (2, 1),
#         (2, 2),
#         (2, 8),
#         (2, 9),
#         (8, 1),
#         (8, 2),
#         (8, 8),
#         (8, 9),
#         (9, 1),
#         (9, 2),
#         (9, 8),
#         (9, 9),
#     ],
#     {1: 3, 2: 2, 3: 1, 6: 1, 7: 2, 8: 3, 9: 4},
# )

# puzzle[2, 2] = 9

puzzle.solve(with_terminal=True)
