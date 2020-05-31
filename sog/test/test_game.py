''' test_game '''
import os
import unittest

from common.test import TestGameBase
from common.general import logger
from common.globals import DATADIR
# import object
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

        logger.debug('Char Before Trans: ' + str(charObj.describeInventory()))
        logger.debug('Room Before Trans: ' + str(roomObj.describeInventory()))
        assert len(roomObj.getInventory()) == 0
        charObj.transferInventoryToRoom(charObj.getRoom(),
                                        gameObj.roomMsg,
                                        persist=True,
                                        verbose=False)
        logger.debug('Room After Trans: ' + str(roomObj.describeInventory()))
        logger.debug('Char After Trans: ' + str(charObj.describeInventory()))
        assert len(roomObj.getInventory()) == 5
        assert len(charObj.getInventory()) == 0
        for obj in roomObj.getInventory():
            assert obj.persistsThroughOneRoomLoad()
        roomObj.removeNonPermanents(removeTmpPermFlag=True)
        logger.debug('Room PostRemove: ' + str(roomObj.describeInventory()))
        assert len(roomObj.getInventory()) == 5
        for obj in roomObj.getInventory():
            assert not obj.persistsThroughOneRoomLoad(), (
                "Item " + str(obj.getItemId()) + " should no longer persist")

    def logRoomInventory(self, charObj):
        logger.info("----- room ID: " + charObj.getRoom().getItemId() +
                    " " + str(charObj.getRoom()) + ' -----')
        logger.info(charObj.getRoom().display(charObj))
        logger.info(str(charObj.getRoom().getInventory()))
        logger.info("")

    def testPlayerDeath(self):
        # clean up the test room before we start
        testRoomFilename = os.path.abspath(DATADIR + '/Room/99999.json')
        try:
            os.remove(testRoomFilename)
            logger.info("Removing test datafile " + testRoomFilename)
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

        assert len(charObj.getInventory()) == 5
        assert len(roomObj.getInventory()) == 0

        gameObj.applyPlayerDamage(charObj, creObj, 11)

        self.logRoomInventory(charObj)
        assert len(charObj.getInventory()) == 0, (
            "player's belongings should be removed as they are dumped to room")
        assert len(charObj.getRoom().getInventory()) == 0

        self.joinRoom(room=99999)
        self.logRoomInventory(charObj)
        assert len(charObj.getRoom().getInventory()) == 5, (
            "player's belongings should have persisted in room inventory")
        logger.info(str(charObj.getRoom().getInventory()))

        self.joinRoom(room=self._testRoomNum)
        self.logRoomInventory(charObj)
        self.joinRoom(room=99999)
        self.logRoomInventory(charObj)
        assert len(charObj.getRoom().getInventory()) == 0, (
            "player's belongings in room inventory should only persist once")

        try:
            os.remove(testRoomFilename)
            logger.info("Removed test datafile " + testRoomFilename)
        except OSError:
            pass

    def testDoors(self):
        ''' Set up a pair of doors and verify that door actions work '''
        # gameObj = self.getGameObj()
        gameCmdObj = self.getGameCmdObj()
        charObj = self.getCharObj()
        charObj.setName('doorOpener')
        charObj.setHitPoints(10)
        doorObj1 = self.createObject(num=99997, type='Door', name='door1')
        doorObj1._toWhere = 99991
        doorObj1._correspondingDoorId = 99996
        doorObj1._closed = False
        doorObj2 = self.createObject(num=99996, type='Door', name='door2')
        doorObj2._toWhere = 99990
        doorObj2._correspondingDoorId = 99997
        doorObj2._closed = False
        roomObj1 = self.createRoom(num=99990)
        roomObj1._inventory = []
        roomObj1.addToInventory(doorObj1)
        roomObj2 = self.createRoom(num=99991)
        roomObj2._inventory = []
        roomObj2.addToInventory(doorObj2)

        self.joinRoom(room=roomObj1)

        # test that doors are set up correctly
        assert doorObj1.getToWhere() == roomObj2.getId()
        assert doorObj2.getToWhere() == roomObj1.getId()
        assert doorObj1.getCorresspondingDoorId() == doorObj2.getId()
        assert doorObj2.getCorresspondingDoorId() == doorObj1.getId()

        # Open door1
        self.logRoomInventory(charObj)
        assert not gameCmdObj.do_open("door1")  # cmds always return False

        # close door1 - check that its closed, and corresponding door is closed
        assert not gameCmdObj.do_close("door1")  # cmds always return False
        assert doorObj1.isClosed()  # Door should be closed
        # assert doorObj2.isClosed()  # Corresponding Door should be closed
        #
        # # Re-open door1 after being closed
        # self.logRoomInventory(charObj)
        # assert not gameCmdObj.do_open("door1")  # cmds always return False
        # assert not doorObj1.isClosed()  # Door should be closed
        # assert not doorObj2.isClosed()  # Corresponding Door should be closed
        #
        # # self._spring = True   # automatically close if nobody is in the room
        #
        # ''' test lock/unlock/locklevels/keys '''
        # # self._locked = False
        # # self._locklevel = 0  # 0=no lock, -1=unpickable, 1=minor lock
        # # self._lockId = 0     # keys matching this lockId will open it
        #
        # ''' test traps/poison '''
        # # self._poison = False  # when trapped, this flag inflicts poison
        # # self._traplevel = 0  # 0=no trap, 1=minor trap
        #
        # ''' test toll '''
        # # self._toll = 0       # 0=no toll, amount to deduct to open


if __name__ == '__main__':
    unittest.main()
