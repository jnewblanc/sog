''' test_room '''
import unittest

from common.test import TestGameBase
from common.general import logger, targetSearch, getNeverDate
from room import RoomFactory


class TestRoom(TestGameBase):

    num = 99999

    def setTestName(self, name=''):
        self._testName = __class__.__name__

    def testValidity(self):
        roomObj = RoomFactory('room', self.num)
        assert not roomObj.isValid()
        roomObj._shortDesc = 'test room - short'
        roomObj._desc = 'test room'
        assert roomObj.isValid()

    def displayAndInfo(self, roomObj, loginfo=True):
        ''' test and log a room's description and info '''
        roomDisplay = roomObj.display(self.getCharObj())
        roomInfo = roomObj.getInfo()
        logger.debug("--- start display ---\n" + roomDisplay)
        logger.debug("--- end display ---")
        if loginfo:
            logger.debug("\n" + roomInfo)
        assert roomDisplay != ''
        assert roomInfo != ''

    def testBasics(self):
        ''' load room , verify that room to the south is room 319.  Test a
            variety of other basic room functions '''
        charObj = self.getCharObj()
        roomObj = RoomFactory('room', self._testRoomNum)
        roomObj.load()
        assert roomObj.s == self._testRoomNum2
        roomObj.toggleInstanceDebug()
        assert roomObj.getInstanceDebug()
        roomObj.setInstanceDebug(False)
        assert not roomObj.getInstanceDebug()
        assert roomObj.getType() != ''
        self.displayAndInfo(roomObj, loginfo=False)
        charObj.setPromptSize('brief')
        self.displayAndInfo(roomObj, loginfo=False)
        roomObj._dark = True
        self.displayAndInfo(roomObj, loginfo=False)
        charObj.setDm()
        self.displayAndInfo(roomObj, loginfo=True)
        roomObj._dark = False
        charObj.removeDm()
        assert roomObj.displayExits(charObj) != ''
        assert not roomObj.isSafe()

        # This room has items in it
        roomObj = RoomFactory('room', self._testRoomNum2)
        roomObj.load()
        self.displayAndInfo(roomObj)

        # This room is a shop
        roomObj = RoomFactory('shop', self._testRoomShop)
        roomObj.load()
        self.displayAndInfo(roomObj)

        # This room is a guild
        roomObj = RoomFactory('guild', self._testRoomGuild)
        roomObj.load()
        self.displayAndInfo(roomObj)

    def testCreatureInRoom(self):
        creObj = self.createCreature()

        roomObj = RoomFactory('room', self._testRoomNum)
        roomObj._shortDesc = "in a test room"
        roomObj._desc = 'in a long test room'
        roomObj._encounterList = ['Creature/1']
        roomObj.postLoad()
        roomObj.addToInventory(creObj)
        self.displayAndInfo(roomObj)

    def testRoomVsTarget(self):
        ''' Verify that the target order (i.e. the when interacting with
            objects) is the same as the order of objects in a room '''

        # Create a room
        roomObj = RoomFactory('room', self._testRoomNum)
        roomObj._shortDesc = "in a test room"
        roomObj._desc = 'in a long test room'

        # Create a few portals and add them to room
        for num in range(1, 4):
            obj = self.createObject(num=99990 + num,
                                    type='Portal',
                                    name='portal' + str(num))
            roomObj.addToInventory(obj)

        disp = roomObj.displayItems(self.getCharObj())
        logger.debug("disp: " + str(disp))

        iList = roomObj.getInventory()
        logger.debug("inv: " +
                     str([str(x) + " " + x.describe() for x in iList]))

        tList = [targetSearch(iList, "por #1"),
                 targetSearch(iList, "por #2"),
                 targetSearch(iList, "por #3")]
        logger.debug("tList: " +
                     str([str(x) + " " + x.describe() for x in tList]))

        assert iList == tList

    def testRoomItemSquashing(self):
        ''' Test that identically named items are consolidated when displayed
        '''
        # Create a room
        roomObj = RoomFactory('room', self._testRoomNum)
        roomObj._shortDesc = "in a test room"
        roomObj._desc = 'in a long test room'

        # Create a few similar items and add them to room
        for num in range(1, 4):
            obj = self.createObject(num=99999,
                                    type='Weapon',
                                    name='toothpick')
            roomObj.addToInventory(obj)
        # Create a few similar items and add them to room
        for num in range(1, 3):
            cre = self.createCreature(num=99999,
                                      name='bug')
            roomObj.addToInventory(cre)

        disp = roomObj.displayItems(self.getCharObj())
        logger.debug("disp: " + str(disp))
        assert disp == 'You see three toothpicks and two bugs\n'

    def testRoomLoad(self):
        self.setTestName('testRoomLoad')
        roomNumber = 319
        roomObj = RoomFactory('room', roomNumber)
        roomObj.load()

        # Shop/318 is a shop.  Make sure that we can load it by room number
        shopNumber = 318
        roomObj = RoomFactory('Shop', shopNumber)
        roomObj.load()
        assert roomObj.o == 319
        assert hasattr(roomObj, '_catalog')

        # Shop/317 is a guild.  Make sure that we can load it by room number
        guildNumber = 317
        roomObj = RoomFactory('Guild', guildNumber)
        roomObj.load()
        assert roomObj.o == 319
        assert hasattr(roomObj, '_order')

    def testRoomShop(self):
        tmpRoomNum = 99999
        roomObj = RoomFactory('Shop', tmpRoomNum)  # instanciate room object
        roomObj._catalog = ['Armor/2', 'Weapon/2']
        charObj = self.getCharObj()
        charObj.setName('Lucky')
        charObj.setCoins(10)
        assert roomObj.isVendor()
        assert not roomObj.isRepairShop()
        assert not roomObj.isPawnShop()
        assert not roomObj.isBank()
        assert roomObj.getCatalog() != ''
        assert roomObj.getPriceBonus() == 100
        assert roomObj.getCantAffordTxt() != ''
        assert roomObj.getCantCarryTxt() != ''
        assert roomObj.getSuccessTxt() != ''
        assert roomObj.getAbortedTxt() != ''
        assert roomObj.shopGetInfo() != ''
        assert roomObj.getTaxRate() >= 0
        assert roomObj.getTaxAmount(100) == 0
        assert roomObj.adjustPrice(1000) == 1000
        obj = self.createObject(num=99999, type='Weapon', name='knife')
        logger.debug(roomObj.debug())
        roomObj.recordTransaction(obj, saveRoomFlag=False)
        logger.debug(roomObj.debug())
        assert roomObj.displayTransactions() != ''
        assert not roomObj.displayLedger() != ''
        roomObj._bank = True
        roomObj.recordTransaction('deposit/5000', saveRoomFlag=False)
        assert roomObj.displayLedger() != ''

    def testRoomGuild(self):
        tmpRoomNum = 99999
        roomObj = RoomFactory('Guild', tmpRoomNum)  # instanciate room object
        roomObj._lastTrainees = ['Bob', 'Satish', 'Goldilocks', 'Dom', "Lashi"]
        roomObj._order = 'fighter'
        roomObj._masterLevel = 5
        roomObj._masters = ['Berger']
        charObj = self.getCharObj()
        charObj.setClassName('fighter')
        charObj.setCoins(10)
        charObj.setName('Bingo')
        assert not roomObj.train(charObj)
        assert roomObj.display(charObj) != ''
        assert roomObj.getNotHereTxt() != ''
        assert roomObj.getNotEnoughExpTxt() != ''
        assert roomObj.guildGetInfo() != ''
        assert roomObj.getOrder() != ''
        assert isinstance(roomObj.getLastTrainees(), list)
        assert isinstance(roomObj.getMasters(), list)
        assert roomObj.getMasterLevel() == 5
        assert roomObj.getLastTrainDate() == getNeverDate()
        assert roomObj.isTrainingGround()
        assert roomObj.isTrainingGroundForChar(charObj)
        charObj.setClassName('mage')
        assert not roomObj.isTrainingGroundForChar(charObj)
        assert not roomObj.train(charObj)
        assert roomObj.getCostToTrain(5) == 4096
        assert not roomObj.payToTrain(charObj)
        charObj.setCoins(4096)
        assert roomObj.payToTrain(charObj)
        charObj._expToNextLevel = 10
        assert not roomObj.train(charObj)
        charObj._expToNextLevel = 0
        assert roomObj.train(charObj)
        assert charObj.getLevel() == 2
        assert roomObj.calculateMasterCoinBonus(7) == 49000
        assert self._testAcctName + '/Bingo' in roomObj.getLastTrainees()
        logger.info(roomObj.getPlaqueMsg())
        assert roomObj.getPlaqueMsg() != ''


if __name__ == '__main__':
    unittest.main()
