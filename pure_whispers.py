# https://www.youtube.com/watch?v=nH3vat8z9uM
from sudoku.constraints import GermanWhisper
from sudoku.puzzle import Puzzle

puzzle = Puzzle()

puzzle[1, 5] = 1
puzzle[2, 2] = 5
puzzle[5, 1] = 6
puzzle[5, 9] = 9
puzzle[7, 3] = 3
puzzle[8, 8] = 3
puzzle[9, 5] = 3

GermanWhisper(puzzle, [(8, 1), (7, 1), (7, 2), (8, 3), (9, 3), (9, 2)])
GermanWhisper(
    puzzle,
    [
        (6, 3),
        (5, 2),
        (4, 3),
        (3, 4),
        (2, 5),
        (1, 6),
        (1, 7),
        (2, 8),
        (3, 8),
        (4, 7),
        (5, 6),
        (6, 6),
        (7, 6),
        (8, 5),
        (7, 4),
    ],
)
GermanWhisper(puzzle, [(4, 5), (4, 6), (3, 7)])
GermanWhisper(puzzle, [(5, 8), (6, 9), (7, 8), (7, 7), (8, 7), (9, 6)])

puzzle.solve(with_terminal=True)
