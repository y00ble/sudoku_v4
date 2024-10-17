from sudoku.constraints import GermanWhisper, KillerCage
from sudoku.puzzle import Puzzle

puzzle = Puzzle()

KillerCage(puzzle, [(1, 1), (1, 2)], 11)

KillerCage(puzzle, [(1, 8), (1, 9), (2, 9)], 18)

KillerCage(puzzle, [(5, 1), (6, 1), (7, 1)], 18)

KillerCage(puzzle, [(9, 1), (9, 2), (9, 3)], 16)

KillerCage(puzzle, [(7, 5), (8, 4), (8, 5), (9, 4), (9, 5)], 18)

KillerCage(puzzle, [(8, 6), (8, 7), (9, 6)], 18)

KillerCage(puzzle, [(9, 7), (9, 8)], 10)

GermanWhisper(puzzle, [(4, 1), (3, 1), (2, 1), (3, 2)])

GermanWhisper(puzzle, [(4, 2), (3, 1)])

GermanWhisper(puzzle, [(2, 3), (1, 4), (2, 5)])

GermanWhisper(puzzle, [(3, 3), (2, 4), (3, 5)])

GermanWhisper(puzzle, [(5, 2), (4, 3), (3, 4), (4, 5), (5, 6)])

GermanWhisper(puzzle, [(6, 2), (5, 3), (4, 4), (5, 5), (6, 6)])

GermanWhisper(puzzle, [(5, 4), (6, 4), (7, 4)])

GermanWhisper(puzzle, [(6, 7), (5, 8), (6, 9)])

GermanWhisper(puzzle, [(7, 7), (6, 8), (7, 9)])

GermanWhisper(puzzle, [(7, 8), (8, 8)])

puzzle[7, 4] = 7

puzzle.solve(with_terminal=True)
