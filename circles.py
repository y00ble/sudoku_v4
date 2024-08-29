from collections import defaultdict

from sudoku.constraints import NoX
from sudoku.puzzle import Puzzle

puzzle = Puzzle()

puzzle[1, 1] = 8
puzzle[1, 2] = 9
puzzle[1, 8] = 1
puzzle[1, 9] = 7
puzzle[2, 1] = 1
puzzle[2, 2] = [6, 7]
puzzle[2, 8] = [2, 3]
puzzle[2, 9] = 9
puzzle[8, 1] = 2
puzzle[8, 2] = [6, 7]
puzzle[8, 8] = 9
puzzle[8, 9] = 8
puzzle[9, 1] = 9
puzzle[9, 2] = 8
puzzle[9, 8] = [2, 3]
puzzle[9, 9] = 1

# puzzle[1, 3] = 5
# puzzle[1, 4] = 6
# puzzle[1, 5] = 2
# puzzle[1, 6] = 3
# puzzle[1, 7] = 4
# board[7, 6] = 6

# Debugging coveree bifurcation
# board[3, 4] = 1
# board[4, 5] = 5
# board[9, 4] = 7

NoX(puzzle)

puzzle.solve(with_terminal=True)

grouped_by_circle_pattern = defaultdict(list)
for solution_idx, solution in enumerate(puzzle.solutions):
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
