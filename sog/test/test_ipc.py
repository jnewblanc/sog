''' test_ipc '''
import unittest

from common.test import TestGameBase
# from common.general import logger


class TestIpc(TestGameBase):

    _testCharName = "testCharIpc"

    def setUp(self):
        super().setUp()
        self.getCharObj().setName(self._testCharName)

    def testDoesntCrash(self):
        ''' Pass if these run without crashing, ignore results for now '''
        gameObj = self.getGameObj()
        charObj = self.getCharObj()
        roomObj = self.getRoomObj()

        assert gameObj.directMsg(charObj, 'hello')
        assert gameObj.charMsg(charObj, 'hello')
        assert gameObj.roomMsg(roomObj, 'hello')
        assert gameObj.roomMsg(roomObj, 'hello', allowDupMsgs=False)
        assert gameObj.othersInRoomMsg(charObj, roomObj, 'hello')
        assert gameObj.yellMsg(roomObj, 'hello')


if __name__ == '__main__':
    unittest.main()
