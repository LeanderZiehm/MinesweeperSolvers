from z3 import *
import sys
import os
import random
import time

sys.path.insert(1, os.path.join(sys.path[0], ".."))
from MinsweeperFiles import minesweeper as minesweeperManager


BOARD_SIZE = (8, 8)
MAX_GAMES = 1000
MINE_COUNT = -1

if len(sys.argv) >= 2:
    firstActualArgument = sys.argv[1]
    argTuple = eval(firstActualArgument)
    BOARD_SIZE = argTuple

if len(sys.argv) >= 3:
    MAX_GAMES = int(sys.argv[2])

if len(sys.argv) >= 4:
    MINE_COUNT = int(sys.argv[3])


UNKNOWN = -1


def main():
    minesweeper = minesweeperManager.Create(BOARD_SIZE, MINE_COUNT)
    minesweeper.setupMaxGames(MAX_GAMES)
    minesweeper.setupSaveMetrics(os.path.dirname(os.path.realpath(__file__)))

    while True:
        boardString = minesweeper.getBoardString()
        result = SAT(boardString)
        if result != {}:
            smallestTileFromSolution = min(result, key=result.get)
            minesweeper.clickTile(smallestTileFromSolution)
        else:
            rand = random.choice(minesweeper.getAllInteractableTilesPostitions())
            minesweeper.clickTile(rand)

            if minesweeper.isLose():
                print(minesweeper.getBoardString())
                print("[THE RANDOM ACTION WAS A MINE]", rand)

        if minesweeper.isGameOver():
            minesweeper.restartGame()


def SAT(boardString):
    sol = SimpleSolver()
    game = string_to_matrix(boardString)
    rows = len(game)
    columns = len(game[0])

    possibleMines = {}
    for i in range(rows):
        for j in range(columns):
            currentTile = game[i][j]
            if currentTile > 0:  # only add neighbor mines around numberd tiles
                neighborsOfNumberedTile = []
                for x in [-1, 0, 1]:
                    for y in [-1, 0, 1]:
                        if i + x >= 0 and j + y >= 0 and i + x < rows and j + y < columns:
                            neighborsOfNumberedTile.append((i + x, j + y))

                possibleMineNeighbours = []

                for neighbor in neighborsOfNumberedTile:
                    isUnknown = game[neighbor[0]][neighbor[1]] == UNKNOWN
                    if isUnknown:
                        nx, ny = neighbor
                        if neighbor not in possibleMines:  # not already added
                            possibleMines[(nx, ny)] = Bool("possibleMines_%i,%i" % (nx, ny))
                            # sol.add(mines[(nx, ny)] >= 0, mines[(nx, ny)] <= 1)
                        possibleMineNeighbours.append(possibleMines[(nx, ny)])

                sol.add(currentTile == Sum([If(possibleMine, 1, 0) for possibleMine in possibleMineNeighbours]))
                # sol.add(Sum(possibleMineNeighbours) == mineCountOfTile)

    mineCountSolutions = {}

    num_solutions = 0
    while sol.check() == sat:
        num_solutions += 1
        model = sol.model()

        sol.add(Or([possibleMines[(i, j)] != model.eval(possibleMines[(i, j)]) for i, j in possibleMines]))

        for minePos in possibleMines:  # mine = 1, save = 0
            if minePos not in mineCountSolutions:
                mineCountSolutions[minePos] = 0

            isMineBoolRef = model.eval(possibleMines[minePos])
            isMine = str(isMineBoolRef) == "True"
            if isMine:
                mineCountSolutions[minePos] += 1

        if num_solutions >= 500:
            print("More then 500 solutions, stopping the count now...")
            break

    return mineCountSolutions


def string_to_matrix(input_string):
    size = int(math.sqrt(len(input_string)))
    matrix = []
    for i in range(0, len(input_string), size):
        row = []
        for char in input_string[i : i + size]:
            if char == "#" or char == "?":
                row.append(UNKNOWN)  # "?"
            else:
                row.append(int(char))
        matrix.append(row)
    return matrix


if __name__ == "__main__":
    main()
