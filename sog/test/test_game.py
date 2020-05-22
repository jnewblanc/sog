''' test_game '''
import os
import unittest

from common.test import TestGameBase
from common.general import logger
from common.globals import DATADIR
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

    def addFiveItemsToCharacter(self, charObj):
        obj1 = self.createObject(num=99991, type='Armor', name="armor1")
        charObj.addToInventory(obj1)
        obj2 = self.createObject(num=99992, type='Weapon', name="weapon2")
        charObj.addToInventory(obj2)
        obj3 = self.createObject(num=99993, type='Shield', name="shield3")
        charObj.addToInventory(obj3)
        obj4 = self.createObject(num=99994, type='Treasure', name="treasure4")
        charObj.addToInventory(obj4)
        obj5 = self.createObject(num=99995, type='Treasure', name="treasure5")
        charObj.addToInventory(obj5)
        assert len(charObj.getInventory()) == 5

    def testTransferInventoryToRoom(self):
        gameObj = self.getGameObj()
        charObj = self.getCharObj()
        charObj.setName('deadGuy')
        charObj.setHitPoints(10)
        roomObj = self.createRoom(num=99999)
        roomObj._inventory = []
        charObj.setRoom(roomObj)
        logger.debug('Testing inventory transfer')
        self.addFiveItemsToCharacter(charObj)

        logger.debug('Char Before: ' + str(charObj.describeInventory()))
        logger.debug('Room Before: ' + str(roomObj.describeInventory()))
        assert len(roomObj.getInventory()) == 0
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

    def testPlayerDeath(self):
        # clean up the test room before we start
        filename = os.path.abspath(DATADIR + '/Room/99999.json')
        try:
            os.remove(filename)
        except OSError:
            pass
        gameObj = self.getGameObj()
        charObj = self.getCharObj()
        charObj.setName('deadGuy')
        charObj.setHitPoints(10)
        roomObj = self.createRoom(num=99999)
        roomObj._inventory = []
        self.joinRoom(room=roomObj)
        creObj = self.createCreature()
        logger.info('Testing character death')
        self.addFiveItemsToCharacter(charObj)

        logger.info("\nroom ID: " + charObj.getRoom().getItemId() +
                    " " + str(charObj.getRoom()) + "\n" +
                    charObj.getRoom().display(charObj) +
                    str(charObj.getRoom().getInventory()))
        assert len(charObj.getInventory()) == 5
        assert len(roomObj.getInventory()) == 0

        gameObj.applyPlayerDamage(charObj, creObj, 11)

        logger.info("\nroom ID: " + charObj.getRoom().getItemId() +
                    " " + str(charObj.getRoom()) + "\n" +
                    charObj.getRoom().display(charObj) +
                    str(charObj.getRoom().getInventory()))
        assert len(charObj.getInventory()) == 0
        assert len(charObj.getRoom().getInventory()) == 0

        self.joinRoom(room=99999)
        logger.info("\nroom ID: " + charObj.getRoom().getItemId() +
                    " " + str(charObj.getRoom()) + "\n" +
                    charObj.getRoom().display(charObj) +
                    str(charObj.getRoom().getInventory()))
        assert len(charObj.getRoom().getInventory()) == 5
        logger.info(str(charObj.getRoom().getInventory()))

        filename = os.path.abspath(DATADIR + '/Room/99999.json')
        try:
            os.remove(filename)
        except OSError:
            pass


if __name__ == '__main__':
    unittest.main()
