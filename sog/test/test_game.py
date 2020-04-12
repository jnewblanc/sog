import unittest

import game


# class TestGame(unittest.TestCase):

    # def testSplitCmd(self):
    #     inputs = ['use staff',
    #               'use staff 1',
    #               'use staff player',
    #               'use staff 1 player',
    #               'use staff player 2',
    #               'use staff 1 player 2']
    #     output = [('use', ['staff']),
    #               ('use', ['staff 1']),
    #               ('use', ['staff', 'player']),
    #               ('use', ['staff 1', 'player']),
    #               ('use', ['staff', 'player 2']),
    #               ('use', ['staff 1', 'player 2'])]
    #     gameObj = game.Game()
    #     for num, input in enumerate(inputs):
    #         inWords = input.split(' ')
    #         resultlist = gameObj.splitCmd(inWords)
    #         out = ("Input: " + str(input) + " - Output: " + str(resultlist) +
    #                " - Expected: " + str(output[num]))
    #         self.assertEqual(resultlist == output[num], True, out)


# if __name__ == '__main__':
#     unittest.main()
