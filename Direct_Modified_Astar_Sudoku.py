import argparse
import sys
import csv
from queue import PriorityQueue
import copy
from functools import reduce
import time
import tkinter as tk

ALL_VALID = 511  # the bit string 111111111
VALID_DIGITS_STR = "123456789"

def popcount(x):
    """Utility function to get the popcount (# of 1 bits) in a bit string."""
    return bin(x).count("1")

def get_vals_as_list(bstr):
    """Converts a bit string encoding the possible values for a cell to an array of integer values."""
    val = 1
    vals = []
    while bstr != 0:
        if bstr & 1:
            vals.append(val)
        bstr >>= 1
        val += 1
    return vals

class Solver(object):
    """Encompasses the logic of the solution process."""
    def __init__(self, initial_board):
        self.start = initial_board
        self.visited_set = set()
        self.queue = PriorityQueue()

    def solve(self):
        puzzle_state = self.start
        puzzle_state.fast_forward()
        dist = puzzle_state.get_dist_to_goal()
        self.queue.put((dist, puzzle_state))
        
        while not puzzle_state.is_complete() and self.queue.qsize():
            puzzle_state = self.queue.get()[1]
            puzzle_hash = str(puzzle_state)
            self.visited_set.add(puzzle_hash)
            
            for c in puzzle_state.create_children():
                if str(c) not in self.visited_set:
                    dist = c.get_dist_to_goal()
                    self.queue.put((dist, c))
        
        return puzzle_state
    
    

class BoardState(object):
    """Describes a single instance of the game board."""
    def __init__(self, data):
        self.board = data
        self.possible_vals = [[ALL_VALID for _ in range(9)] for _ in range(9)]
        for r, row in enumerate(self.board):
            for c, val in enumerate(row):
                if val:
                    self.mark_value_invalid(r, c, val)
    
    def place_value(self, row, col, val):
        """
        Place value val at (row, col) and mark the value as an invalid
        selection elsewhere in the puzzle.
        """
        self.board[row][col] = val
        self.mark_value_invalid(row, col, val)

    def mark_value_invalid(self, row, col, val):
        """
        Mark the value val placed at (row, col) for cells where val is
        no longer an valid option.
        """
        self.possible_vals[row][col] = 0
        val_mask = (511 - (1 << val-1))

        # Mark this value as invalid for all cells in the specified row
        for c in range(9):
            self.possible_vals[row][c] &= val_mask

        # Mark this value as invalid for all cells in the specified col
        for r in range(9):
            self.possible_vals[r][col] &= val_mask

        # Mark this value as invalid for all cells in the same 3x3 square
        start_row, start_col = 3*(row//3), 3*(col//3)
        end_row, end_col = start_row + 3, start_col + 3
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                self.possible_vals[r][c] &= val_mask

    def get_dist_to_goal(self):
        """
        The goal of this function is to establish a quantitative measure of 
        distance from the (solved) end-state. Currently uses a naive count of
        the number of filled-in cells on the board.
        """
        bool_map = [map(bool, row) for row in self.board]
        return sum([sum(r) for r in bool_map])
        
    def is_complete(self):
        return self.get_dist_to_goal() == 0 

    def get_scored_next_steps(self):
        """
        Instantiate and return a priority queue where cells are prioritized 
        according to the number of possible values they can take. Fewer is better,
        bc it means a higher probability of selecting the correct value.
        """
        scored_steps = PriorityQueue()
        for r, row in enumerate(self.possible_vals):
            for c, val in enumerate(row):
                pc = popcount(val)
                # Add cells with # possible vals > 0 to the queue
                if pc:
                    poss_vals = get_vals_as_list(self.possible_vals[r][c])
                    scored_steps.put((pc, r, c, poss_vals))
        return scored_steps

    def fast_forward(self):
        """
        Scan the board for obvious next moves, and go ahead and make those.

        In particular this means repeatedly looking for cells that we've marked
        as having a single possible value and actually placing that value on the
        board.
        """
        cells_need_updating = True
        while cells_need_updating:
            cells_need_updating = False
            for r, row in enumerate(self.possible_vals):
                for c, poss_vals in enumerate(row):
                    pc = popcount(poss_vals)
                    if pc == 1: 
                        if not cells_need_updating: cells_need_updating = True
                        val = get_vals_as_list(poss_vals)[0]
                        self.place_value(r, c, val)

    def create_children(self):
        """
        Here we examine the available alternatives for our next step, as scored
        using the get_scored_next_steps function. We simply take one of the best-
        rated cells (fewest possible vals) and create board states where each
        of the possible values is selected.
        """

        next_steps = self.get_scored_next_steps()
        if next_steps.qsize():
            pc, row, col, choices = self.get_scored_next_steps().get()
            children = []
            for val in choices:
                child = copy.deepcopy(self)
                child.place_value(row, col, val)
                child.fast_forward()
                children.append(child)

            return children
        else:
            return []

    def pretty_print(self):      
        print ("Found solution")
        for row in self.board:
            print (row)

    def _str_(self):
        """
        Return a unique sting identifier for this board
        """
        return ''.join([''.join(map(str, row)) for row in self.board])



def Astar_solve(board):
    try:
        start = BoardState(board)
        solver = Solver(start)
        fin = solver.solve()
        return True, fin.board
    except Exception as e:
        print(f"Error: {str(e)}")
        return False, None

def display_board_gui(board):
    root = tk.Tk()
    root.title("Sudoku Solver")
    for i in range(9):
        for j in range(9):
            cell = tk.Label(root, text=str(board[i][j]), width=4, height=2, borderwidth=1, relief="solid")
            cell.grid(row=i, column=j)
    root.mainloop()

def main():
    # Define a sample Sudoku board; 0 represents an empty cell
    sample_board = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [0, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]
    is_solved, board = Astar_solve(sample_board)
    if is_solved:
        print("Sudoku solved successfully!")
        display_board_gui(board)
    else:
        print("Failed to solve Sudoku.")

if __name__ == '__main__':
    main()