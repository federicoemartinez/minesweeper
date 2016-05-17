__author__ = 'Federico Martinez'

import random
from collections import defaultdict

# Custom exceptions
class InvalidCellException(Exception):
    pass


# Strategies for placing bombs in a board

class BombPlacerStrategy(object):
    def get_bomb_positions(self, rows, columns, bombs):
        raise NotImplementedError


class RandomBombPlacerStrategy(BombPlacerStrategy):
    def get_bomb_positions(self, rows, columns, bombs):
        positions = [(x, y) for x in range(rows) for y in range(columns)]
        return set(random.sample(positions, bombs))


# A cell can have a flag or not. The behavior changes, because a cell with
# a flag cannot be clicked (or better said: nothing happens if you do)

class FlagState(object):
    def render(self):
        raise NotImplementedError

    def click(self, a_cell, board, neighbors):
        raise NotImplementedError


class Flag(FlagState):
    def render(self):
        return "F"

    def click(self, a_cell, board, neighbors):
        pass


class NoFlag(FlagState):
    def render(self):
        return " "

    def click(self, a_cell, board, neighbors):
        a_cell._clicked.click(a_cell, board, neighbors)


# A cell can be in a clicked or unclicked state. A clicked cell
# shows its content and cannot be clicked again. You can't put a flag on it either
class ClickState(object):
    def render(self, a_cell):
        raise NotImplementedError

    def click(self, a_cell, board, neighbors):
        raise NotImplementedError

    def put_flag(self, a_cell):
        raise NotImplementedError


class ClickedState(object):
    def render(self, a_cell):
        return a_cell.get_content()

    def put_flag(self, a_cell):
        pass

    def click(self, a_cell, board, neighbors):
        return


class UnclikedState(object):
    def render(self, a_cell):
        return a_cell._flag.render()

    def put_flag(self, a_cell):
        a_cell._flag = Flag()

    def click(self, a_cell, board, neighbors):
        a_cell._clicked = ClickedState()
        a_cell.propagate_click(board, neighbors)


# Basic class for a cell
class Cell(object):
    def __init__(self):
        self._flag = NoFlag()
        self._clicked = UnclikedState()

    def put_flag(self):
        self._clicked.put_flag(self)

    def remove_flag(self):
        self._flag = NoFlag()

    def click(self, board, neighbors):
        self._flag.click(self, board, neighbors)

    def render(self):
        return self._clicked.render(self)

    def propagate_click(self, board, neighbors):
        raise NotImplementedError

# A plain cell is a cell without a bomb. It's content is the amount
# of close bombs.
class PlainCell(Cell):
    def __init__(self, counter):
        super(PlainCell, self).__init__()
        self._counter = counter

    def get_content(self):
        return str(self._counter)

    def propagate_click(self, board, neighbors):
        return

# An empty plain cell is a special case as it has different behavior:
# When you click it, it propagates the "click" to its neighbors
class EmptyPlainCell(PlainCell):
    def __init__(self):
        super(PlainCell, self).__init__()
        self._counter = 0

    def get_content(self):
        return str(self._counter)

    def click_neighbors(self, board, neighbors):
        for each in neighbors:
            board.click(*each)

    def propagate_click(self, board, neighbors):
        self.click_neighbors(board, neighbors)

# The class of the cells with a bomb
class BombCell(Cell):
    def get_content(self):
        return "B"

    def propagate_click(self, board, neighbors):
        return

# Factory to make abstract the creation of plain cells based on their content
class PlainCellFactory(object):
    def __init__(self):
        self.plain_classes = defaultdict(lambda: lambda x: PlainCell(x))
        self.plain_classes[0] = lambda x: EmptyPlainCell()

    def build_plain_cell(self, counter):
        return self.plain_classes[counter](counter)


class Board(object):
    def __init__(self, rows, columns, bombs, bomb_placer=RandomBombPlacerStrategy()):
        self.rows = rows
        self.columns = columns
        self.bombs = bombs
        self._cells = {}
        self._place_bombs(bomb_placer)


    def _place_bombs(self, bomb_placer):
        plain_cells_factory = PlainCellFactory()
        bombs_positions = bomb_placer.get_bomb_positions(self.rows, self.columns, self.bombs)
        bomb_cells = {}
        for row, col in bombs_positions:
            bomb_cells[(row, col)] = BombCell()
        for row in range(self.rows):
            for col in range(self.columns):
                neighbors = self._get_neighbors(row, col)
                counter = sum((1 for x in neighbors if x in bomb_cells))
                self._cells[(row, col)] = plain_cells_factory.build_plain_cell(counter)
        self._cells.update(bomb_cells)
        self.exploded_bomb = None

    def is_valid_row(self, row):
        return 0 <= row and row < self.rows

    def is_valid_column(self, column):
        return 0 <= column and column < self.columns

    def _validate_cell(self, row, column):
        if not self.is_valid_row(row):
            raise InvalidCellException("Row %s is not in range [0, %s)" % (row, self.rows))
        if not self.is_valid_column(column):
            raise InvalidCellException("Column %s is not in range [0, %s)" % (column, self.columns))

    def click(self, row, column):
        self._validate_cell(row, column)
        a_cell = self._cells[(row, column)]
        a_cell.click(self, self._get_neighbors(row, column))

    def _get_neighbors(self, row, column):
        return set((a_row, a_column) for a_row in (row - 1, row, row + 1) \
                   for a_column in (column - 1, column, column + 1) \
                   if self.is_valid_row(a_row) and self.is_valid_column(a_column) \
                   and (a_row, a_column) != (row, column))

    def put_flag(self, row, column):
        self._validate_cell(row, column)
        self._cells[(row, column)].put_flag()

    def remove_flag(self, row, column):
        self._validate_cell(row, column)
        self._cells[(row, column)].remove_flag()

    def __iter__(self):
        for row in range(self.rows):
            for col in range(self.columns):
                yield (row, col, self._cells[(row, col)])


class BoardDrawer(object):
    cell = "|%s"
    border = "_"

    def draw(self, board):
        rows = []
        current_row = 0
        row_str = ""
        for row, col, cell in board:
            if current_row != row:
                row_str += "|"
                rows.append(row_str)
                row_str = ""
                current_row = row
            cell_str = "|" + board._cells[(row, col)].render()
            row_str += cell_str
        row_str += "|"
        rows.append(row_str)
        print "\n".join(rows)


b = Board(3, 10, 10)
bd = BoardDrawer()
bd.draw(b)
