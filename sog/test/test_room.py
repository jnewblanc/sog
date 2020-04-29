''' test_room '''
import unittest

from common.testLib import InitTestLog
from room import RoomFactory


class TestRoom(unittest.TestCase, InitTestLog):

    num = 9999999

    def testIntAttributes(self):
        roomObj = RoomFactory('room', self.num)
        for oneAtt in roomObj.intAttributes:
            val = getattr(roomObj, oneAtt)
            self.assertEqual(isinstance(val, int), True, oneAtt + " should be a int")  # noqa: E501

    def testBoolAttributes(self):
        roomObj = RoomFactory('room', self.num)
        for oneAtt in roomObj.boolAttributes:
            val = getattr(roomObj, oneAtt)
            self.assertEqual(isinstance(val, bool), True, oneAtt + " should be a bool")  # noqa: E501

    def testStrAttributes(self):
        roomObj = RoomFactory('room', self.num)
        for oneAtt in roomObj.strAttributes:
            val = getattr(roomObj, oneAtt)
            self.assertEqual(isinstance(val, str), True, oneAtt + " should be a str")  # noqa: E501

    def testListAttributes(self):
        roomObj = RoomFactory('room', self.num)
        for oneAtt in roomObj.listAttributes:
            val = getattr(roomObj, oneAtt)
            self.assertEqual(isinstance(val, list), True, oneAtt + " should be a list")  # noqa: E501

    def testisValidPos(self):
        roomObj = RoomFactory('room', self.num)
        roomObj._shortDesc = 'test room - short'
        roomObj._desc = 'test room'
        self.assertEqual(roomObj.isValid(), True, "isValid should return True")  # noqa: E501

    def testisValidNeg(self):
        roomObj = RoomFactory('room', self.num)
        self.assertEqual(roomObj.isValid(), False, "isValid should return False")  # noqa: E501

    def loadRoom1(self):
        ''' load room 1, verify that room to the south is room 2 '''
        roomObj = RoomFactory('room', self.num)
        roomObj._roomself.num = 1
        roomObj.load()
        self.assertEqual(roomObj.s == 2, False, "isValid should return False")  # noqa: E501


if __name__ == '__main__':
    unittest.main()
