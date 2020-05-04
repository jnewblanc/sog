''' common test finctions and classes '''
import unittest

import account
import character
import common.serverLib
# from common.general import logger
import threads
from game import GameCmd


class TestGameBase(unittest.TestCase):
    ''' Base class for testing game
        * Sets up commonly used parts of the game so that each test subClass
          doesn't need to do the same thing.
        * Set up Account, Character, Game, Room with defaults
    '''
    _testAcctName = "sogTest@gadgetshead.com"
    _testAcctDisplay = "sogTest"

    _testCharName = 'testChar3'
    _testCharGender = 'male'
    _testCharClassName = 'fighter'
    _testCharAlignment = 'neutral'

    _testRoomNum = 320

    def getClientObj(self):
        return(self._client)

    def getCharObj(self):
        return(self.getClientObj().charObj)

    def getRoomObj(self):
        return(self.getCharObj().getRoom())

    def getGameObj(self):
        return(self.getClientObj().gameObj)

    def getGameCmdObj(self):
        return(self._gameCmdObj)

    def getAcctObj(self):
        return(self.getClientObj().acctObj)

    def getAsyncThread(self):
        return(self._asyncThread)

    def startAsyncThread(self):
        self._asyncThread = common.serverLib.createAndStartAsyncThread()

    def stopAsyncThread(self):
        common.serverLib.haltAsyncThread(self.getGameObj(),
                                         self.getAsyncThread())

    def createClientAndAccount(self):
        client = threads.ClientBase()
        client.acctObj = account.Account(self)
        client.acctObj.setUserEmailAddress(self._testAcctName)
        client.acctObj.setDisplayName(self._testAcctDisplay)
        assert client.acctObj.isValid()
        return(client)

    def createCharacter(self,
                        name=_testCharName,
                        gender=_testCharGender,
                        cname=_testCharClassName,
                        align=_testCharAlignment):

        charObj = character.Character(client=self.getClientObj(),
                                      acctName=self.getAcctObj().getId())
        charObj.setName(name)
        charObj.setGender(gender)
        charObj.setClassName(cname)
        charObj.setAlignment(align)
        assert charObj.isValid()
        return(charObj)

    def joinGame(self):
        assert self._client.gameObj.isValid()
        self._client.gameObj.addToActivePlayerList(self.getCharObj())
        self._gameCmdObj = GameCmd(self._client)

    def joinRoom(self, roomnum=_testRoomNum):
        self._client.gameObj.joinRoom(roomnum, self.getCharObj())
        assert self.getRoomObj().isValid()

    def setUp(self):
        self._client = self.createClientAndAccount()
        self._client.charObj = self.createCharacter()
        self.joinGame()
        self._asyncThread = None
        # self.startAsyncThread()
        self.joinRoom()

    def tearDown(self):
        self._client.gameObj.leaveRoom(self.getCharObj())
        if self.getAsyncThread():
            self.stopAsyncThread()
