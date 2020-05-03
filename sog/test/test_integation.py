''' test_integration '''
from mock import patch
import unittest

import account
import character
import common.serverLib
# from common.general import logger
import threads


class TestIntegration(unittest.TestCase):

    _testAcctName = "sogIntTest@gadgetshead.com"
    _testCharName = "intChar1"

    _clientCmds1 = ["info", "who"]
    _clientCmdCounter = 0
    _lastOutput = ''

    def initClientThread(self, clientObj):
        ''' This method is passed in to ClientThread as a callback function,
            as part of startThreads.  It is used to spoof/bypass the
            account login '''
        self.acctObj = account.Account(client=clientObj)
        self.acctObj.email = self._testAcctName
        self.acctObj.password = "test"
        self.acctObj._displayName = "TestAccount1"

    def spoofSendRecieve(self):
        # get client commands via a list with an incrementer
        if self._clientCmdCounter < len(self._clientCmds1):
            cmd = self._clientCmds1[self._clientCmdCounter]
        else:
            cmd = 'exit'
        self._clientCmdCounter += 1

        # Simulate client sending command to the server
#        self._clientThread.setInputStr(cmd)

        # capture the output as if consumed by the client
        self.lastOutput = self._clientThread.popOutSpool()

    def startThreads(self):
        # mock_socket = Mock(name='socket')
        mock_socket = None
        self._clientThread = threads.ClientThread(mock_socket, "fakeadd",
                                                  "fakeid",
                                                  self.initClientThread)
        self._clientThread.start()

        self._asyncThread = common.serverLib.createAndStartAsyncThread()

    def createAcct1(self):
        self._acctObj = account.Account(client=self._clientThread)
        self._acctObj.email = self._testAcctName
        self._acctObj.password = "test"
        self._acctObj._displayName = "TestAccount1"
        self._acctObj.characterList = [self._testCharName]
        self._acctObj.save()

    def createChar1(self):
        self._charObj = character.Character(client=self._clientThread,
                                            acctName=self._testAcctName)
        # Add stats
        self._charObj.initializeStats(10)
        self._charObj.setMaxHP(100)
        self._charObj.create(charName=self._testCharName, promptFlag=False)
        self._charObj.setHitPoints(100)

    def XsetUp(self):
        self._patchObj = patch.object(threads.ClientThread, '_sendAndReceive',
                                      side_effect=self.spoofSendRecieve)
        self._mockObj = self._patchObj.start()

        self.startThreads()

        self.createAcct1()
        self._clientThread.acctObj = self._acctObj
        assert self._clientThread.acctObj.isValid()

        self.createChar1()
        self._clientThread.charObj = self._charObj
        self._clientThread.charObj.isValid()

    def XtearDown(self):
        common.serverLib.haltAsyncThread(self._clientThread.gameObj,
                                         self._asyncThread)
        common.serverLib.haltClientThreads()

        self._patchObj.stop()

    def XtestSpinUp(self):
        assert self._clientThread
        assert self._clientThread._startdate
        assert self._clientThread.gameObj
        assert self._clientThread.lobbyObj
        assert self._asyncThread._startdate
        assert self._clientThread.gameObj._startdate
        assert self._asyncThread.gameObj._startdate
        pass

    def testSomething(self):
        # assert self._clientThread.spoolOut("test")
        # assert self._clientThread._sendAndReceive()
        # assert self._clientThread.promptForInput("Enter Something")
        # client.gameObj.joinGame(client)
        # out = "Could not joinGame"
        # self.assertEqual(client.charObj.getRoom().getId() == '1', True, out)
        pass


if __name__ == '__main__':
    unittest.main()
