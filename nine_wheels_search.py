from sudoku.constraints import AntiKing, CornerMark
from sudoku.puzzle import Puzzle

puzzle = Puzzle()

AntiKing(puzzle)

puzzle[1, 2] = 4
puzzle[2, 2] = 3
puzzle[4, 5] = 4
puzzle[5, 5] = 1
puzzle[5, 8] = 4
puzzle[8, 8] = 2
puzzle[2, 5] = 5
puzzle[2, 8] = 6
puzzle[5, 2] = 7
puzzle[8, 2] = 8
puzzle[8, 5] = 9

puzzle[2, 1] = [1, 2]
puzzle[2, 3] = [1, 2]
puzzle[1, 8] = [1, 3]
puzzle[3, 8] = [1, 3]
puzzle[5, 4] = [2, 3]
puzzle[5, 6] = [2, 3]
puzzle[7, 2] = [1, 2]
puzzle[9, 2] = [1, 2]
puzzle[8, 7] = [1, 3]
puzzle[8, 9] = [1, 3]

CornerMark(puzzle, [(2, 4), (2, 6)], 4)
CornerMark(puzzle, [(1, 5), (3, 5)], 3)
CornerMark(puzzle, [(8, 4), (8, 6)], 4)
CornerMark(puzzle, [(7, 5), (9, 5)], 2)

if __name__ == "__main__":
    puzzle.solve(multiprocess=True)
