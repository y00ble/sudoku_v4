from __future__ import annotations

import collections
import contextlib
import copy
import curses
import datetime
import itertools
import time
from multiprocessing import Manager, Pool

import numpy as np

from sudoku.constraints import DIGITS, Box, Column, Row
from sudoku.exceptions import SudokuContradiction

FRAME_RATE = 1
NUM_ROWS = 9
NUM_COLS = 9
NUM_CELLS = NUM_ROWS * NUM_COLS
NUM_DIGITS = 9
NUM_POSSIBLES = NUM_CELLS * NUM_DIGITS
MAX_COVEREE_SIZE = 9

Bifurcation = collections.namedtuple(
    "Bifurcation",
    ["index", "possibles", "finalised", "num_options", "current_option_num"],
)

MULTIPROCESS_TASK_COUNT = 50


class Puzzle:

    def __init__(self):
        self.possibles = np.ones(NUM_POSSIBLES + 1).astype(bool)
        self.finalised = np.zeros(NUM_POSSIBLES + 1).astype(bool)
        self.in_valid_solutions = np.zeros(NUM_POSSIBLES + 1)
        self.possibles[-1] = False

        self.constraints = []

        self.unbifurcated_possibles = self.possibles

        self.contradictions = np.zeros(
            (NUM_POSSIBLES + 1, NUM_POSSIBLES + 1)
        ).astype(bool)
        self.contradictions[-1] = False
        self.contradictions[:, -1] = False
        self.coverees = np.array([])
        self.screen = None
        self.solutions = set()
        self.last_frame_time = 0
        self.bifurcations = []
        self.solve_start_time = 0

        self.multiprocess_progress_dict = None
        self.multiprocessing_id = None
        self.multiprocess_solution_count = None
        self.multiprocess_lock = None

        self._init_grid_constraints()

    def solve(self, with_terminal=False, multiprocess=False):
        # TODO error handling for impossible puzzles

        if with_terminal and multiprocess:
            raise ValueError(
                "Can't specify both `with_terminal` and `multiprocess`."
            )

        self.solve_start_time = time.time()
        try:
            if with_terminal:
                curses.wrapper(self._solve)
            elif multiprocess:
                puzzle_copy = copy.deepcopy(self)
                bifurcations_to_try = puzzle_copy._list_bifurcations() or [[]]
                results = []
                with Manager() as manager, Pool() as pool:
                    progress_dict = manager.dict()
                    solution_counts = manager.dict()
                    multi_lock = manager.Lock()
                    for i, bifurcation_idxs in enumerate(bifurcations_to_try):
                        puzzle = copy.deepcopy(self)
                        puzzle.finalise(bifurcation_idxs)
                        puzzle.multiprocess_progress_dict = progress_dict
                        puzzle.multiprocessing_id = i
                        puzzle.multiprocess_solution_count = solution_counts
                        puzzle.multiprocess_lock = multi_lock
                        results.append(pool.apply_async(puzzle._solve))

                    time_started = time.time()
                    total_progress = len(results)
                    while any(not result.ready() for result in results):
                        current_progress = sum(progress_dict.values())
                        normalised_progress = current_progress / total_progress
                        if normalised_progress == 0:
                            continue
                        elapsed_time = time.time() - time_started
                        projected_finish_time = (
                            time_started + elapsed_time / normalised_progress
                        )
                        finish_time = datetime.datetime.fromtimestamp(
                            projected_finish_time
                        )
                        # TODO technically this isn't thread safe.
                        with multi_lock:
                            progress_values = copy.deepcopy(
                                progress_dict.values()
                            )
                            solution_counts_copy = copy.deepcopy(
                                solution_counts
                            )

                        done_count = len([v for v in progress_values if v == 1])
                        in_progress_count = len(
                            [v for v in progress_values if 0 < v < 1]
                        )
                        unstarted_count = (
                            len(results) - done_count - in_progress_count
                        )
                        solution_count = sum(
                            count for count in solution_counts_copy.values()
                        )
                        print(
                            f"Progress {normalised_progress:.2%}, projected "
                            f"finish time {finish_time.isoformat()}. "
                            f"Done: {done_count}, "
                            f"in progress: {in_progress_count}, "
                            f"yet to start: {unstarted_count}. "
                            f"Found {solution_count} solutions.",
                            end="\r",
                        )
                        time.sleep(1)

                self.solutions = {
                    sol for result in results for sol in result.get()
                }
            else:
                self._solve()
        finally:
            print(
                "{} {} found!".format(
                    len(self.solutions),
                    "solution" if len(self.solutions) == 1 else "solutions",
                )
            )
            for i, solution in enumerate(self.solutions):
                print(f"SOLUTION {i}".center(30, "-"))
                self.simple_draw(solution)

            total_possibles = [False for _ in range(len(self.possibles))]
            for solution in self.solutions:
                for i, possible in enumerate(solution):
                    total_possibles[i] |= possible

            print("COMBINED SOLUTION".center(30, "-"))
            self.simple_draw(total_possibles)

    def _solve(self, screen=None):
        self.screen = screen
        self._init_colors()
        output = self._solve_or_bifurcate()
        self._update_multiprocess_progress(override_value=1)
        return output

    def _solve_or_bifurcate(self):
        self._logical_solve_til_no_change()
        if self.is_finished:
            return copy.deepcopy(self.solutions)
        idxs_to_bifurcate = self._select_bifurcation_coveree()
        for bifurcation_num, idx in enumerate(idxs_to_bifurcate):
            try:
                with self._bifurcate(
                    idx, len(idxs_to_bifurcate), bifurcation_num
                ):
                    self._refresh_screen()
                    self._solve_or_bifurcate()
            except SudokuContradiction:
                self.possibles[idx] = False

        try:
            self._logical_solve_til_no_change()
        except SudokuContradiction:
            return set()
        return copy.deepcopy(self.solutions)

    def _list_bifurcations(
        self, current_bifurcations=None, trivial_bifurcations=None
    ):
        """Simulate a few branches of a solve to get a list of bifurcations."""
        current_bifurcations = current_bifurcations or []
        trivial_bifurcations = trivial_bifurcations or []
        level = 0 if not current_bifurcations else len(current_bifurcations[0])
        print(
            f"Enumerating bifurcations: found {len(current_bifurcations)}/"
            f"{MULTIPROCESS_TASK_COUNT} on level {level}",
            end="\r",
        )

        self._logical_solve_til_no_change()
        if self.is_finished:
            return []

        if len(current_bifurcations) > MULTIPROCESS_TASK_COUNT:
            return current_bifurcations + trivial_bifurcations

        next_level_bifurcations = []
        for existing_bifurcations in current_bifurcations or [[]]:
            with contextlib.ExitStack() as stack:
                for idx in existing_bifurcations:
                    stack.enter_context(self._bifurcate(idx, 1, 1))

                idxs_to_bifurcate = self._select_bifurcation_coveree()
                for new_idx in idxs_to_bifurcate:
                    try:
                        with self._bifurcate(new_idx, 1, 1):
                            bifurcations_copy = copy.deepcopy(
                                self.bifurcation_indices
                            )
                            if self.is_finished:
                                trivial_bifurcations.append(bifurcations_copy)
                            else:
                                next_level_bifurcations.append(
                                    bifurcations_copy
                                )
                    except SudokuContradiction:
                        self.possibles[new_idx] = False

        if not next_level_bifurcations:
            return current_bifurcations + trivial_bifurcations
        return self._list_bifurcations(
            current_bifurcations=next_level_bifurcations,
            trivial_bifurcations=trivial_bifurcations,
        )

    def _logical_solve_til_no_change(self):
        old_possibles = None
        old_finalised = None
        while old_possibles != tuple(self.possibles) or old_finalised != tuple(
            self.finalised
        ):
            # TODO add pointing coverees (for each coveree, count indices
            # leading to each contradictions, compare to coveree length).
            # TODO add pair detection?? Seems costly
            # TODO add constraints like KillerCages that check for validity.
            for constraint in self.constraints:
                constraint.act_on_grid()
            self.process_singleton_coverees()
            old_possibles = tuple(self.possibles)
            old_finalised = tuple(self.finalised)

    def _init_grid_constraints(self) -> None:
        for i in DIGITS:
            for constraint_cls in [Row, Column, Box]:
                constraint = constraint_cls(self, i)
                for j in DIGITS:
                    indices = [
                        self.possible_index(*cell, j)
                        for cell in constraint.cells
                    ]
                    self.add_coveree(indices)

        for row in DIGITS:
            for col in DIGITS:
                indices = [self.possible_index(row, col, j) for j in DIGITS]
                self.add_coveree(indices)

                for d1, d2 in itertools.product(DIGITS, repeat=2):
                    if d1 == d2:
                        continue

                    i1 = self.possible_index(row, col, d1)
                    i2 = self.possible_index(row, col, d2)
                    self.add_contradiction(i1, i2)

    def _select_bifurcation_coveree(self) -> list[int]:
        possible_mask = self.possibles[self.coverees]
        remaining_coverees = self.coverees * possible_mask - (1 - possible_mask)

        finalised_msak = np.any(self.finalised[remaining_coverees], axis=1)
        remaining_coverees[finalised_msak] = -1

        coveree_counts = (remaining_coverees != -1).sum(axis=1)
        coveree_counts[coveree_counts < 2] = MAX_COVEREE_SIZE + 1
        min_coveree_size = coveree_counts.min()

        if min_coveree_size == MAX_COVEREE_SIZE + 1:
            return []

        candidate_coverees = remaining_coverees[
            coveree_counts == min_coveree_size
        ]
        # If I bifurcate on this index, how many possibles get removed
        possibles_removed = (
            self.contradictions * self.possibles * (1 - self.finalised)
        ).sum(axis=1)
        possibles_removed_per_coveree = possibles_removed[
            candidate_coverees
        ].sum(axis=1)
        best_coveree = np.argmax(possibles_removed_per_coveree)
        output = [idx for idx in candidate_coverees[best_coveree] if idx != -1]
        return output

    @contextlib.contextmanager
    def _bifurcate(self, index: int, num_options: int, current_num: int):
        bifurcation = Bifurcation(
            index=index,
            possibles=self.possibles,
            finalised=self.finalised,
            num_options=num_options,
            current_option_num=current_num,
        )
        self.possibles = copy.deepcopy(self.possibles)
        self.finalised = copy.deepcopy(self.finalised)
        try:
            self.bifurcations.append(bifurcation)
            self.finalise([index])
            yield
        except SudokuContradiction:
            raise
        finally:
            self.bifurcations.pop()
            self.possibles = bifurcation.possibles
            self.finalised = bifurcation.finalised

    def finalise(self, possible_indices: list[int]) -> None:
        """Mark the given possibles as finalised."""
        not_yet_finalised = [
            idx for idx in possible_indices if not self.finalised[idx]
        ]
        if not not_yet_finalised:
            return
        self.finalised[not_yet_finalised] = True
        adjacent_contradictions = (
            self.contradictions[not_yet_finalised].sum(axis=0) > 0
        )
        if np.any(self.finalised[adjacent_contradictions]):
            raise SudokuContradiction("Trying to remove finalised digit!")
        self.possibles[adjacent_contradictions] = False

        if self.is_finished:
            # Final check for contradictions in constraints.
            self._logical_solve_til_no_change()
            self._add_solution(self.possibles)
            return

        self.process_singleton_coverees()

    def _add_solution(self, indices):
        self.solutions.add(tuple(self.possibles))
        if self.multiprocess_lock is not None:
            with self.multiprocess_lock:
                self.multiprocess_solution_count[self.multiprocessing_id] = len(
                    self.solutions
                )
        self.in_valid_solutions[self.possibles] = True

    def process_singleton_coverees(self) -> None:
        """Return indices that are the only option left in their coverees."""
        possible_mask = self.possibles[self.coverees]
        remaining_coverees = self.coverees * possible_mask - (1 - possible_mask)
        coveree_counts = (remaining_coverees != -1).sum(axis=1)
        if np.any(coveree_counts == 0):
            raise SudokuContradiction("Coveree no longer possible")
        singleton_coverees = remaining_coverees[coveree_counts == 1]
        indices = np.unique(singleton_coverees).tolist()
        if indices:
            indices.remove(-1)
            self.finalise(indices)

    def add_coveree(self, coveree: list[int]) -> None:
        """Add a coveree.

        A coveree is a list of possible indices, one of which must be true.
        """
        if len(coveree) > MAX_COVEREE_SIZE:
            msg = f"Coveree {coveree} too long. Max size is {MAX_COVEREE_SIZE}."
            raise ValueError(msg)

        padded = coveree + [-1] * (MAX_COVEREE_SIZE - len(coveree))
        if self.coverees.shape != (0,):
            self.coverees = np.vstack([self.coverees, [padded]])
        else:
            self.coverees = np.array([padded])

    def add_contradiction(self, i1: int, i2: int) -> None:
        """Add a contradiction."""
        self.contradictions[i1, i2] = True
        self.contradictions[i2, i1] = True

    def __setitem__(self, key: tuple[int, int], value: int | list[int]):
        if not isinstance(value, collections.abc.Iterable):
            value = [value]

        row, column = key

        indices_to_remove = []
        for digit in DIGITS:
            index = self.possible_index(row, column, digit)
            if digit not in value:
                indices_to_remove.append(index)

        if indices_to_remove:
            self.possibles[indices_to_remove] = False
            self.process_singleton_coverees()

    @property
    def is_finished(self):
        return np.sum(self.finalised) == NUM_CELLS

    # Index conversion code
    @staticmethod
    def _cell_start_index(row: int, col: int) -> int:
        return (row - 1) * 81 + (col - 1) * 9

    @staticmethod
    def get_indices_for_cells(cells: list[tuple[int]]):
        """Make a 2D array where each row is a cell's slice of 'finalised'."""
        cells_as_array = np.array(cells)
        cell_indices = (
            (cells_as_array[:, 0] - 1) * 81 + (cells_as_array[:, 1] - 1) * 9
        ).reshape((len(cells), 1))
        possible_indices = cell_indices + np.tile(
            np.arange(0, 9), (len(cells), 1)
        )
        return possible_indices

    @staticmethod
    def possible_index(row: int, col: int, possible: int) -> int:
        return Puzzle._cell_start_index(row, col) + (possible - 1)

    # Drawing code
    def simple_draw(self, state: np.ndarray | None = None) -> None:
        if state is None:
            state = self.possibles
        output = ""
        for row in DIGITS:
            for col in DIGITS:
                possibles = [
                    str(i)
                    for i in DIGITS
                    if state[self.possible_index(row, col, i)]
                ]
                output += "".join(possibles).ljust(len(DIGITS))
                if col in {3, 6}:
                    output += " | "
                elif col != 9:
                    output += " "
            if row in {3, 6}:
                output += "\n" + "-" * (9 * 9 + 6 + 2 * 3) + "\n"
            elif row != 9:
                output += "\n"

        print(output)

    def _init_colors(self) -> None:
        if self.screen is None:
            return
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, 12, -1)  # Primary bifurcation
        curses.init_pair(4, 28, -1)  # in a valid solution
        curses.init_pair(
            5, 72, -1
        )  # in a valid solution, but not on bifurcation
        curses.init_pair(2, 88, -1)  # Non-primary bifurcation
        curses.init_pair(3, 0, -1)  # Unbifurcated possible

    def _update_multiprocess_progress(self, override_value=None):
        if self.multiprocess_lock is not None:
            with self.multiprocess_lock:
                self.multiprocess_progress_dict[self.multiprocessing_id] = (
                    override_value or self.progress
                )
            return

    def _refresh_screen(self):
        if time.time() - self.last_frame_time < 1 / FRAME_RATE:
            return
        self.last_frame_time = time.time()
        self._update_multiprocess_progress()
        if self.screen is None:
            return

        self.screen.erase()

        self.screen.addstr(
            0,
            0,
            "==={} SOLUTIONS, BIFURCATION STATUS {}".format(
                len(self.solutions),
                ",".join(
                    [
                        f"{b.current_option_num + 1}/{b.num_options}"
                        for b in self.bifurcations
                    ]
                ),
            ).ljust((9 * 9) + 6 + 2 * 3, "="),
        )

        for i in range(11):
            self.screen.addstr(i + 1, 0, " | ".join([" " * 29] * 3))

        for i in [3, 7]:
            self.screen.addstr(i + 1, 0, "-" * ((9 * 9) + 6 + 2 * 3))

        draw_coords = self._possibles_to_draw_coords(
            self.unbifurcated_possibles
        )

        bifurcation_indices = [
            bifurcation.index for bifurcation in self.bifurcations
        ]
        for index in range(9**3):
            digit = str(index % 9 + 1)
            coords = tuple(draw_coords[index])
            if self.unbifurcated_possibles[index]:
                self.screen.addstr(
                    *coords,
                    digit,
                    curses.color_pair(
                        5 if self.in_valid_solutions[index] else 3
                    ),
                )

            if self.possibles[index]:
                self.screen.addstr(*coords, digit)
                if self.in_valid_solutions[index]:
                    self.screen.addstr(*coords, digit, curses.color_pair(4))

            if index in bifurcation_indices:
                first_bifurcation = index == bifurcation_indices[0]
                self.screen.addstr(
                    *coords,
                    digit,
                    curses.color_pair(1 if first_bifurcation else 2),
                )

        status_string = (
            f"Progress {self.progress * 100:.2f}%. "
            f"Projected finish time {self.projected_finish}."
        )
        self.screen.addstr(
            12, 0, f"==={status_string}".ljust((9 * 9) + 6 + 2 * 3, "=")
        )
        self.screen.refresh()

    @property
    def progress(self):
        registered_progress = 0
        current_subdivision = 1
        for bifurcation in self.bifurcations:
            registered_progress += (
                bifurcation.current_option_num / bifurcation.num_options
            ) * current_subdivision
            current_subdivision *= 1 / bifurcation.num_options
        return registered_progress

    @property
    def projected_finish(self):
        progress = self.progress
        if progress == 0:
            return "N/A"
        time_elapsed = time.time() - self.solve_start_time
        total_time = time_elapsed / progress
        finish_timestamp = self.solve_start_time + total_time
        return datetime.datetime.fromtimestamp(finish_timestamp).isoformat()

    @property
    def bifurcation_indices(self):
        return [bifurcation.index for bifurcation in self.bifurcations]

    @staticmethod
    def _possibles_to_draw_coords(possibles: np.ndarray) -> np.ndarray:
        reshaped_possibles = possibles[:-1].reshape((81, 9))
        index_offests = np.cumsum(reshaped_possibles, axis=1).reshape(9**3)
        cell_start_xs = ((np.arange(9**3) // 9) % 9) * 10
        cell_start_xs += 2 * (cell_start_xs >= 30) + 2 * (cell_start_xs >= 60)
        x_pos = cell_start_xs + index_offests - 1

        y_pos = np.arange(9**3) // 9**2
        y_pos += (y_pos >= 3).astype(int) + (y_pos >= 6).astype(int)

        return np.stack([y_pos + 1, x_pos]).T

    @staticmethod
    def _describe_possible_index(index: int) -> str:
        return f"R{index // 81 + 1}C{(index // 9) % 9 + 1} = {index % 9 + 1}"
