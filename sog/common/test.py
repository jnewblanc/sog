''' test harness - common test functions and classes
      * TestGameBase - superClass from which all tests classes should inherit
                       from
      * masterTestNum & incrementTestNum - globals for tracking/incrementing
                       the test numbers
'''
# import doctest
import unittest

import account
import character
import creature
from object import ObjectFactory
from room import RoomFactory
import common.serverLib
from common.general import logger
import threads
from game import GameCmd


class TestGameBase(unittest.TestCase):
    ''' Base class for testing game
        * Sets up commonly used parts of the game so that each test subClass
          doesn't need to do the same thing.
        * Make it easy to create and get handles for the following major class
          types, which start with default values and can then be customized:
          - Client/Account/Game
          - Character
          - Room
          - Creature
          - Objects
    '''
    _testAcctName = "sogTest@example.com"
    _testAcctDisplay = "sogTest"

    _testCharName = 'testCharBase'
    _testCharGender = 'male'
    _testCharClassName = 'fighter'
    _testCharAlignment = 'neutral'

    _testRoomNum = 320
    _testRoomNum2 = 319
    _testRoomShop = 318
    _testRoomGuild = 317

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

    def setTestName(self, name=''):
        if name == '':
            self._testName = __class__.__name__
        else:
            self._testName = name

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

    def createObject(self, num=99999, type='Portal', name='portal'):
        obj = ObjectFactory(type, num)
        if not obj:
            logger.error('Could not instanciate object type ' + type)
        obj._name = name
        obj._article = 'a'
        obj._singledesc = name
        obj._pluraldesc = name + 's'
        obj._longdesc = "A long " + name
        obj._weight = 5
        obj._value = 100
        return(obj)

    def createCreature(self, num=99999, name="bug"):
        cre = creature.Creature(num)
        cre._name = name
        cre._article = 'a'
        cre._singledesc = name
        cre._pluraldesc = name + 's'
        cre._longdesc = "It's a long " + name
        cre._level = 1
        cre._hostile = False
        cre._itemCatalog = ['Armor/1', 'Weapon/1']
        cre._numOfItemsCarried = [1, 2]
        cre.setHitPoints(20)
        cre.autoPopulateInventory()
        cre.setEnterRoomTime()
        assert cre.isValid()
        return(cre)

    def createRoom(self, num=99999):
        room = RoomFactory('room', num)
        room._shortDesc = 'Its a test room - short'
        room._desc = 'Its a test room - long'
        return(room)

    def joinGame(self):
        assert self._client.gameObj.isValid()
        self._client.gameObj.addToActivePlayerList(self.getCharObj())
        self._gameCmdObj = GameCmd(self._client)
    #    self._gameCmdObj.postcmd = [lambda *args: None]

    def joinRoom(self, roomnum=_testRoomNum):
        self._client.gameObj.joinRoom(roomnum, self.getCharObj())
        assert self.getRoomObj().isValid()

    def banner(self, status='start', testName=''):
        if not hasattr(self, "_testName"):
            self.setTestName(testName)
        dashes = "-" * 12
        logger.info(dashes + " " + self._testName + " " +
                    str(masterTestNum) + " " + status + " " + dashes)

    def setUp(self, testName="TestGameBase"):
        self.setTestName(testName)
        self.banner('start')
        self._client = self.createClientAndAccount()
        self._client.charObj = self.createCharacter()
        self.joinGame()
        self._asyncThread = None
        # self.startAsyncThread()
        self.joinRoom()

    def tearDown(self):
        if hasattr(self, '_asyncThread'):
            self.stopAsyncThread()
        self.banner('end')
        incrementTestNum()


# Set masterTestNum if it's not already set
global masterTestNum
try:
    masterTestNum
except NameError:
    masterTestNum = 1


def incrementTestNum():
    global masterTestNum
    masterTestNum += 1
