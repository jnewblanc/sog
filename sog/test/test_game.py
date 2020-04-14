import unittest

import game


class TestGame(unittest.TestCase):

    def testGameInstanciation(self):
        gameObj = game.Game()
        out = "Could not instanciate the game object"
        self.assertEqual(gameObj._startdate != '', True, out)


class TestGameCmd(unittest.TestCase):

    def testGameCmdInstanciation(self):
        gameCmdObj = game.GameCmd()
        out = "Could not instanciate the gameCmd object"
        self.assertEqual(gameCmdObj._lastinput == '', True, out)


if __name__ == '__main__':
    unittest.main()
