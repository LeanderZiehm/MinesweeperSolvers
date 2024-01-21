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

SAVE_QDICT = False


BOARD_SIZE = (4, 4)
MAX_TRAINING_GAMES = 1000000000000


FILENAME_TO_LOAD = "qDict(4, 4)100000.txt"


LEARNING_RATE = 0.95 
DISCOUNT_FACTOR = 0.4  
EXPLORATION_PROB = 0.1 

CUSTOM_MINE_COUNT = None

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

if len(sys.argv) >= 8:
    CUSTOM_MINE_COUNT = int(sys.argv[7])


pathOfThisFile = os.path.dirname(os.path.realpath(__file__))
saveFileName = f"_qDict{BOARD_SIZE}{MAX_TRAINING_GAMES}.txt"
pathToSavedDicts = pathOfThisFile #os.path.join(pathOfThisFile, "dictsSaved")

parameterLogsFileName = "parameterLogs.txt"

minesweeper = minesweeperManager.Create(BOARD_SIZE,CUSTOM_MINE_COUNT)
# minesweeper.setupSaveMetrics(os.path.join(pathOfThisFile, "metrics"))


SECONDS_BETWEEN_ACTIONS = 0


toAppendToParameterLogs = f"LEARNING_RATE: {LEARNING_RATE} | DISCOUNT_FACTOR: {DISCOUNT_FACTOR} | EXPLORATION_PROB: {EXPLORATION_PROB} For {MAX_TRAINING_GAMES} Games\n"


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


def get_available_actions():  # state is not needed because minesweeper already knows the state
    return minesweeper.getAllInteractableTilesPostitions()


def myArgMax(qAsDict, state, available_actions):
    maxAction = None
    maxValue = float("-inf")  # -100000

    for action in available_actions:
        if qAsDict[state][action] > maxValue:
            maxValue = qAsDict[state][action]
            maxAction = action

    return maxAction


def getMaxReward(state):
    available_actions = get_available_actions()
    return max([qDict[state][action] for action in available_actions])


def main():
    while (minesweeper.winCount + minesweeper.loseCount) < MAX_TRAINING_GAMES:
        state = minesweeper.getBoardString()

        while minesweeper.isGameOver() is False:
            available_actions = get_available_actions()
            if np.random.rand() < EXPLORATION_PROB:
                randomIndex = random.randint(0, len(available_actions) - 1)
                action = available_actions[randomIndex]
            else:
                action = myArgMax(qDict, state, available_actions)
            minesweeper.clickTile(action)
            next_state = minesweeper.getBoardString()
            reward = 0
            if minesweeper.isLose():
                reward = -1
            elif minesweeper.isWin():
                reward = 1
            else:
                goodPercentage = minesweeper.tilesUnveiled / minesweeper.GOOD_TILES_COUNT
                reward = goodPercentage

            qDict[state][action] = reward + DISCOUNT_FACTOR * getMaxReward(next_state)

            state = next_state

        minesweeper.restartGame()

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