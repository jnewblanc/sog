''' test_game '''
import unittest

from common.test import TestGameBase
from common.general import logger
import object
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

    def testTransferInventoryToRoom(self):
        gameObj = self.getGameObj()
        charObj = self.createCharacter()
        charObj.setName('deadGuy')
        charObj.setHitPoints(10)
        roomObj = self.createRoom(num=99999)
        roomObj._inventory = []
        charObj.setRoom(roomObj)
        logger.debug('Testing inventory on death')
        obj1 = object.Armor(99999)
        obj1._singledesc = "good armor"
        charObj.addToInventory(obj1)
        obj2 = object.Weapon(99999)
        obj2._singledesc = "good weapon"
        charObj.addToInventory(obj2)
        obj3 = object.Shield(99999)
        obj3._singledesc = "good shield"
        charObj.addToInventory(obj3)
        obj4 = object.Treasure(99999)
        obj4._singledesc = "treasure1"
        charObj.addToInventory(obj4)
        obj5 = object.Treasure(99998)
        obj5._singledesc = "treasure2"
        charObj.addToInventory(obj5)

        logger.debug('Char Before: ' + str(charObj.describeInventory()))
        logger.debug('Room Before: ' + str(roomObj.describeInventory()))
        assert len(roomObj.getInventory()) == 0
        assert len(charObj.getInventory()) == 5
        charObj.transferInventoryToRoom(charObj.getRoom(),
                                        gameObj.roomMsg,
                                        persist=True,
                                        verbose=False)
        logger.debug('Room After: ' + str(roomObj.describeInventory()))
        logger.debug('Char After: ' + str(charObj.describeInventory()))
        assert len(roomObj.getInventory()) == 5
        assert len(charObj.getInventory()) == 0
        for obj in roomObj.getInventory():
            assert obj.persistsThroughOneRoomLoad()
        roomObj.removeNonPermanents()
        logger.debug('Room PostRemove: ' + str(roomObj.describeInventory()))
        assert len(roomObj.getInventory()) == 5
        for obj in roomObj.getInventory():
            assert not obj.persistsThroughOneRoomLoad()


if __name__ == '__main__':
    unittest.main()
