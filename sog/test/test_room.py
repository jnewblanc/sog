''' test_room '''
import unittest

from common.test import TestGameBase
from common.general import logger
import creature
from room import RoomFactory


class TestRoom(TestGameBase):

    num = 99999

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
        creObj = creature.Creature(99999)
        creObj._name = 'bug'
        creObj._article = 'a'
        creObj._pluraldesc = 'potato bugs'
        creObj._singledesc = 'potato bug'
        creObj._longdesc = "potato bugs don't taste like potatoes"
        creObj._level = '1'

        roomObj = RoomFactory('room', self._testRoomNum)
        roomObj._shortDesc = "in a test room"
        roomObj._desc = 'in a long test room'
        roomObj._encounterList = ['Creature/1']
        roomObj.postLoad()
        roomObj.addToInventory(creObj)
        self.displayAndInfo(roomObj)


if __name__ == '__main__':
    unittest.main()
