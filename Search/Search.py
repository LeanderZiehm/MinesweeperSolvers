"[Author: Leander Ziehm]"

import random
import os
import sys

sys.path.insert(1, os.path.join(sys.path[0], ".."))
from MinsweeperFiles import minesweeper as minesweeperManager


BOARD_SIZE = (8, 8)
MAX_GAMES = 1000000000000
MINE_COUNT = None

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
# minesweeper.setupSaveMetrics(os.path.dirname(os.path.realpath(__file__)))


def main():
    startAction = (0, 0)  # (minesweeper.SIZE_X // 2, minesweeper.SIZE_Y // 2)
    minesweeper.clickTile(startAction)

    while True:
        todo = [startAction]
        globalFlagPositions = []

        while minesweeper.isGameOver() == False:
            currentActionPosition = todo.pop(0)
            currentNumberValue = minesweeper.getNumberOfNumberedTile(currentActionPosition)
            tilePos = currentActionPosition
            neighbors = minesweeper.getInteractableNeighborPositions(tilePos)
            tileValuebombCount = currentNumberValue
            flagNeighborCount = len([n for n in neighbors if n in globalFlagPositions])
            nonFlagNeighbors = [n for n in neighbors if n not in globalFlagPositions]

            bombsNearby = tileValuebombCount - flagNeighborCount

            if bombsNearby == len(nonFlagNeighbors):  # if all neighbors are bombs
                for nonFlagNeighbor in nonFlagNeighbors:
                    minesweeper.setFlag(nonFlagNeighbor)
                    globalFlagPositions.append(nonFlagNeighbor)

                    numberNeighbors = minesweeper.getNumberNeighborPostitions(nonFlagNeighbor)
                    todo.extend(numberNeighbors)

            elif (tileValuebombCount - flagNeighborCount) == 0:  # if all non flagged neighbors are not bombs
                nonFlagInteractableNeighbors = [neighbour for neighbour in neighbors if neighbour not in globalFlagPositions]
                for neighbour in nonFlagInteractableNeighbors:
                    minesweeper.clickTile(neighbour)

                    todo.append(neighbour)

            else:
                interactableNonFlagNeighboursA = nonFlagNeighbors
                valueA = bombsNearby
                numberNeighbors = minesweeper.getNumberNeighborPostitions(currentActionPosition)
                for numberNeighborB in numberNeighbors:
                    interactableNeighborsB = minesweeper.getInteractableNeighborPositions(numberNeighborB)
                    interactableNonFlagNeighboursB = [n for n in interactableNeighborsB if n not in globalFlagPositions]
                    valueB = minesweeper.getNumberOfNumberedTile(numberNeighborB) - len([n for n in interactableNeighborsB if n in globalFlagPositions])

                    valueDiffAB = valueA - valueB
                    neighboursDiffSetAB = set(interactableNonFlagNeighboursA) - set(interactableNonFlagNeighboursB)
                    if valueDiffAB == len(neighboursDiffSetAB):
                        for neighbour in neighboursDiffSetAB:
                            minesweeper.setFlag(neighbour)
                            globalFlagPositions.append(neighbour)

                            numberNeighbors = minesweeper.getNumberNeighborPostitions(neighbour)
                            todo.extend(numberNeighbors)

            if todo == []:  # if logic fails, do random action
                # print("TODO IS EMPTY")
                if nonFlagNeighbors != []:
                    rand = random.choice(nonFlagNeighbors)
                else:
                    inter = minesweeper.getAllInteractableTilesPostitions()
                    nonFlagInteractableNeighbors = [neighbour for neighbour in inter if neighbour not in globalFlagPositions]
                    if nonFlagInteractableNeighbors == []:
                        if minesweeper.isGameOver() == False:
                            print(f"{minesweeper.getBoardString()}, {minesweeper.getAllNumberedTiles()}, {minesweeper.getAllInteractableTilesPostitions()}, {globalFlagPositions}")
                            # input("NO MORE INTERACTABLE TILES BUT GAME IS NOT OVER. PRESS ENTER TO CONTINUE...")

                        break
                    rand = random.choice(nonFlagInteractableNeighbors)

                minesweeper.clickTile(rand)
                todo = minesweeper.getAllNumberedTiles()

        minesweeper.restartGame()


if __name__ == "__main__":
    try:
        main()
    except:
        pass

