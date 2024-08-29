from __future__ import annotations

import itertools
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .puzzle import DIGITS, Puzzle

DIGITS = list(range(1, 10))


class Constraint(ABC):

    def __init__(self, puzzle: Puzzle, cells: list[tuple]):
        self.puzzle = puzzle
        self.cells = np.array(cells)
        self.add_contradictions()
        self.restrict_possibles()

    @abstractmethod
    def add_contradictions(self) -> None:
        """Add puzzle contradictions for values that break this constraint."""
        ...

    @abstractmethod
    def restrict_possibles(self) -> None:
        """Mark some of the puzzle's numbers as impossible."""
        ...


class NoRepeatsConstraint(Constraint):

    def add_contradictions(self) -> None:
        for c1, c2 in itertools.combinations(self.cells, 2):
            for value in DIGITS:
                i1 = self.puzzle.possible_index(*c1, value)
                i2 = self.puzzle.possible_index(*c2, value)
                self.puzzle.add_contradiction(i1, i2)

    def restrict_possibles(self) -> None:
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

    def restrict_possibles(self) -> None:
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

    def restrict_possibles(self):
        pass

    def add_contradictions(self):
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
