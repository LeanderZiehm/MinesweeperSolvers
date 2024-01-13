import random
import os
import sys

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

minesweeper = minesweeperManager.Create(BOARD_SIZE, MINE_COUNT)
minesweeper.setupMaxGames(MAX_GAMES)
minesweeper.setupSaveMetrics(os.path.dirname(os.path.realpath(__file__)))


def main():
    while True:
        while minesweeper.isGameOver() == False:
            unknownTiles = minesweeper.getAllInteractableTilesPostitions()
            rand = random.choice(unknownTiles)
            minesweeper.clickTile(rand)
        minesweeper.restartGame()


if __name__ == "__main__":
    main()
