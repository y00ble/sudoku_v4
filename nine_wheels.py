from sudoku.constraints import AntiKing, Wheel
from sudoku.puzzle import Puzzle

puzzle = Puzzle()

AntiKing(puzzle)
Wheel(puzzle, (2, 2), (1, 4, 2, 9))
Wheel(puzzle, (2, 5), (3, 4, 6, 9))
Wheel(puzzle, (2, 8), (1, 8, 3, 7))
Wheel(puzzle, (5, 2), (5, 8, 6, 9))
Wheel(puzzle, (5, 5), (2, 4, 3, 7))
Wheel(puzzle, (5, 8), (5, 9, 6, 7))
Wheel(puzzle, (8, 2), (1, 5, 2, 6))
Wheel(puzzle, (8, 5), (2, 7, 8, 4))
Wheel(puzzle, (8, 8), (1, 5, 3, 8))

if __name__ == "__main__":
    puzzle.solve(multiprocess=True)
