""" test_game """
from collections import namedtuple
import re
import unittest

from common.testLib import TestGameBase
from common.general import logger

# import object
# import room
# import creature
from game import GameCmd


class TestGame(TestGameBase):
    def setTestName(self, name=""):
        self._testName = __class__.__name__

    def testGameInstanciation(self):
        gameObj = self.getGameObj()
        assert gameObj.isValid()
        out = "Could not instanciate the game object"
        self.assertEqual(gameObj._startdate != "", True, out)

    def testToggleInstanceDebug(self):
        gameObj = self.getGameObj()
        startState = gameObj.getInstanceDebug()
        gameObj.toggleInstanceDebug()
        out = "toggleInstanceDebug could not be set"
        self.assertEqual(gameObj.getInstanceDebug() != startState, True, out)
        gameObj.toggleInstanceDebug()
        out = "toggleInstanceDebug could not be set"
        self.assertEqual(gameObj.getInstanceDebug() == startState, True, out)


class TestGameCmd(TestGameBase):
    def multiCharacterSetUp(self, nameList=["char1", "char2"], roomObj=None):
        """ Create X characters and place them in the same room
            Returns a list of nametuples, one element for each character """

        # Create namedtuple and charList for resulting objects
        CharBlob = namedtuple('CharBlob', ['charObj', 'clientObj', 'gameCmdObj'])
        charList = []

        # Create a roomObj for our characters, if it doesn't already exist.
        if not roomObj:
            roomObj = self.createRoom(num=99990)

        for name in nameList:
            if name == nameList[0]:

                # Set up the first character, which is special since the
                # framework creates it for us.
                charObj = self.getCharObj()
                charObj.setName(name)
                clientObj = charObj.client
                gameCmdObj = GameCmd(self.getGameCmdObj())
            else:
                # Create the secondary characters
                clientObj, gameCmdObj = self.createAdditionalClient(name=name)
                charObj = clientObj.charObj

            # Store resulting character, client, and gameCmd objects in list
            # of namedtuples
            C = CharBlob(charObj, clientObj, gameCmdObj)
            charList.append(C)

            # Add the character to the room
            clientObj.getGameObj().joinRoom(roomObj, charObj)

        if len(nameList) > 1:
            logger.debug("multi: Verifying character setup")

            charNamesInGame = self.getCharNamesInGame(charList[0].clientObj.gameObj)
            charNamesInRoom = self.getCharNamesInRoom(charList[0].charObj.getRoom())
            # logger.debug("multi: CharList={}".format(", ".join(charNamesInGame)))

            for oneCharName in nameList:
                # Check that our characters are all currently in the same game
                assert oneCharName in charNamesInGame, (
                    "Character {} is not in the game -- Chars:{}".format(
                        oneCharName, charNamesInGame))
                # Check that our characters are all currently in the same room
                assert oneCharName in charNamesInRoom, (
                    "Character {} is not in the room -- Chars:{}".format(
                        oneCharName, charNamesInRoom))

        return(charList)

    def getCharNamesInRoom(self, roomObj):
        """ Returns a list of character names in the given room """
        return [c.getName() for c in roomObj.getCharacterList()]

    def getCharNamesInGame(self, gameObj):
        return [c.getName() for c in gameObj.getCharacterList()]

    def charIsInRoom(self, charObj, roomObj):
        return charObj in roomObj.getCharacterList()

    def showRoomNumsForAllChars(self):
        """ Dump the list of characters and their room number as debug output """
        outStr = "--- Characters in the Game: "
        outStr += ", ".join(["{0}-->{1}".format(
            c.getName(),
            c.getRoom().getId()) for c in self.getGameObj().getCharacterList()])
        logger.debug(outStr)

    def showOutput(self, prefix, charObj):
        """ Shows the character's output spool as debug log output """
        logStr = "--- {0} {1} - begin output ---\n{2}\n--- {0} {1}- end output ---\n"
        outStr = re.sub("\n", "\n> ", ("> " + charObj.client.popOutSpool().rstrip()))
        logger.debug(logStr.format(prefix, charObj.getName(), outStr))

    def testFollow(self):
        """ Test the lead/follow functionality """
        roomObj = self.createRoom(num=99990)
        roomObj._shortDesc = "room1"
        roomObj.s = "1"
        leadCharName = "Leader"
        parasiteCharName = "Parasite"
        charList = self.multiCharacterSetUp([leadCharName, parasiteCharName],
                                            roomObj)

        leadCharObj = charList[0].charObj
        leadGameCmdObj = charList[0].gameCmdObj
        parasiteCharObj = charList[1].charObj
        parasiteGameCmdObj = charList[1].gameCmdObj

        # Begin tests

        logger.debug("testFollow: Follow case1: invalid target")
        logger.debug("testFollowBad: FollowSettingPre={}".format(
            parasiteCharObj.getFollow()))
        assert not parasiteGameCmdObj.do_follow("does-not-exist")  # always False
        logger.debug(self.showOutput("testFollowBad", parasiteCharObj))
        logger.debug("testFollowBad: FollowSettingPost={}".format(
            parasiteCharObj.getFollow()))
        assert parasiteCharObj.getFollow() is None

        logger.debug("testFollow: Follow case2: invalid self target")
        logger.debug("testFollowBad: FollowSettingPre={}".format(
            parasiteCharObj.getFollow()))
        assert not parasiteGameCmdObj.do_follow(parasiteCharObj.getName())  # always F
        logger.debug(self.showOutput("testFollowBad", parasiteCharObj))
        logger.debug("testFollowBad: FollowSettingPost={}".format(
            parasiteCharObj.getFollow()))
        assert parasiteCharObj.getFollow() is None

        logger.debug("testFollow: Follow case3: valid target")

        logger.debug("testFollowGood: FollowSettingPre={}".format(
            parasiteCharObj.getFollow()))
        assert not parasiteGameCmdObj.do_follow(leadCharObj.getName())  # always False
        logger.debug(self.showOutput("testFollowGood", parasiteCharObj))
        logger.debug("testFollowGood: FollowSettingPost={}".format(
            parasiteCharObj.getFollow()))
        assert parasiteCharObj.getFollow() is leadCharObj

        logger.debug("testFollow: Follow case4: lead moves south")

        self.showRoomNumsForAllChars()
        leadGameCmdObj._lastinput = "s"
        assert not leadGameCmdObj.do_s("")  # always False
        logger.debug(self.showOutput("testFollowGood", leadCharObj))
        logger.debug(self.showOutput("testFollowGood", parasiteCharObj))
        debugInfo = "LeadCharRoom={} - ParasiteCharRoom={}".format(
            leadCharObj.getRoom().getId(), parasiteCharObj.getRoom().getId())
        self.showRoomNumsForAllChars()
        assert self.charIsInRoom(parasiteCharObj, leadCharObj.getRoom()), debugInfo

        logger.debug("testFollow: Follow case5: unfollow")
        assert not parasiteGameCmdObj.do_unfollow("")  # always False
        assert parasiteCharObj.getFollow() is None
        parasitePreRoomObj = parasiteCharObj.getRoom()  # store pre-move roomObj
        assert not leadGameCmdObj.do_s("")  # always False
        assert parasitePreRoomObj is parasiteCharObj.getRoom()  # hasn't moved

    def testLose(self):
        """ Test the lead/follow functionality """
        roomObj = self.createRoom(num=99990)
        leadCharName = "Leader"
        parasiteCharName = "Parasite"
        charList = self.multiCharacterSetUp([leadCharName, parasiteCharName],
                                            roomObj)

        leadCharObj = charList[0].charObj
        leadGameCmdObj = charList[0].gameCmdObj
        parasiteCharObj = charList[1].charObj
        parasiteGameCmdObj = charList[1].gameCmdObj

        # This should already be tested as part of follow
        assert not parasiteGameCmdObj.do_follow(leadCharObj.getName())  # always False
        assert parasiteCharObj.getFollow() is leadCharObj

        # Begin tests
        logger.debug("testLose: Lose case1: valid target")
        assert not leadGameCmdObj.do_lose(parasiteCharObj.getName())  # always False
        assert not parasiteCharObj.getFollow() is leadCharObj
        assert not leadGameCmdObj.do_lose("does-not-exist")
        assert parasiteCharObj.getFollow() is None


if __name__ == "__main__":
    unittest.main()
