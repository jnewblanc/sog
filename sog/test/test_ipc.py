''' test_ipc '''
import unittest

from common.test import TestGameBase
# from common.general import logger


class TestIpc(TestGameBase):

    _testCharName = "testCharIpc"

    def setUp(self):
        super().setUp(__class__.__name__)
        self.getCharObj().setName(self._testCharName)

    def testDoesntCrash(self):
        ''' Pass if these run without crashing, ignore results for now '''
        gameObj = self.getGameObj()
        charObj = self.getCharObj()
        roomObj = self.getRoomObj()

        assert gameObj.directMsg(charObj, 'hello directMsg')
        assert gameObj.charMsg(charObj, 'hello charMsg')
        assert gameObj.roomMsg(roomObj, 'hello roomMsg with dups')
        assert gameObj.roomMsg(roomObj, 'hello roomMsg nodups',
                               allowDupMsgs=False)
        assert gameObj.othersInRoomMsg(charObj, roomObj,
                                       'hello othersInRoomMsg')
        assert gameObj.yellMsg(roomObj, 'hello yellMsg')


if __name__ == '__main__':
    unittest.main()
