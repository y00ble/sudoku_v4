from sudoku.puzzle import Puzzle

puzzle = Puzzle()
givens = [
    [0, 2, 0, 0, 0, 6, 0, 8, 0],
    [0, 9, 6, 0, 1, 5, 0, 0, 2],
    [5, 0, 7, 0, 3, 0, 4, 0, 0],
    [0, 3, 0, 5, 0, 0, 0, 0, 4],
    [2, 0, 1, 4, 0, 8, 9, 0, 3],
    [8, 0, 0, 0, 0, 9, 0, 1, 0],
    [0, 0, 5, 0, 9, 0, 2, 0, 8],
    [9, 0, 0, 1, 8, 0, 3, 5, 0],
    [0, 6, 0, 2, 0, 0, 0, 9, 0],
]

for i, digits in enumerate(givens):
    for j, digit in enumerate(digits):
        if digit != 0:
            row = i + 1
            column = j + 1
            puzzle[row, column] = digit

if __name__ == "__main__":
    puzzle.solve(multiprocess=True)
