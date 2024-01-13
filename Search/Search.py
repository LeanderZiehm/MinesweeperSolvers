# import time
import random
import os
import sys
sys.path.insert(1, os.path.join(sys.path[0], ".."))
from MinsweeperFiles import minesweeper as minesweeperManager


BOARD_SIZE = (8, 8)
MAX_GAMES = 1000
MINE_COUNT = -1

if len(sys.argv) >= 2:
    # print("len(sys.argv) == 2")
    firstActualArgument = sys.argv[1]
    # print(f"firstActualArgument: {firstActualArgument}")
    argTuple = eval(firstActualArgument)
    # print(f"argTuple: {argTuple}", type(argTuple))
    BOARD_SIZE = argTuple

if len(sys.argv) >= 3:
    MAX_GAMES = int(sys.argv[2])

if len(sys.argv) >= 4:
    MINE_COUNT = int(sys.argv[3])





minesweeper = minesweeperManager.Create(BOARD_SIZE, MINE_COUNT)
# minesweeper.setupDebug()
# minesweeper.setupSeed(420)
# minesweeper.setupSeed(123)
minesweeper.setupMaxGames(MAX_GAMES)
minesweeper.setupSaveMetrics(os.path.dirname(os.path.realpath(__file__)))

# minesweeper.startLivePlotter()


def main():
    startAction = (minesweeper.SIZE_X // 2, minesweeper.SIZE_Y // 2)
    minesweeper.clickTile(startAction)

    while True:
        todo = [startAction]
        globalFlagPositions = []

        while minesweeper.isGameOver() == False:
            # print(f"todo:{todo} todoLength: {len(todo)}")
            # time.sleep(SECONDS_BETWEEN_ACTIONS)
            currentActionPosition = todo.pop(0)
            currentNumberValue = minesweeper.getNumberOfNumberedTile(currentActionPosition)
            # interactableNeighborPositions = minesweeper.getInteractableNeighborPositions(currentActionPosition)
            tilePos = currentActionPosition
            neighbors = minesweeper.getInteractableNeighborPositions(tilePos)
            # print(f"currentActionPosition: {currentActionPosition} neighbors: {neighbors}")
            tileValuebombCount = currentNumberValue
            flagNeighborCount = len([n for n in neighbors if n in globalFlagPositions])
            nonFlagNeighbors = [n for n in neighbors if n not in globalFlagPositions]

            bombsNearby = tileValuebombCount - flagNeighborCount

            if bombsNearby == len(nonFlagNeighbors):  # if all neighbors are bombs
                for nonFlagNeighbor in nonFlagNeighbors:
                    minesweeper.setFlag(nonFlagNeighbor)
                    globalFlagPositions.append(nonFlagNeighbor)

                    for n in minesweeper.getAllNumberedTiles():
                        if n not in todo:
                            todo.append(n)

            elif (tileValuebombCount - flagNeighborCount) == 0:  # if all non flagged neighbors are not bombs
                # print(f"ALL ARE SAVE: tileValuebombCount: {tileValuebombCount} flagNeighborCount: {flagNeighborCount} nonFlagNeighbors: {nonFlagNeighbors}")
                nonFlagInteractableNeighbors = [neighbour for neighbour in neighbors if neighbour not in globalFlagPositions]
                for neighbour in nonFlagInteractableNeighbors:
                    minesweeper.clickTile(neighbour)

                    for n in minesweeper.getAllNumberedTiles():
                        if n not in todo:
                            todo.append(n)

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

                            for n in minesweeper.getAllNumberedTiles():
                                if n not in todo:
                                    todo.append(n)
                        # print(f"$$$$$$SET DIFF CONFIRMED with A: {currentActionPosition} to B: {numberNeighborB} and the vDiff: {valueDiffAB}  that those are bombs: {neighboursDiffSetAB} ")

            if todo == []:  # if logic fails, do random action
                # print("RANDOM ACTION", neighbors)
                if nonFlagNeighbors != []:
                    rand = random.choice(nonFlagNeighbors)
                else:
                    inter = minesweeper.getAllInteractableTilesPostitions()
                    nonFlagInteractableNeighbors = [neighbour for neighbour in inter if neighbour not in globalFlagPositions]
                    if nonFlagInteractableNeighbors == []:
                        if minesweeper.isGameOver() == False:
                            print(f"{minesweeper.getBoardString()}, {minesweeper.getAllNumberedTiles()}, {minesweeper.getAllInteractableTilesPostitions()}, {globalFlagPositions}")
                            input("NO MORE INTERACTABLE TILES BUT GAME IS NOT OVER. PRESS ENTER TO CONTINUE...")

                        break
                    rand = random.choice(nonFlagInteractableNeighbors)
                # print(minesweeper.getBoardString())
                # isRandomPositionFlagged = rand in globalFlagPositions
                # print(f"EXECUTING RANDOM ACTION: {rand} in 2 sec isRandomPositionFlagged: {isRandomPositionFlagged}")

                # time.sleep(2)
                minesweeper.clickTile(rand)
                todo = minesweeper.getAllNumberedTiles()

                # if minesweeper.isGameOver():
                # print(f"{rand} was a bomb. The random action just lost the game.")

        # if minesweeper.isWin():
        # print("WIN")
        # input("Press Enter to continue...")
        # time.sleep(1)
        # minesweeper.tk.mainloop()
        # else:
        # print("LOSE")
        # input("Press Enter to continue...")
        # time.sleep(1)

        # minesweeper.tk.mainloop()

        # print("SEARCH OVER")
        minesweeper.restartGame()
        # minesweeper.tk.mainloop()


if __name__ == "__main__":
    main()
