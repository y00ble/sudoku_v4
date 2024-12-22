from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np

from sudoku.exceptions import SudokuContradiction

if TYPE_CHECKING:
    from .puzzle import DIGITS, Puzzle

DIGITS = list(range(1, 10))


class Constraint(ABC):

    def __init__(self, puzzle: Puzzle, cells: list[tuple]):
        self.puzzle = puzzle
        self.cells = np.array(cells)
        puzzle.constraints.append(self)
        self.add_contradictions()
        self.initialise_on_grid()

    @abstractmethod
    def add_contradictions(self) -> None:
        """Add puzzle contradictions for values that break this constraint."""
        ...

    @abstractmethod
    def initialise_on_grid(self) -> None:
        """Mark some of the puzzle's numbers as impossible."""
        ...

    def act_on_grid(self) -> None:
        """
        Update the grid's possibles and finalised state.

        Called periodically thoughout the solve.
        """
        pass


class NoRepeatsConstraint(Constraint):

    def add_contradictions(self) -> None:
        for c1, c2 in itertools.combinations(self.cells, 2):
            for value in DIGITS:
                i1 = self.puzzle.possible_index(*c1, value)
                i2 = self.puzzle.possible_index(*c2, value)
                self.puzzle.add_contradiction(i1, i2)

    def initialise_on_grid(self) -> None:
        pass


class Row(NoRepeatsConstraint):

    def __init__(self, puzzle: Puzzle, row: int):
        super().__init__(puzzle, [(row, i) for i in DIGITS])


class Column(NoRepeatsConstraint):

    def __init__(self, puzzle: Puzzle, column: int):
        super().__init__(puzzle, [(i, column) for i in DIGITS])


class Box(NoRepeatsConstraint):

    def __init__(self, puzzle: Puzzle, box: int):
        rows = [((box - 1) // 3) * 3 + i + 1 for i in range(3)]
        cols = [((box - 1) % 3) * 3 + i + 1 for i in range(3)]
        super().__init__(puzzle, [(i, j) for i in rows for j in cols])
        super().__init__(puzzle, [(i, j) for i in rows for j in cols])


class GermanWhisper(Constraint):

    def initialise_on_grid(self) -> None:
        indices = [
            self.puzzle.possible_index(row, col, 5) for row, col in self.cells
        ]
        self.puzzle.possibles[indices] = False

    def add_contradictions(self) -> None:
        for (r1, c1), (r2, c2) in zip(self.cells[:-1], self.cells[1:]):
            for d1, d2 in itertools.product(DIGITS, repeat=2):
                if abs(d1 - d2) < 5:
                    i1 = self.puzzle.possible_index(r1, c1, d1)
                    i2 = self.puzzle.possible_index(r2, c2, d2)
                    self.puzzle.add_contradiction(i1, i2)


class NoX(Constraint):
    """No adjacent cells sum to 10."""

    def __init__(self, puzzle):
        cells = [(i, j) for i in range(1, 10) for j in range(1, 10)]
        super().__init__(puzzle, cells)

    def initialise_on_grid(self) -> None:
        pass

    def add_contradictions(self) -> None:
        for low_summand in range(1, 5):
            for col in DIGITS:
                for row in DIGITS:
                    # Right side of cell
                    if col != max(DIGITS):
                        i1 = self.puzzle.possible_index(row, col, low_summand)
                        i2 = self.puzzle.possible_index(
                            row, col + 1, 10 - low_summand
                        )
                        self.puzzle.add_contradiction(i1, i2)

                        i1 = self.puzzle.possible_index(
                            row, col, 10 - low_summand
                        )
                        i2 = self.puzzle.possible_index(
                            row, col + 1, low_summand
                        )
                        self.puzzle.add_contradiction(i1, i2)

                    if row < max(DIGITS):
                        i1 = self.puzzle.possible_index(row, col, low_summand)
                        i2 = self.puzzle.possible_index(
                            row + 1, col, 10 - low_summand
                        )
                        self.puzzle.add_contradiction(i1, i2)

                        i1 = self.puzzle.possible_index(
                            row, col, 10 - low_summand
                        )
                        i2 = self.puzzle.possible_index(
                            row + 1, col, low_summand
                        )
                        self.puzzle.add_contradiction(i1, i2)


class RegionCountConstraint(Constraint):
    def __init__(
        self, puzzle: Puzzle, cells: list[tuple[int]], counts: dict[int, int]
    ):
        self.counts_array = np.array([counts.get(i, 0) for i in DIGITS])
        self.indices = puzzle.get_indices_for_cells(cells)
        super().__init__(puzzle, cells)

    def initialise_on_grid(self) -> None:
        indices_to_remove = []
        for digit, count in zip(DIGITS, self.counts_array):
            if count == 0:
                for cell in self.cells:
                    index_to_remove = self.puzzle.possible_index(
                        cell[0], cell[1], digit
                    )
                    indices_to_remove.append(index_to_remove)

        self.puzzle.possibles[indices_to_remove] = False

    def add_contradictions(self) -> None:
        pass

    def act_on_grid(self) -> None:
        finalised = self.puzzle.finalised[self.indices]
        counts = finalised.sum(axis=0)
        if np.any(counts > self.counts_array):
            raise SudokuContradiction("Specified region count exceeded!")


class CountingCircles(Constraint):

    def __init__(self, puzzle: Puzzle, cells: list[tuple[int]]):
        super().__init__(puzzle, cells)
        self.indices = puzzle.get_indices_for_cells(self.cells)
        self.target_counts_array = np.arange(1, 10)

    def initialise_on_grid(self) -> None:
        pass

    def add_contradictions(self) -> None:
        tuple_cells = [tuple(row) for row in self.cells]
        for c1 in tuple_cells:
            for c2 in tuple_cells:
                if np.all(c1 == c2):
                    continue

                i1 = self.puzzle.possible_index(*c1, 1)
                i2 = self.puzzle.possible_index(*c2, 1)
                self.puzzle.add_contradiction(i1, i2)

        for c1 in tuple_cells:
            for c2 in itertools.product(range(1, 10), repeat=2):
                if c2 in tuple_cells:
                    continue

                i1 = self.puzzle.possible_index(*c1, 9)
                i2 = self.puzzle.possible_index(*c2, 9)
                self.puzzle.add_contradiction(i1, i2)

    def act_on_grid(self) -> None:
        finalised = self.puzzle.finalised[self.indices]
        finalised_counts = finalised.sum(axis=0)
        if np.any(finalised_counts > self.target_counts_array):
            raise SudokuContradiction("Too many numbers inside circles")

        possibles = self.puzzle.possibles[self.indices]
        possible_counts = possibles.sum(axis=0)
        if np.any(
            (possible_counts < self.target_counts_array)
            * (finalised_counts != 0)
        ):
            raise SudokuContradiction(
                "Not enough possibles to satisfy circles."
            )


class KillerCage(NoRepeatsConstraint):

    def __init__(self, puzzle: Puzzle, cells: list[tuple[int]], total: int):
        super().__init__(puzzle, cells)
        self.indices = puzzle.get_indices_for_cells(self.cells)
        self.total = total

    def act_on_grid(self) -> None:
        possibles = self.puzzle.possibles[self.indices]
        combined_possibles = np.sum(possibles, axis=0) > 0
        values = combined_possibles * np.arange(1, 10)

        cumsum = np.unique(np.cumsum(values))

        if cumsum[0] == 0:
            cumsum = cumsum[1:]

        num_unique_possibles = len(cumsum)
        if num_unique_possibles < len(self.cells):
            raise SudokuContradiction("Not enough possibles left to fill cage.")

        if cumsum[len(self.cells) - 1] > self.total:
            raise SudokuContradiction("Minimum cage total too big.")

        starting_cumsum = 0
        if len(self.cells) < len(cumsum):
            starting_cumsum = cumsum[-len(self.cells) - 1]
        if cumsum[-1] - starting_cumsum < self.total:
            raise SudokuContradiction("Maximum cage total too small.")


class CornerMark(Constraint):

    def __init__(
        self, puzzle: Puzzle, cells: list[tuple[int, int]], value: int
    ):
        self.indices = [
            puzzle.possible_index(row, col, value) for row, col in cells
        ]
        super().__init__(puzzle, cells)

    def add_contradictions(self) -> None:
        self.puzzle.add_coveree(self.indices)

    def initialise_on_grid(self):
        pass


class Wheel(Constraint):

    def __init__(
        self, puzzle: Puzzle, centre: tuple[int, int], values: list[int | None]
    ):
        row, col = centre
        if {row, col}.intersection({1, 9}):
            raise ValueError("Cannot place wheels in R1, R9, C1 or C9.")
        cells = [
            (row - 1, col),
            (row, col + 1),
            (row + 1, col),
            (row, col - 1),
        ]
        self.values = values
        super().__init__(puzzle, cells)

    def initialise_on_grid(self) -> None:
        possibles_to_remove = [
            self.puzzle.possible_index(row, col, value)
            for row, col in self.cells
            for value in range(1, 10)
            if value not in self.values
        ]

        self.puzzle.possibles[possibles_to_remove] = False

    def add_contradictions(self) -> None:
        for value_idx_1, value_idx_2 in itertools.combinations(range(4), 2):
            expected_diff = (value_idx_2 - value_idx_1) % 4
            for cell_idx_1, cell_idx_2 in itertools.product(range(4), repeat=2):
                if cell_idx_1 == cell_idx_2:
                    continue
                actual_diff = (cell_idx_2 - cell_idx_1) % 4

                if actual_diff != expected_diff:
                    i1 = self.puzzle.possible_index(
                        *self.cells[cell_idx_1], self.values[value_idx_1]
                    )
                    i2 = self.puzzle.possible_index(
                        *self.cells[cell_idx_2], self.values[value_idx_2]
                    )
                    self.puzzle.add_contradiction(i1, i2)


class AntiKing(Constraint):

    def __init__(self, puzzle: Puzzle):
        super().__init__(
            puzzle,
            list(itertools.product(range(1, 10), repeat=2)),
        )

    def initialise_on_grid(self) -> None:
        pass

    def add_contradictions(self) -> None:
        for r1, c1 in self.cells:
            for r2, c2 in self.cells:
                if r1 == r2 or c1 == c2:
                    continue
                if abs(r1 - r2) == 1 and abs(c1 - c2) == 1:
                    for value in range(1, 10):
                        i1 = self.puzzle.possible_index(r1, c1, value)
                        i2 = self.puzzle.possible_index(r2, c2, value)
                        self.puzzle.add_contradiction(i1, i2)


class DiagonalNoBlackKropki(Constraint):

    def __init__(self, puzzle: Puzzle):
        super().__init__(
            puzzle,
            list(itertools.product(range(1, 10), repeat=2)),
        )

    def add_contradictions(self) -> None:
        for r1, c1 in self.cells:
            for r2, c2 in self.cells:
                if abs(r1 - r2) <= 1 and abs(c1 - c2) <= 1:
                    for v1, v2 in itertools.product(range(1, 10), repeat=2):
                        i1 = self.puzzle.possible_index(r1, c1, v1)
                        i2 = self.puzzle.possible_index(r2, c2, v2)
                        if v1 + v2 == 8:
                            self.puzzle.add_contradiction(i1, i2)

    def initialise_on_grid(self) -> None:
        pass
