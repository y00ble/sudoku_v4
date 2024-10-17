from sudoku.constraints import CountingCircles, GermanWhisper
from sudoku.puzzle import Puzzle

puzzle = Puzzle()

CountingCircles(
    puzzle,
    [
        (1, 2),
        (1, 9),
        (2, 1),
        (2, 2),
        (2, 3),
        (2, 4),
        (3, 5),
        (3, 8),
        (4, 6),
        (4, 7),
        (4, 8),
        (5, 9),
        (6, 1),
        (6, 2),
        (6, 3),
        (6, 8),
        (7, 2),
        (7, 4),
        (7, 7),
        (8, 2),
        (8, 3),
        (8, 4),
        (8, 6),
        (9, 5),
    ],
)
GermanWhisper(
    puzzle,
    [
        (2, 2),
        (1, 2),
        (2, 3),
        (2, 4),
        (3, 5),
        (4, 6),
        (4, 7),
        (3, 8),
        (4, 8),
        (5, 9),
        (6, 8),
        (7, 7),
        (8, 6),
        (9, 5),
        (8, 4),
        (8, 3),
        (7, 2),
        (6, 1),
        (6, 2),
    ],
)
GermanWhisper(puzzle, [(4, 1), (5, 1), (5, 2), (5, 3)])
GermanWhisper(puzzle, [(3, 2), (4, 2), (5, 2)])
GermanWhisper(puzzle, [(5, 4), (5, 5), (5, 6)])
GermanWhisper(puzzle, [(5, 5), (6, 5), (7, 5), (8, 5)])
GermanWhisper(puzzle, [(2, 7), (2, 8), (2, 9)])
GermanWhisper(puzzle, [(9, 6), (8, 7), (8, 8)])
GermanWhisper(puzzle, [(7, 9), (8, 9)])

puzzle.solve(with_terminal=True)
