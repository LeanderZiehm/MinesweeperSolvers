"[Author: Leander Ziehm]"

import random
from collections import defaultdict
import atexit
import os
import numpy as np
import random
import time
import sys

sys.path.insert(1, os.path.join(sys.path[0], ".."))
from MinsweeperFiles import minesweeper as minesweeperManager

SAVE_QDICT = False  # True


UNKNOWN_TILE = -1
FLAGGED = -2
CLICK = -3

WINDOW_SIZE = (3, 3)

BOARD_SIZE = (4, 4)
MAX_TRAINING_GAMES = 1000000000000


FILENAME_TO_LOAD = "localQDict20000.txt" 


LEARNING_RATE = 0.95
DISCOUNT_FACTOR = 0.4 
EXPLORATION_PROB = 0.1  

if len(sys.argv) >= 2:
    LEARNING_RATE = float(sys.argv[1])

if len(sys.argv) >= 3:
    DISCOUNT_FACTOR = float(sys.argv[2])

if len(sys.argv) >= 4:
    EXPLORATION_PROB = float(sys.argv[3])

if len(sys.argv) >= 5:
    MAX_TRAINING_GAMES = int(sys.argv[4])

if len(sys.argv) >= 6:
    BOARD_SIZE = eval(sys.argv[5])

if len(sys.argv) >= 7:
    FILENAME_TO_LOAD = str(sys.argv[6])


pathOfThisFile = os.path.dirname(os.path.realpath(__file__))
saveFileName = f"_qDict{BOARD_SIZE}{MAX_TRAINING_GAMES}.txt"
pathToSavedDicts = pathOfThisFile # os.path.join(pathOfThisFile, "dictsSavedLocal")

# parameterLogsFileName = "parameterLogsLocal.txt"

minesweeper = minesweeperManager.Create(BOARD_SIZE)
# minesweeper.setupSaveMetrics(os.path.join(pathOfThisFile, "metricsLocal"))


SECONDS_BETWEEN_ACTIONS = 0


toAppendToParameterLogs = f"[LEARNING_RATE: ({LEARNING_RATE}) | DISCOUNT_FACTOR: ({DISCOUNT_FACTOR}) | EXPLORATION_PROB: ({EXPLORATION_PROB})]\n"


qDict = defaultdict(lambda: defaultdict(lambda: 0))


def save_file():
    dictToSave = {}
    for key in qDict:
        currentDict = qDict[key]
        cleanedDict = {}
        for key2 in currentDict:
            if currentDict[key2] == 0:
                continue
            else:
                cleanedDict[key2] = round(currentDict[key2], 2)
        if cleanedDict:
            dictToSave[key] = cleanedDict

    textToSave = str(dictToSave)
    minesweeperManager.saveFile(saveFileName, textToSave, pathToSavedDicts)


if SAVE_QDICT:
    atexit.register(save_file)


if FILENAME_TO_LOAD != "":
    FILENAME_TO_LOADPath = os.path.join(pathToSavedDicts, FILENAME_TO_LOAD)
    with open(FILENAME_TO_LOADPath, "r") as file:
        loadedDict = eval(file.read())
        for key in loadedDict:
            qDict[key] = defaultdict(lambda: 0, loadedDict[key])

    print(f"Loaded {FILENAME_TO_LOAD} from file. with {len(qDict)} states.")


def myArgMax(qAsDict, state, available_actions):
    maxAction = None
    maxValue = float("-inf")  # -100000

    for action in available_actions:
        if qAsDict[state][action] > maxValue:
            maxValue = qAsDict[state][action]
            maxAction = action

    return maxAction


def get_available_actions(stateDict):  # state is not needed because minesweeper already knows the state
    possibleActions = []
    for x in range(3):
        for y in range(3):
            if stateDict[x][y] == UNKNOWN_TILE:
                possibleActions.append(((x, y), FLAGGED))
                possibleActions.append(((x, y), CLICK))

    # if len(possibleActions) == 0:
    #     print("No available actions")
    #     input(possibleActions)
    return possibleActions


def getMaxReward(stateWindow):
    if stateWindow == "GAME OVER":
        return 0
    available_actions = get_available_actions(stateWindow)
    if len(available_actions) == 0:
        return 0

    stateString = str(stateWindow)

    # print(stateString, available_actions)
    # if len(available_actions) == 0:
    # input("No available actions")
    return max([qDict[stateString][action] for action in available_actions])


def getBestNextCenterPosition(minesweeper):
    numberedTiles = minesweeper.getAllNumberedTiles()

    if len(numberedTiles) >= 0:
        numberedTilesWithMineCount = []
        for tile in numberedTiles:
            numberedTilesWithMineCount.append((tile, minesweeper.getNumberOfNumberedTile(tile), len(minesweeper.getUnknownNeighborPositions(tile))))

        sorted_list = sorted(numberedTilesWithMineCount, key=lambda x: (x[-2], x[-1]))

        for data in sorted_list:
            tilePos = data[0]
            tileValue = data[1]
            tileUnknownCount = data[2]

            if tileUnknownCount > 0:
                unknownNeighborPositions = minesweeper.getUnknownNeighborPositions(tilePos)
                # print("unknownNeighborPositions", unknownNeighborPositions)

                return random.choice(unknownNeighborPositions)

    interactable = minesweeper.getAllInteractableTilesPostitions()
    if len(interactable) == 0:
        return "GAME OVER"
    else:
        return random.choice(interactable)


def calculateGloablPosFromWindowAction(actionPos, windowCenterPos):
    return (actionPos[0] + windowCenterPos[0] - 1, actionPos[1] + windowCenterPos[1] - 1)


def getStateWindow(windowCenterPos):
    # print("getStateWindow", windowCenterPos)
    windowDict = minesweeper.get3x3WindowOfBoard(windowCenterPos)
    # print(windowDict)
    window = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]

    globalToLocalZeroZero = (windowCenterPos[0] - 1, windowCenterPos[1] - 1)

    for pos in windowDict:
        value = windowDict[pos]
        localX = pos[0] - globalToLocalZeroZero[0]
        localY = pos[1] - globalToLocalZeroZero[1]
        window[localX][localY] = value

    # print(window)
    # exit()
    return window


def main():
    while (minesweeper.winCount + minesweeper.loseCount) <= MAX_TRAINING_GAMES - 1:
        windowCenterPosition = (0, 0)
        stateWindow = getStateWindow(windowCenterPosition)
        stateString = str(stateWindow)

        while minesweeper.isGameOver() is False:
            available_actions = get_available_actions(stateWindow)
            if np.random.rand() < EXPLORATION_PROB:
                randomIndex = random.randint(0, len(available_actions) - 1)
                action = available_actions[randomIndex]
            else:
                action = myArgMax(qDict, stateString, available_actions)

            # print(stateWindow)
            # if action == None:
            #     input("No action")
            actionPos, actionType = action
            gloablPos = calculateGloablPosFromWindowAction(actionPos, windowCenterPosition)

            correctlySetFlag = False

            if actionType == FLAGGED:
                correctlySetFlag = minesweeper.setFlag(gloablPos)

                # if correctlySetFlag == False:
                # print("Flagged wrong tile")
                # input()
            elif actionType == CLICK:
                minesweeper.clickTile(gloablPos)

            windowCenterPosition = getBestNextCenterPosition(minesweeper)
            # if minesweeper.checkIfPositionIsFlagged(windowCenterPosition):
            #     print("windowCenterPosition is Flagged")
            #     input()

            if windowCenterPosition == "GAME OVER":
                next_stateWindow = "GAME OVER"
            else:
                next_stateWindow = getStateWindow(windowCenterPosition)

            # if flaggedTileIsMine != None:
            #     if flaggedTileIsMine == False:
            #         minesweeper.setGameOver(won=False)

            reward = 0
            if minesweeper.isLose():
                goodPercentage = minesweeper.tilesUnveiled / minesweeper.GOOD_TILES_COUNT
                reward = -goodPercentage

            elif minesweeper.isWin():
                reward = 1
            else:
                goodPercentage = minesweeper.tilesUnveiled / minesweeper.GOOD_TILES_COUNT
                reward = goodPercentage

            if correctlySetFlag:
                reward += 1 / minesweeper.MINE_COUNT

            qDict[stateString][action] = reward + DISCOUNT_FACTOR * getMaxReward(next_stateWindow)

            stateWindow = next_stateWindow
            stateString = str(stateWindow)

        # print("r")
        minesweeper.restartGame()

    onTrainingFinished()


def onTrainingFinished():
    ad = f"LR({LEARNING_RATE})_DF({DISCOUNT_FACTOR})_EP({EXPLORATION_PROB})_M{MAX_TRAINING_GAMES}"
    header = minesweeper.addGameSummaryHeader(ad)

    toSave = toAppendToParameterLogs + header + "\n\n"
    with open(parameterLogsFileName, "a") as file:
        file.write(toSave)


if __name__ == "__main__":
    try:
        main()
    except:
        pass

