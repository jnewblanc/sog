''' test_game '''
import unittest

from common.test import TestGameBase
from common.general import logger
# import room
# import creature


class TestGame(TestGameBase):

    def setTestName(self, name=''):
        self._testName = __class__.__name__

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

    def testGameCmdGetObj(self):
        gameCmdObj = self.getGameCmdObj()
        roomObj = self.getRoomObj()
        charObj = self.getCharObj()

        obj = self.createObject(type='Weapon', name='laser')
        obj._singledesc = "green laser"
        roomObj.addToInventory(obj)
        logger.info("\n" + roomObj.display(charObj))
        logger.info("Before:\n" + charObj.inventoryInfo())
        assert not gameCmdObj.do_get("laser")  # cmds always return False
        logger.info("After:\n" + charObj.inventoryInfo())
        assert obj not in roomObj.getInventory()
        assert obj in charObj.getInventory()

    def testGameCmdGetCoins(self):
        gameCmdObj = self.getGameCmdObj()
        roomObj = self.getRoomObj()
        charObj = self.getCharObj()

        charObj.setCoins(0)
        assert charObj.getCoins() == 0
        coinObj = self.createObject(type='Coins', name='coins')
        coinObj._value = 50
        roomObj.addToInventory(coinObj)
        logger.info("\n" + roomObj.display(charObj))
        logger.info("Before:\n" + charObj.financialInfo())
        assert not gameCmdObj.do_get("coins")  # cmds always return False
        logger.info("After:\n" + charObj.financialInfo())
        assert coinObj not in roomObj.getInventory()
        assert coinObj not in charObj.getInventory()
        assert charObj.getCoins() == 50


if __name__ == '__main__':
    unittest.main()
