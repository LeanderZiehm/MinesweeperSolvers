"Credit: base game code was adapted from https://github.com/ripexz/python-tkinter-minesweeper"
from tkinter import *
from collections import deque
import random
import itertools
import os
import atexit
import sys
import time

sys.path.insert(1, os.path.join(sys.path[0], ".."))
# import socketPlotter

AUTO_RESTART = FALSE
SAVE_PATH = None

DEBUG_BOARD_STATE = True
SOCKET_PLOTTER_ACTIVATED = False

DEBUG = False

STATE_DEFAULT = 0
STATE_CLICKED = 1
STATE_FLAGGED = 2

BTN_CLICK = "<Button-1>"
BTN_FLAG = "<Button-3>"

window = None
pathToImages = "images/"
pathToImages = os.path.join(os.path.dirname(__file__), pathToImages)


start_time = time.time()

METRICS_FILE_NAME = ""


class Create:
    def __init__(self, SIZE=(8, 8), MINE_COUNT=None):
        tk = Tk()
        tk.title("M")  # Minesweeper

        self.SIZE_X, self.SIZE_Y = SIZE
        if MINE_COUNT == None:
            MINE_PERCENTAGE = 0.156
            MINE_COUNT = round(self.SIZE_X * self.SIZE_Y * MINE_PERCENTAGE)

        self.MINE_COUNT = MINE_COUNT
        self.WON = "won"
        self.LOST = "lost"
        self.TOTAL_TILE_COUNT = self.SIZE_X * self.SIZE_Y
        self.GOOD_TILES_COUNT = self.TOTAL_TILE_COUNT - self.MINE_COUNT

        self.loseCount = 0
        self.winCount = 0
        self.MAX_GAMES = 1000000

        self.images = {
            "unknown": PhotoImage(file=pathToImages + "tile_plain.gif"),
            "clicked": PhotoImage(file=pathToImages + "tile_clicked.gif"),
            "mine": PhotoImage(file=pathToImages + "tile_mine.gif"),
            "flag": PhotoImage(file=pathToImages + "tile_flag.gif"),
            "wrong": PhotoImage(file=pathToImages + "new2_wrong.gif"),
            "wrongFlag": PhotoImage(file=pathToImages + "wrongFlag.gif"),
            "correctFlag": PhotoImage(file=pathToImages + "correctFlag.gif"),
            "green": PhotoImage(file=pathToImages + "green.gif"),
            "numbers": [],
        }
        for i in range(1, 9):
            self.images["numbers"].append(PhotoImage(file=pathToImages + "tile_" + str(i) + ".gif"))

        self.tk = tk
        self.frame = Frame(self.tk)

        self.frame.pack()

        self.labels = {"minesCount": Label(self.frame, font=("Helvetica", 12))}
        self.labels["minesCount"].grid(row=self.SIZE_X + 1, column=2, columnspan=int(self.SIZE_Y / 2))  # bottom left
        self.labels["losses"] = Label(self.frame, font=("Helvetica", 10))
        self.labels["losses"].grid(row=self.SIZE_X + 1, column=self.SIZE_Y - 2, columnspan=2)
        self.labels["wins"] = Label(self.frame, font=("Helvetica", 10))
        self.labels["wins"].grid(row=self.SIZE_X + 1, column=0, columnspan=2)

        self.tiles = {}
        self._allGridIndeciesForMineGeneration = list(itertools.product(range(self.SIZE_Y), range(self.SIZE_X)))

        for y in range(0, self.SIZE_Y):
            for x in range(0, self.SIZE_X):
                if x == 0:
                    self.tiles[y] = {}

                id = str(y) + "_" + str(x)

                gfx = self.images["unknown"]

                tile = {
                    "id": id,
                    "isMine": False,
                    "state": STATE_DEFAULT,
                    "position": (y, x),
                    "button": Button(self.frame, image=gfx),
                    "minesAround": 0,
                    "neighborPostions": None,
                }  # calculated after grid is built

                tile["button"].bind(BTN_CLICK, self.onClickXYButton(y, x))
                tile["button"].bind(BTN_FLAG, self.onClickXYFlagButton(y, x))
                tile["button"].grid(row=y, column=x)
                self.tiles[y][x] = tile

        self.restartGame()  # start game

    def changeBackgroundColor(self, color):
        self.tk.configure(background=color)
        self.frame.configure(background=color)
        for l in self.labels.values():
            l.config(bg=color)

    def setup(self):
        self.restoreOldSelectedTileToNormalColor()
        self.gameStatus = False
        self.flagCount = 0
        self.correctFlagCount = 0
        self.tilesUnveiled = 0
        self.firstClick = True
        self.currentSelectedTile = None
        self.turnCount = 0
        self.gameStartTime = time.time()

        mineTuples = random.sample(self._allGridIndeciesForMineGeneration, self.MINE_COUNT)

        for y in range(0, self.SIZE_Y):
            for x in range(0, self.SIZE_X):
                isMine = False
                gfx = self.images["unknown"]
                if (y, x) in mineTuples:
                    isMine = True

                self.tiles[y][x]["isMine"] = isMine
                self.tiles[y][x]["button"].config(image=gfx)
                self.tiles[y][x]["state"] = STATE_DEFAULT
                self.tiles[y][x]["minesAround"] = 0
                self.tiles[y][x]["neighborPostions"] = None

        for y in range(0, self.SIZE_Y):
            for x in range(0, self.SIZE_X):
                mc = 0
                neighbors = self.calculateNeighbors(y, x)
                for n in neighbors:
                    mc += 1 if n["isMine"] else 0
                self.tiles[y][x]["minesAround"] = mc

    def setupSaveMetrics(self, savePath):
        global SAVE_PATH
        SAVE_PATH = savePath
        global toSave
        global METRICS_FILE_NAME

        parentDirName = os.path.basename(savePath)
        METRICS_FILE_NAME = f"metrics{parentDirName}({self.SIZE_X}x{self.SIZE_Y}){self.MAX_GAMES}.txt"
        atexit.register(onExit)

    def startLivePlotter(self):
        global SOCKET_PLOTTER_ACTIVATED
        SOCKET_PLOTTER_ACTIVATED = True
        # socketPlotter.startClient()

    def setupAutoRestart(self):
        global AUTO_RESTART
        AUTO_RESTART = True

    def setupDebug(self):
        global DEBUG
        DEBUG = True

    def setupSeed(self, seed):
        random.seed(seed)

    def setupMaxGames(self, maxgames):
        self.MAX_GAMES = maxgames

    def restartGame(self):
        self.setup()
        self.refreshLabels()

    def refreshLabels(self):
        self.labels["minesCount"].config(text="Mines: " + str(self.MINE_COUNT))
        self.labels["losses"].config(text="L:" + str(self.loseCount))
        self.labels["wins"].config(text="W:" + str(self.winCount))

    def setGameOver(self, won, tileButton=None):
        for y in range(0, self.SIZE_Y):
            for x in range(0, self.SIZE_X):
                if self.tiles[y][x]["isMine"] == False and self.tiles[y][x]["state"] == STATE_FLAGGED:
                    self.tiles[y][x]["button"].config(image=self.images["wrongFlag"])
                if self.tiles[y][x]["isMine"] == True and self.tiles[y][x]["state"] == STATE_FLAGGED:
                    self.tiles[y][x]["button"].config(image=self.images["correctFlag"])
                if self.tiles[y][x]["isMine"] == True and self.tiles[y][x]["state"] != STATE_FLAGGED:
                    self.tiles[y][x]["button"].config(image=self.images["mine"])

        if tileButton:
            tileButton.config(image=self.images["wrong"])

        self.gameStatus = self.WON if won else self.LOST

        if won:
            self.winCount += 1
            self.changeBackgroundColor("green")
        else:
            self.loseCount += 1
            self.changeBackgroundColor("red")
        self.refreshLabels()

        metrics = f"{self.gameStatus},{self.winCount},{self.loseCount},{round(time.time() - self.gameStartTime,2)},{self.turnCount}"
        if SAVE_PATH:
            global toSave
            toSave += metrics + "\n"
        if DEBUG:
            print(metrics)
        if SOCKET_PLOTTER_ACTIVATED:
            pass
            # socketPlotter.plot(self.winCount - self.loseCount)

        if self.winCount + self.loseCount >= self.MAX_GAMES:
            self.addGameSummaryHeader()
            exit()
            return

        if AUTO_RESTART:
            self.restartGame()

        self.tk.update()

    def getBombsLeft(self):
        return self.MINE_COUNT - self.flagCount

    def get3x3WindowOfBoard(self, windowCenterPosition):
        neighborPositons = self.getNeighborPostions(windowCenterPosition)
        windowPositons = [windowCenterPosition] + neighborPositons

        windowDict = {}

        for pos in windowPositons:
            y, x = pos

            if self.tiles[y][x]["state"] == STATE_DEFAULT:
                windowDict[pos] = -1
            elif self.tiles[y][x]["state"] == STATE_CLICKED:
                windowDict[pos] = self.tiles[y][x]["minesAround"]
            elif self.tiles[y][x]["state"] == STATE_FLAGGED:
                windowDict[pos] = -2
            else:
                assert False, "WINDOW IS DOING ELSE, this shouldn't happen LOL XD"

        return windowDict

    def getAllInteractableTilesWithProbability(self):
        minesLeft = self.getBombsLeft()
        tiles = self.getAllInteractableTilesPostitions()
        tilesWithProbability = []
        for tile in tiles:
            tilesWithProbability.append((tile, (minesLeft) * 1 / len(tiles)))
        return tilesWithProbability

    def getNeighborPostions(self, tilePos):
        y, x = tilePos
        return self.tiles[y][x]["neighborPostions"]

    def getInteractableNeighborPositions(self, tilePos):
        allNeighbours = self.getNeighborPostions(tilePos)
        return [n for n in allNeighbours if self.tiles[n[0]][n[1]]["state"] != STATE_CLICKED]

    def getUnknownNeighborPositions(self, tilePos):
        allNeighbours = self.getNeighborPostions(tilePos)
        return [n for n in allNeighbours if self.tiles[n[0]][n[1]]["state"] == STATE_DEFAULT]  ##JUMP

    def getNumberNeighborPostitions(self, tilePos):
        allNeighbours = self.getNeighborPostions(tilePos)
        return [n for n in allNeighbours if (self.tiles[n[0]][n[1]]["state"] == STATE_CLICKED and self.tiles[n[0]][n[1]]["minesAround"] > 0)]

    def getNumberOfNumberedTile(self, tilePos):
        x, y = tilePos
        return self.tiles[x][y]["minesAround"]

    def getAllNumberedTiles(self):
        allNumberedTiles = []
        for y in range(0, self.SIZE_Y):
            for x in range(0, self.SIZE_X):
                if self.tiles[y][x]["minesAround"] > 0 and self.tiles[y][x]["state"] == STATE_CLICKED:
                    allNumberedTiles.append((y, x))

        return allNumberedTiles

    def calculateNeighbors(self, y, x):
        neighbors = []
        coords = [
            (y - 1, x - 1),  # top right
            (y - 1, x),  # top middle
            (y - 1, x + 1),  # top left
            (y, x - 1),  # left
            (y, x + 1),  # right
            (y + 1, x - 1),  # bottom right
            (y + 1, x),  # bottom middle
            (y + 1, x + 1),  # bottom left
        ]
        neighborPositons = []
        for n in coords:
            y2, x2 = n

            isInsideBounds = y2 >= 0 and y2 < self.SIZE_Y and x2 >= 0 and x2 < self.SIZE_X
            if isInsideBounds:
                neighbors.append(self.tiles[y2][x2])
                neighborPositons.append((y2, x2))

        self.tiles[y][x]["neighborPostions"] = neighborPositons
        return neighbors

    def displaySelectedTile(self, tile):
        self.restoreOldSelectedTileToNormalColor()
        self.currentSelectedTile = tile
        tile["button"].config(bg="blue")

    def restoreOldSelectedTileToNormalColor(self):
        if hasattr(self, "currentSelectedTile"):
            if self.currentSelectedTile:
                self.currentSelectedTile["button"].config(bg="SystemButtonFace")

    def onClickTile(self, tile):
        wasFirstClick = self.firstClick
        self.firstClick = False
        if DEBUG:
            if DEBUG_BOARD_STATE:
                print(tile["position"])

        self.displaySelectedTile(tile)

        if tile["isMine"] == True:
            if wasFirstClick:
                clickPos = tile["position"]

                allNonBombs = [n for n in self.getAllInteractableTilesPostitions() if self.tiles[n[0]][n[1]]["isMine"] == False]
                newBombPos = random.choice(allNonBombs)

                self.tiles[newBombPos[0]][newBombPos[1]]["isMine"] = True
                oldNeighbors = self.getNeighborPostions(clickPos)
                newNeighbors = self.getNeighborPostions(newBombPos)

                tile["isMine"] = False
                tile["minesAround"] = len([n for n in self.getNeighborPostions(clickPos) if self.tiles[n[0]][n[1]]["isMine"] == True])

                for n in oldNeighbors:
                    self.tiles[n[0]][n[1]]["minesAround"] -= 1

                for n in newNeighbors:
                    actualBombCount = len([n for n in self.getNeighborPostions(n) if self.tiles[n[0]][n[1]]["isMine"] == True])

                    self.tiles[n[0]][n[1]]["minesAround"] = actualBombCount  # += 1

                    if self.tiles[n[0]][n[1]]["state"] == STATE_CLICKED:
                        self.tiles[n[0]][n[1]]["button"].config(image=self.images["numbers"][actualBombCount - 1])

            else:
                self.setGameOver(False, tileButton=tile["button"])
                return

        if tile["minesAround"] == 0:
            tile["button"].config(image=self.images["clicked"])
            self.clearSurroundingTiles(tile["id"])
        else:
            tile["button"].config(image=self.images["numbers"][tile["minesAround"] - 1])
        if tile["state"] != STATE_CLICKED:
            tile["state"] = STATE_CLICKED
            self.tilesUnveiled += 1
        if self.tilesUnveiled == self.GOOD_TILES_COUNT:
            self.setGameOver(True)

        if DEBUG:
            if DEBUG_BOARD_STATE:
                print(self.getBoardString())

    def checkIfPositionIsFlagged(self, pos):
        y, x = pos
        return self.tiles[y][x]["state"] == STATE_FLAGGED

    def onClickFlag(self, tile):
        if tile["state"] == STATE_DEFAULT:
            tile["button"].config(image=self.images["flag"])
            tile["state"] = STATE_FLAGGED
            tile["button"].unbind(BTN_CLICK)

            self.flagCount += 1
            self.refreshLabels()

            if tile["isMine"] == True:
                self.correctFlagCount += 1
            else:
                tile["button"].config(image=self.images["wrongFlag"])
                self.setGameOver(False)
                # input(f"!!!!!!!!!!!! {tile['position']} Flagged a non-mine tile. Press enter to continue!!!!!!!!!!!!!!!!")

        elif tile["state"] == STATE_FLAGGED:  # if already flagged then unflag
            tile["button"].config(image=self.images["unknown"])
            tile["state"] = 0
            tile["button"].bind(BTN_CLICK, self.onClickXYButton(tile["position"][0], tile["position"][1]))
            if tile["isMine"] == True:
                self.correctFlagCount -= 1
            self.flagCount -= 1
            self.refreshLabels()

    def clearSurroundingTiles(self, id):
        queue = deque([id])

        while len(queue) != 0:
            key = queue.popleft()
            parts = key.split("_")
            y = int(parts[0])
            x = int(parts[1])

            for tile in self.calculateNeighbors(y, x):
                self.clearTile(tile, queue)

    def clearTile(self, tile, queue):
        if tile["state"] != STATE_DEFAULT:
            return

        if tile["minesAround"] == 0:
            tile["button"].config(image=self.images["clicked"])
            queue.append(tile["id"])
        else:
            tile["button"].config(image=self.images["numbers"][tile["minesAround"] - 1])

        tile["state"] = STATE_CLICKED
        self.tilesUnveiled += 1
        if self.tilesUnveiled == self.GOOD_TILES_COUNT:
            self.setGameOver(True)

    def getAllInteractableTilesPostitions(self):
        actions = []
        for y in range(0, self.SIZE_Y):
            for x in range(0, self.SIZE_X):
                if self.tiles[y][x]["state"] == STATE_DEFAULT:
                    actions.append((y, x))
        return actions

    def onClickXYButton(self, y, x):
        return lambda Button: self.onClickTile(self.tiles[y][x])

    def onClickXYFlagButton(self, y, x):
        return lambda Button: self.onClickFlag(self.tiles[y][x])

    def clickTile(self, action):
        y, x = action
        self.onClickTile(self.tiles[y][x])
        self.tk.update()
        self.turnCount += 1

    def setFlag(self, action):
        y, x = action
        if self.tiles[y][x]["state"] == STATE_DEFAULT:
            self.onClickFlag(self.tiles[y][x])
        self.tk.update()

        if self.tiles[y][x]["isMine"] == True:
            return True
        else:
            return False
            # self.correctFlagCount += 1

    def getBoardString(self):
        boardState = ""
        for y in range(0, self.SIZE_Y):
            for x in range(0, self.SIZE_X):
                if self.tiles[y][x]["state"] == STATE_DEFAULT:
                    boardState += "#"
                elif self.tiles[y][x]["state"] == STATE_CLICKED:
                    boardState += str(self.tiles[y][x]["minesAround"])
        return boardState

    def getBoardStringAdmin(self):
        boardY = []
        for y in range(0, self.SIZE_Y):
            boardX = []
            boardY.append(boardX)
            for x in range(0, self.SIZE_X):
                if self.tiles[y][x]["isMine"]:
                    boardX.append("M")
                else:
                    boardX.append(self.tiles[y][x]["minesAround"])
        return

    # def setGameOver(self):
    #     self.gameOver(True)

    def isGameOver(self):
        return self.gameStatus == self.WON or self.gameStatus == self.LOST

    def isWin(self):
        return self.gameStatus == self.WON

    def isLose(self):
        return self.gameStatus == self.LOST

    def addGameSummaryHeader(self, ad=""):
        global METRICS_FILE_NAME
        if ad != "":
            METRICS_FILE_NAME = METRICS_FILE_NAME[: len(METRICS_FILE_NAME) - 4 - len(str(self.MAX_GAMES))] + ad + ".txt"

        global toSave
        header = (
            f"[Accuracy: {round(self.winCount / (self.winCount + self.loseCount) * 100, 2)}% on [{self.SIZE_X}x{self.SIZE_Y}] for {self.winCount+self.loseCount} games with {self.MINE_COUNT} bombs, total time: {round(time.time() - start_time,2)}s, average time per game: {round((time.time() - start_time) / (self.winCount + self.loseCount),2)}s]"
            + "\n"
        )
        toSave = header + ad + "\n" + toSave

        return header


toSave = ""


def onExit():
    saveFile(METRICS_FILE_NAME, toSave, SAVE_PATH)


def saveFile(fullFileName, textToSave, pathToSave=""):
    print(f"(Saving {fullFileName})")

    fileName, fileExtension = os.path.splitext(fullFileName)
    fileToSave = fullFileName
    fileIndex = 0
    while os.path.isfile(os.path.join(pathToSave, fileToSave)):
        fileIndex += 1
        fileToSave = fileName + "_(" + str(fileIndex) + ")" + fileExtension

    filePath = os.path.join(pathToSave, fileToSave)
    with open(filePath, "w") as file:
        file.write(textToSave)
    print(f"[Saved {fileToSave}]")


def main():
    print("[All coordinates are (y, x)]")
    print("[Auto restart enabled so you won't see the mines when losing]")

    BOARD_SIZE = (8, 8)
    MINE_COUNT = None
    if len(sys.argv) >= 2:
        BOARD_SIZE = eval(sys.argv[1])

    if len(sys.argv) >= 3:
        MINE_COUNT = int(sys.argv[2])

    minesweeper = Create(BOARD_SIZE, MINE_COUNT)
    minesweeper.setupAutoRestart()
    minesweeper.tk.mainloop()


def setBoard(minesweeper):
    u = -1
    f = -2
    g = -3

    b = [
        [0, u, u, u, 0, u, u, f],
        [0, 1, 2, 0, 0, 1, 2, 0],
        [1, 1, 1, 0, g, f, g, 0],
        [u, g, 1, 0, g, 1, g, 0],
        [u, u, 1, 0, g, g, g, 0],
        [1, 1, 1, 0, u, f, u, 0],
        [u, u, 1, 0, u, 1, u, 0],
        [u, u, 1, 0, u, u, u, 0],
    ]

    for x in range(0, 8):
        for y in range(0, 8):
            value = b[x][y]
            if value == 0:
                minesweeper.tiles[x][y]["button"].config(image=minesweeper.images["clicked"])
            elif value == u:
                minesweeper.tiles[x][y]["button"].config(image=minesweeper.images["unknown"])
            elif value == f:
                minesweeper.tiles[x][y]["button"].config(image=minesweeper.images["flag"])
            elif value == g:
                minesweeper.tiles[x][y]["button"].config(image=minesweeper.images["green"])
            else:
                minesweeper.tiles[x][y]["button"].config(image=minesweeper.images["numbers"][value - 1])

    minesweeper.tk.mainloop()


if __name__ == "__main__":
    main()
