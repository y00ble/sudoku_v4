from sudoku.constraints import DiagonalNoBlackKropki
from sudoku.puzzle import Puzzle

puzzle = Puzzle()

DiagonalNoBlackKropki(puzzle)

if __name__ == "__main__":
    puzzle.solve(multiprocess=True)
