''' test_integration '''
import unittest

from common.test import TestGameBase
from common.general import logger


class TestIntegration(TestGameBase):

    debug = False

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().setUp()

    def testTravelSouthAndThroughPortal(self):
        ''' Use known test area which has a room to the south that contains
            a portal back to the start room '''
        startRoom = 320
        southRoom = 319
        portalDestination = startRoom

        gameCmdObj = self.getGameCmdObj()
        if self.debug:
            logger.debug(self.getCharObj().debug())
        # Remember that all game commands return False so that command loop
        # continues
        self.joinRoom(startRoom)
        assert self.getCharObj().getRoom().getId() == startRoom
        assert not gameCmdObj.runcmd('s')
        assert self.getCharObj().getRoom().getId() == southRoom
        assert not gameCmdObj.runcmd('go portal')
        assert self.getCharObj().getRoom().getId() == portalDestination


if __name__ == '__main__':
    unittest.main()
