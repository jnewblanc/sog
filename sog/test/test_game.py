import unittest

import game


class TestGame(unittest.TestCase):

    def testGameInstanciation(self):
        gameObj = game.Game()
        out = "Could not instanciate the game object"
        self.assertEqual(gameObj._startdate != '', True, out)


if __name__ == '__main__':
    unittest.main()
