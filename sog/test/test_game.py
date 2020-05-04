''' test_game '''
import unittest

from common.test import TestGameBase
# from common.general import logger
import game


class TestGame(TestGameBase):

    def setUp(self):
        self.banner('start', testName=__class__.__name__)

    def testGameInstanciation(self):
        gameObj = game.Game()
        out = "Could not instanciate the game object"
        self.assertEqual(gameObj._startdate != '', True, out)

    def testToggleInstanceDebug(self):
        gameObj = game.Game()
        startState = gameObj.getInstanceDebug()
        gameObj.toggleInstanceDebug()
        out = "toggleInstanceDebug could not be set"
        self.assertEqual(gameObj.getInstanceDebug() != startState, True, out)
        gameObj.toggleInstanceDebug()
        out = "toggleInstanceDebug could not be set"
        self.assertEqual(gameObj.getInstanceDebug() == startState, True, out)


class TestGameCmd(TestGameBase):

    def setUp(self):
        self.banner('start', testName=__class__.__name__)

    def testGameCmdInstanciation(self):
        gameCmdObj = game.GameCmd()
        out = "Could not instanciate the gameCmd object"
        self.assertEqual(gameCmdObj._lastinput == '', True, out)


if __name__ == '__main__':
    unittest.main()
