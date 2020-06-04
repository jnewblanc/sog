''' test_game '''
import unittest

from common.testLib import TestGameBase
from common.general import logger
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

    doorOpenAttributes = [
        "objId", "_name", "_closed"]

    doorLockAttributes = doorOpenAttributes + [
        "_locked", "_locklevel", "_lockId"]

    doorTrapAttributes = doorLockAttributes + [
        "_traplevel", "_poison", "_toll"]

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
        roomObj = self.createRoom(num=99990)
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
        tmpRoomNum = 99980
        # clean up the test room before we start
        self.purgeTestRoomData(roomNums=[tmpRoomNum])
        gameObj = self.getGameObj()
        charObj = self.getCharObj()
        charObj.setName('deadGuy')
        charObj.setHitPoints(10)
        roomObj = self.createRoom(num=tmpRoomNum)
        roomObj._inventory = []
        roomObj.save()
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

        self.joinRoom(room=tmpRoomNum)
        self.logRoomInventory(charObj)
        assert len(charObj.getRoom().getInventory()) == 5, (
            "player's belongings should have persisted in room inventory")
        logger.info(str(charObj.getRoom().getInventory()))

        self.joinRoom(room=self._testRoomNum)
        self.logRoomInventory(charObj)
        self.joinRoom(room=tmpRoomNum)
        self.logRoomInventory(charObj)
        assert len(charObj.getRoom().getInventory()) == 0, (
            "player's belongings in room inventory should only persist once")

        self.purgeTestRoomData(roomNums=[tmpRoomNum])

    def doorTestSetUp(self):
        doorObj1 = self.createObject(num=99997, type='Door', name='door1')
        doorObj1._toWhere = 99993
        doorObj1._correspondingDoorId = 99996
        doorObj1._closed = False
        doorObj2 = self.createObject(num=99996, type='Door', name='door2')
        doorObj2._toWhere = 99992
        doorObj2._correspondingDoorId = 99997
        doorObj2._closed = False
        roomObj1 = self.createRoom(num=99992)
        roomObj1._inventory = []
        roomObj1.addToInventory(doorObj1)
        roomObj2 = self.createRoom(num=99993)
        roomObj2._inventory = []
        roomObj2.addToInventory(doorObj2)
        return roomObj1, roomObj2, doorObj1, doorObj2

    def showDoors(self, doorList, attList=[]):
        charObj = self.getCharObj()  # need any charObj, just to get txtBanner
        gameCmdObj = self.getGameCmdObj()
        gameCmdObj.do_look("door1")
        for door in doorList:
            if len(attList):
                tmplist = []
                for att in attList:
                    tmplist.append(att + " = " + str(getattr(door, att)))
                logger.info('\n' + charObj.client.txtBanner(door.getName()) +
                            '\n' + '\n'.join(tmplist))
            else:
                logger.info(charObj.client.txtBanner(door.getName()) + '\n' +
                            door.debug())

    def testDoorsInActiveRooms(self):
        ''' Set up a pair of doors and verify that door actions work '''
        gameObj = self.getGameObj()
        gameCmdObj = self.getGameCmdObj()
        charObj = self.getCharObj()
        charObj.setName('doorOpener')
        charObj.setHitPoints(10)
        (roomObj1, roomObj2, doorObj1, doorObj2) = self.doorTestSetUp()

        self.joinRoom(room=roomObj1)

        # Add room with 2nd door to active rooms list
        gameObj.addToActiveRooms(roomObj2)

        # test that doors are set up correctly
        assert doorObj1.getToWhere() == roomObj2.getId()
        assert doorObj2.getToWhere() == roomObj1.getId()
        assert doorObj1.getCorresspondingDoorId() == doorObj2.getId()
        assert doorObj2.getCorresspondingDoorId() == doorObj1.getId()

        logger.info("Test: Original State")
        self.showDoors([doorObj1, doorObj2], self.doorOpenAttributes)

        # Open door1
        self.logRoomInventory(charObj)
        msg = "Opening door should succeed"
        logger.info("Test: " + msg)
        logger.warning("Opening Door")
        assert not gameCmdObj.do_open("door1")  # cmds always return False
        assert doorObj1.isOpen(), msg

        self.showDoors([doorObj1, doorObj2], self.doorOpenAttributes)

        # close door1 - check that its closed, and corresponding door is closed
        msg = "Closing door - both doors should be closed"
        logger.info("Test: " + msg)
        logger.warning("Closing Door")
        assert not gameCmdObj.do_close("door1")  # cmds always return False
        self.showDoors([doorObj1, doorObj2], self.doorOpenAttributes)
        assert doorObj1.isClosed(), msg  # Door should be closed
        assert doorObj2.isClosed(), msg  # Corresponding Door should be closed
        self.logRoomInventory(charObj)

        # Re-open door1 after being closed
        msg = "Opening door after it was closed - both doors should be open"
        logger.info("Test: " + msg)
        logger.warning("Opening Door")
        assert not gameCmdObj.do_open("door1")  # cmds always return False
        self.showDoors([doorObj1, doorObj2], self.doorOpenAttributes)
        assert doorObj1.isOpen()  # Door should be open
        assert doorObj2.isOpen()  # Corresponding Door should be open

        # # self._spring = True   # automatically close if nobody is in the room
        #
        keyObj1 = self.createObject(num=99996, type='Key', name='goodkey')
        keyObj1._lockId = 99999
        keyObj2 = self.createObject(num=99995, type='Key', name='badkey')
        keyObj2._lockId = 99990
        charObj.addToInventory(keyObj1)
        charObj.addToInventory(keyObj2)

        msg = "Locking any door without key should fail"
        logger.info("Test: " + msg)
        assert not gameCmdObj.do_lock("door1")  # cmds always return False
        assert not doorObj1.isLocked(), msg

        msg = "Locking an open door with key should fail"
        logger.info("Test: " + msg)
        assert not gameCmdObj.do_lock("door1 goodkey")  # cmds always return False
        assert not doorObj1.isLocked(), msg

        logger.warning("Closing Door")
        assert not gameCmdObj.do_close("door1")  # cmds always return False
        self.showDoors([doorObj1], self.doorLockAttributes)

        msg = "Locking closed door with no lock should fail"
        logger.info("Test: " + msg)
        assert not gameCmdObj.do_lock("door1 goodkey")  # cmds always return False
        assert not doorObj1.isLocked(), msg

        logger.warning("Adding lock level and lock id")
        doorObj1._locklevel = 1
        doorObj1._lockId = 99999
        self.showDoors([doorObj1], self.doorLockAttributes)

        msg = "Locking door with bad key should fail"
        logger.info("Test: " + msg)
        assert not gameCmdObj.do_lock("door1 badkey")  # cmds always return False
        assert not doorObj1.isLocked(), msg

        msg = "Locking door with good key should succeed - both should be locked"
        logger.info("Test: " + msg)
        assert not gameCmdObj.do_lock("door1 goodkey")  # cmds always return False
        self.showDoors([doorObj1, doorObj2], self.doorLockAttributes)
        assert doorObj1.isLocked(), msg
        assert doorObj2.isLocked(), msg

        msg = "Opening a locked door should fail - door should remain closed"
        logger.info("Test: " + msg)
        assert not gameCmdObj.do_open("door1")  # cmds always return False
        assert doorObj1.isClosed(), msg
        assert doorObj1.isLocked(), msg

        msg = "Unlocking a locked door with key should succeed, both should be unlocked"
        logger.info("Test: " + msg)
        logger.warning("Unlocking Door")
        assert not gameCmdObj.do_unlock("door1 goodkey")  # cmds always return False
        self.showDoors([doorObj1], self.doorLockAttributes)
        assert doorObj1.isUnlocked(), msg
        assert doorObj2.isUnlocked(), msg

        msg = "Opening a previously locked door should succeed - both should be open"
        logger.info("Test: " + msg)
        logger.warning("Opening Door")
        assert not gameCmdObj.do_open("door1")  # cmds always return False
        self.showDoors([doorObj1], self.doorLockAttributes)
        assert doorObj1.isOpen(), msg
        assert doorObj2.isOpen(), msg

        msg = "Opening door with trap - char should be damaged"
        logger.info("Test: " + msg)
        charObj.client.popOutSpool()  # Clear the output spool
        charObj._instanceDebug = True
        charObj.dexterity = -1000  # make sure random odds don't break tests
        charObj._level = -1000     # make sure random odds don't break tests
        logger.warning("Adding trap level")
        doorObj1._traplevel = 1
        doorObj1.close(charObj)
        self.showDoors([doorObj1], self.doorTrapAttributes)
        charObj.setMaxHP(100)
        charObj.setHitPoints(100)
        assert not gameCmdObj.do_open("door1")  # cmds always return False
        charObj._instanceDebug = False
        logger.info("OutSpool: " + charObj.client.popOutSpool())
        assert charObj.getHitPoints() < 100, msg

        msg = "Opening door with trap and poison - char should be poisoned"
        logger.info("Test: " + msg)
        charObj._instanceDebug = True
        logger.warning("Adding poison to trap")
        doorObj1._poison = True
        doorObj1.close(charObj)
        self.showDoors([doorObj1], self.doorTrapAttributes)
        charObj.setMaxHP(100)
        charObj.setHitPoints(100)
        assert not gameCmdObj.do_open("door1")  # cmds always return False
        charObj._instanceDebug = False
        logger.info("OutSpool: " + charObj.client.popOutSpool())
        assert charObj.getHitPoints() < 100
        assert charObj.isPoisoned(), msg

#        doorObj1._toll = True

        self.purgeTestRoomData(roomNums=[99992, 99993])


if __name__ == '__main__':
    unittest.main()
