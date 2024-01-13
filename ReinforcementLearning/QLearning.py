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
import socketPlotter

SAVE_AND_LOAD_QDICT_FROM_FILE = False


BOARD_SIZE = (5, 5)
MAX_TRAINING_GAMES = 100



LEARNING_RATE = 0.95#1
DISCOUNT_FACTOR = 0.5#0.93
EXPLORATION_PROB = 0.1#0.4

if len(sys.argv) >= 2:
    LEARNING_RATE = float(sys.argv[1])

if len(sys.argv) >= 3:
    DISCOUNT_FACTOR = float(sys.argv[2])

if len(sys.argv) >= 4:
    EXPLORATION_PROB = float(sys.argv[3])

if len(sys.argv) >= 5:
    MAX_TRAINING_GAMES = int(sys.argv[4])


FILENAME_TO_LOAD = "_qDict4.txt" #"_qDict(5, 5)1000000.txt"


pathOfThisFile = os.path.dirname(os.path.realpath(__file__))
saveFileName = f"_qDict{BOARD_SIZE}{MAX_TRAINING_GAMES}.txt"
pathToSavedDicts = os.path.join(pathOfThisFile,"dictsSaved")

parameterLogsFileName = "parameterLogs.txt"

minesweeper = minesweeperManager.Create(BOARD_SIZE)
# minesweeper.setupMaxGames(metricsSaved)
minesweeper.setupSaveMetrics(os.path.join(pathOfThisFile,"metrics"))
# minesweeper.startLivePlotter()

# socketPlotter.startClient()



SECONDS_BETWEEN_ACTIONS = 0



toAppendToParameterLogs = f"LEARNING_RATE: {LEARNING_RATE} | DISCOUNT_FACTOR: {DISCOUNT_FACTOR} | EXPLORATION_PROB: {EXPLORATION_PROB} For {MAX_TRAINING_GAMES} Games\n"


qDict = defaultdict(lambda: defaultdict(lambda: 0))


def save_file():
    # # 12-26-2023_2-51-51PM
    dictToSave = {}
    for key in qDict:
        currentDict = qDict[key]
        cleanedDict = {}
        for key2 in currentDict:
            if currentDict[key2] == 0:
                # print("0")
                continue
            else:
                cleanedDict[key2] = round(currentDict[key2], 2)
        if cleanedDict:
            dictToSave[key] = cleanedDict

    textToSave = str(dictToSave)
    # minesweeperManager.addGameSummaryHeader()
    minesweeperManager.saveFile(saveFileName, textToSave, pathToSavedDicts )


if SAVE_AND_LOAD_QDICT_FROM_FILE:
    atexit.register(save_file)


# def getLatestFile(inputFullName):  # inputFileName
#     prefix, suffix = os.path.splitext(inputFullName)
#     # print(prefix, suffix)
#     matching_files = [file for file in os.listdir(pathOfThisFile) if file.startswith(prefix) and file.endswith(suffix)]
#     # print(matching_files)
#     if matching_files:
#         latest_file = max(matching_files, key=lambda x: int(x[len(prefix) : -len(suffix)]))
#         # print(latest_file)
#         return latest_file
#     else:
#         print("No matching files found.")
#         return None


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
    # maxAction = random.choice(available_actions)
    # maxValue = qAsDict[state][maxAction]  # float("-inf")  # -100000

    for action in available_actions:
        if qAsDict[state][action] > maxValue:
            maxValue = qAsDict[state][action]
            maxAction = action

    return maxAction


def getMaxReward(state):
    available_actions = get_available_actions()
    return max([qDict[state][action] for action in available_actions])


def main():
    # global toAppendToParameterLogs
    # gameCounter = 0
    while (minesweeper.winCount + minesweeper.loseCount) < MAX_TRAINING_GAMES:
        state = minesweeper.getBoardString()

        allCharsAreHashtags = state.count("#") == len(state)
        if allCharsAreHashtags:
            startAction = minesweeper.SIZE_X // 2, minesweeper.SIZE_Y // 2
            minesweeper.clickTile(startAction)
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
                goodPercentage = minesweeper.tilesUnveiled / minesweeper.GOOD_TILES_COUNT
                # reward =  -1 + goodPercentage #-minesweeper.SIZE_X * minesweeper.SIZE_Y 
                reward =  -minesweeper.SIZE_X * minesweeper.SIZE_Y 
                print("lose")

            elif minesweeper.isWin():
                # reward = 1000#minesweeper.SIZE_X * minesweeper.SIZE_Y
                reward = minesweeper.SIZE_X * minesweeper.SIZE_Y
                print("win")
            else:
                reward = 1
                print("normal click")


            qDict[state][action] = reward + DISCOUNT_FACTOR * getMaxReward(next_state)

            state = next_state
            # if SECONDS_BETWEEN_ACTIONS > 0:
                # time.sleep(SECONDS_BETWEEN_ACTIONS)

        # winNumber = 1 if minesweeper.isWin() else 0
        # loseNumber = 1 if minesweeper.isLose() else 0

        # toAppendToParameterLogs += f"({gameCounter},{loseNumber},{winNumber},{minesweeper.tilesUnveiled})"
        # toAppendToParameterLogs += f"({gameCounter},{minesweeper.loseCount},{minesweeper.winCount},{minesweeper.tilesUnveiled})"

        ##
        # if minesweeper.isWin():
        #     txt = f"Win {minesweeper.winCount} after {gameCounter} games."
        #     print(txt)
        ##
        
        #     toAppendToParameterLogs += "+++++++++++++++++++++++++++++="
        #     # toAppendToParameterLogs += "#" + txt + "\n"
        # elif minesweeper.isLose():
        #     toAppendToParameterLogs += "-"

        # socketPlotter.plot(minesweeper.tilesUnveiled)

        # toAppendToParameterLogs += f" [{gameCounter}] {minesweeper.tilesUnveiled}c  | {minesweeper.winCount}W | {minesweeper.loseCount}L\n"

        # toAppendToParameterLogs += "\n"

        minesweeper.restartGame()
        # gameCounter += 1

    ad = f"LR({LEARNING_RATE})_DF({DISCOUNT_FACTOR})_EP({EXPLORATION_PROB})_M{MAX_TRAINING_GAMES}"
    header = minesweeper.addGameSummaryHeader(ad)
    # toPrint = f"Training finished after {gameCounter} episodes."
    # print(toPrint)

    toSave = toAppendToParameterLogs+header+"\n\n"
    print(toSave)
    # os.system("say " + toPrint)
    with open(parameterLogsFileName, "a") as file:
        file.write(toSave)
    # os.startfile(parameterLogsFileName)
    # input("Press enter to close terminal.")


if __name__ == "__main__":
    main()
