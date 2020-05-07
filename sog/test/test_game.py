''' test_game '''
import unittest

from common.test import TestGameBase
# from common.general import logger
# import room
# import creature


class TestGame(TestGameBase):

    def testGameInstanciation(self):
        gameObj = self.getGameObj()
        assert gameObj.isValid()
        out = "Could not instanciate the game object"
        self.assertEqual(gameObj._startdate != '', True, out)

    def testToggleInstanceDebug(self):
        gameObj = self.getGameObj()
        startState = gameObj.getInstanceDebug()
        gameObj.toggleInstanceDebug()
        out = "toggleInstanceDebug could not be set"
        self.assertEqual(gameObj.getInstanceDebug() != startState, True, out)
        gameObj.toggleInstanceDebug()
        out = "toggleInstanceDebug could not be set"
        self.assertEqual(gameObj.getInstanceDebug() == startState, True, out)

    # def testAsync(self):
    #     gameObj = self.getGameObj()
        # gameObj.asyncTasks()
        # gameObj.asyncNonPlayerActions()
        # gameObj.asyncCharacterActions()

    def testEncounter(self):
        self.joinRoom(15)
        roomObj = self.getRoomObj()
        gameObj = self.getGameObj()
        gameObj.creatureEncounter(roomObj)


class TestGameCmd(TestGameBase):

    def testGameCmdInstanciation(self):
        gameCmdObj = self.getGameCmdObj()
        out = "Could not instanciate the gameCmd object"
        self.assertEqual(gameCmdObj._lastinput == '', True, out)


if __name__ == '__main__':
    unittest.main()
