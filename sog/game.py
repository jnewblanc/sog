""" game class """  # noqa

# We want only one implementation of the Game Class.
# To do this, create a single instance of the Game class on import.  Then
# each time we try to instanciate Game(), we just return a reference to
# the game class.

import cmd
from datetime import datetime
import pprint
import random
import re

from combat import Combat
from common.ipc import Ipc
from common.general import isIntStr, dateStr, logger, dLog
from common.general import splitTargets, targetSearch, itemSort
from common.general import getRandomItemFromList, secsSinceDate, getNeverDate
from common.globals import maxCreaturesInRoom
from common.help import enterHelp
from magic import Spell, SpellList, spellCanTargetSelf
from room import RoomFactory, isRoomFactoryType, getRoomTypeFromFile
from object import ObjectFactory, isObjectFactoryType
from creature import Creature


class _Game(cmd.Cmd, Combat, Ipc):
    """ Single instance of the Game class, shared by all users
        (see instanciation magic at the bottom of the file)"""

    _instanceDebug = False

    def __init__(self):
        """ game-wide attributes """
        self.instance = "Instance at %d" % self.__hash__()
        self._activeRooms = []
        self._activePlayers = []
        self._startdate = datetime.now()

        self._instanceDebug = _Game._instanceDebug
        return None

    def debug(self):
        return pprint.pformat(vars(self))

    def toggleInstanceDebug(self):
        self._instanceDebug = not self._instanceDebug

    def getInstanceDebug(self):
        return self._instanceDebug

    def getId(self):
        return self.instance

    def isValid(self):
        if self.getId() != "" and self._startdate < datetime.now():
            return True
        return False

    def asyncTasks(self):
        """ Tasks that run in a separate thread with ~1 sec intervals """
        self.asyncNonPlayerActions()
        self.asyncCharacterActions()

    def joinGame(self, client):
        """ Perform required actions related to joining the game """
        charObj = client.charObj
        if not charObj:
            logger.warn("Game: Character not defined - returning False")
            return False

        gameCmd = GameCmd(client)  # each user gets their own cmd shell

        self.addToActivePlayerList(charObj)

        # in-game broadcast announcing game entry
        msg = client.txtBanner(
            "{} has entered the game at {}".format(charObj.getName(),
                                                   dateStr("now")), bChar="=")
        self.gameMsg(msg + "\n")
        logger.info("JOINED GAME " + charObj.getId())

        # add room to charObj and then display the room
        if self.joinRoom(1, charObj):
            self.charMsg(charObj, charObj.getRoom().display(charObj))
            try:
                gameCmd.cmdloop()  # start the game cmdloop
            finally:
                if client.charObj:
                    self.leaveGame(client)
        return False

    def leaveGame(self, client, saveChar=True):
        """ Handle details of leaving a game """
        charObj = client.charObj

        self.leaveRoom(charObj)

        # remove character from game character list
        self.removeFromActivePlayerList(charObj)

        # final character save before throwing away charObj
        if saveChar:
            # saveChar is False when it's a suicide
            charObj.save(logStr=__class__.__name__)

        # notification and logging
        msg = client.txtBanner(
            "{} has left the game at {}".format(charObj.getName(), dateStr("now")),
            bChar="=")
        self.gameMsg(msg + "\n")
        client.spoolOut(msg + "\n")

        logger.info("LEFT GAME " + charObj.getId())

        # Discard charObj
        charObj = None
        client.charObj = None
        return True

    def getCharacterList(self):
        return self._activePlayers

    def addToActivePlayerList(self, charObj):
        """ add character to list of characters in game """
        if charObj not in self.getCharacterList():
            self._activePlayers.append(charObj)

    def removeFromActivePlayerList(self, charObj):
        """ remove character from list of characters in game """
        if charObj in self.getCharacterList():
            self._activePlayers.remove(charObj)

    def getActiveRoomList(self):
        return self._activeRooms

    def addToActiveRooms(self, roomObj):
        """ Add room to active room list """
        if roomObj not in self.getActiveRoomList():
            self._activeRooms.append(roomObj)
        return True

    def removeFromActiveRooms(self, roomObj):
        """ Remove room from active room list """
        if self.isActiveRoom(roomObj):
            self._activeRooms.remove(roomObj)
        return True

    def isActiveRoom(self, roomObj):
        """ Return true if room is in active room list """
        if roomObj in self.getActiveRoomList():
            return True
        return False

    def getActiveRoom(self, num):
        """ Return the roomObj for an active room, given the room number """
        for roomObj in self.getActiveRoomList():
            if roomObj.getId() == num:
                return roomObj
        return None

    def activeRoomInfo(self):
        msg = "Active rooms: " + ", ".join(
            [x.getItemId() + "(" + str(x) + ")" for x in self.getActiveRoomList()]
        )
        return msg

    def deActivateEmptyRoom(self, roomObj):
        """ deactiveates room if empty.  Returns true if deactiveated """
        if len(roomObj.getCharacterList()) == 0:
            self.removeFromActiveRooms(roomObj)
            return True
        return False

    def asyncCharacterActions(self):
        """ asyncronous actions that occur to players. """
        for charObj in self.getCharacterList():
            self.timeoutInactivePlayers(charObj)
            charObj.processPoisonAndRegen()

    def timeoutInactivePlayers(self, charObj, timeoutInSecs=30):
        """ kick character out of game if they have been inactive """
        timeOutTxt = "You have timed out due to inactivity\n"
        if charObj.getInputDate() == getNeverDate():
            # Ignore the timeout check if the input date has not been set yet
            # This is a timing issue in that the first run of the async loop
            # runs before the character is fully initialized with an input date.
            return(False)
        if secsSinceDate(charObj.getInputDate()) > timeoutInSecs:
            # kick character out of game
            self.charMsg(charObj, timeOutTxt)
            logger.info("GAME TIMEOUT {}".format(charObj.getId()))
            self.leaveGame(charObj.client, saveChar=True)
            return(True)

        return(False)

    def asyncNonPlayerActions(self):
        """ asyncronous actions that are not tied to a player. """
        for roomObj in self.getActiveRoomList():
            if self.deActivateEmptyRoom(roomObj):
                continue
            self.creatureEncounter(roomObj)
            self.creaturesAttack(roomObj)
        return None

    def roomLoader(self, roomStr):
        """ returns a roomObj, given a roomStr """
        logPrefix = "game.roomLoader (" + str(roomStr) + ")"
        roomObj = None
        roomType = "room"
        roomNum = 0

        roomStr = str(roomStr)
        if isIntStr(roomStr):
            roomNum = int(roomStr)
            roomType = getRoomTypeFromFile(roomNum)
        elif "/" in roomStr:
            # if it's not a number, assume it's in the form: Room/35
            roomType, roomNum = roomStr.split("/")

        if isIntStr(roomNum):
            roomNum = int(roomNum)
            if roomNum == 0:
                logger.error(logPrefix + "Room number is 0")
                return None
        else:
            logger.error(logPrefix + "Room number is invalid")
            return None

        # See if room is already active
        for oneroom in self.getActiveRoomList():
            if oneroom.getRoomNum() == roomNum:  # if the room alread exists
                roomObj = oneroom  # use existing roomObj

        if not roomObj:
            roomObj = RoomFactory(roomType, roomNum)  # instanciate room object
            roomObj.load(logStr=__class__.__name__)  # load room from disk

        if roomObj is None:
            logger.error(logPrefix + "Room object is None")

        return roomObj
        # end roomLoader

    def joinRoom(self, roomThing, charObj):
        """ insert player into a room
            * can accept room number or roomObj
            * create or join room instance
            * add character to room instance
            * add room to character instance
            * add room to active rooms list
            * close spring loaded doors if room is empty
            # roomStr can be a room number or can be in the form Shop/35
        """
        roomObj = None
        if isinstance(roomThing, int) or isinstance(roomThing, str):
            roomObj = self.roomLoader(roomThing)
        elif isRoomFactoryType(roomThing.getType()):
            roomObj = roomThing

        if not roomObj:
            logger.error("joinRoom: Could not get roomObj")
            return False

        existingRoom = charObj.getRoom()
        if existingRoom:
            if existingRoom == roomObj:  # if already in desired room
                return True  # do nothing
            else:
                self.leaveRoom(charObj)  # leave the previous room

        charObj.setRoom(roomObj)  # Add room to character
        roomObj.addCharacter(charObj)  # Add character to room
        self.addToActiveRooms(roomObj)  # Add room to active room list
        return True

    def leaveRoom(self, charObj):
        """ Handle details of leaving a room
            * Remove room from active rooms list if it's empty
            * remove character from room instance
            * remove room from character instance
            * toDo - check if other players/creatures follow
            * toDo - notify others that character has left the room
            * toDo - stop/reassign attackers
        """

        if not charObj:
            return False
        if not charObj.getRoom():  # There is no previous room, so just return
            return True
        if charObj.getRoom().getId() == 0:  # Not a real room - just loaded?
            return True

        charObj.getRoom().removeCharacter(charObj)  # remove charact from room
        # if room's character list is empty, remove room from activeRoomList
        if len(charObj.getRoom().getCharacterList()) == 0:
            self.removeFromActiveRooms(charObj.getRoom())
            charObj.getRoom().removeNonPermanents(removeTmpPermFlag=False)
        charObj.getRoom().save()
        charObj.removeRoom()  # Remove room from character
        return True

    def calculateObjectPrice(self, charObj, obj):
        """ return adjusted price for an object based on many factors """
        if obj.isCursed():
            return 1

        price = obj.getValue()
        price = obj.adjustPrice(price)  # object adjustment
        price = charObj.getRoom().adjustPrice(price)  # room adjustment
        price = charObj.adjustPrice(price)  # char adjust
        return price

    def getCorrespondingRoomObj(self, doorObj, activeOnly=False):
        """ Get the room object that correcponds to a door """
        roomObj = self.getActiveRoom(doorObj.getToWhere())
        if not roomObj:  # If active room doesn't exist
            if not activeOnly:
                # Load room from disk into separate instance
                roomObj = self.roomLoader(doorObj.getToWhere())
            else:
                roomObj = None
        return roomObj

    def modifyCorrespondingDoor(self, doorObj, charObj):
        """ When a door is opened/closed on one side, the corresponing door
            needs to be updated """

        roomObj = self.getCorrespondingRoomObj(doorObj)

        if roomObj:
            for obj in roomObj.getInventory():
                if obj.getId() == doorObj.getCorresspondingDoorId():
                    if doorObj.isClosed():
                        obj.close(charObj)
                    else:
                        obj.open(charObj)
                    if doorObj.isLocked():
                        obj.lock()
                    else:
                        obj.unlock()
                    roomObj.save()
            return True
        return True

    def buyTransaction(
        self, charObj, obj, price, prompt, successTxt="Ok.", abortTxt="Ok."
    ):
        """ buy an item """
        roomObj = charObj.getRoom()

        if charObj.client.promptForYN(prompt):
            charObj.subtractCoins(price)  # tax included
            charObj.addToInventory(obj)  # add item
            if roomObj.getType() == "Shop":
                roomObj.recordTransaction(obj)  # update stats
                roomObj.recordTransaction("sale/" + str(price))
                charObj.recordTax(roomObj.getTaxAmount(price))
            self.charMsg(charObj, successTxt)
            logger.info(
                "PURCHASE "
                + charObj.getId()
                + " bought "
                + obj.describe()
                + " for "
                + str(price)
            )
            return True
        else:
            self.charMsg(charObj, abortTxt)
        return False

    def sellTransaction(
        self, charObj, obj, price, prompt, successTxt="Ok.", abortTxt="Ok."
    ):
        """ sell an item """
        roomObj = charObj.getRoom()

        if charObj.client.promptForYN(prompt):
            charObj.removeFromInventory(obj)  # remove item
            charObj.addCoins(price)  # tax included
            if roomObj.getType() == "Shop":
                roomObj.recordTransaction(obj)  # update stats
                roomObj.recordTransaction("purchase/" + str(price))
                charObj.recordTax(roomObj.getTaxAmount(price))
            self.charMsg(charObj, successTxt)
            logger.info(
                "SALE "
                + charObj.getId()
                + " sold "
                + obj.describe()
                + " for "
                + str(price)
            )

            return True
        else:
            self.charMsg(charObj, abortTxt)
            return False

    def populateRoomCreatureCache(self, roomObj):
        """ Create a creature cache, so that we don't have to load the
            creatures every time we check for encounters.  These creatures are
            never actually encountered.  They just exist for reference
        """
        debugPrefix = "game.populateRoomCreatureCache (" + str(roomObj.getId()) + "): "
        if len(roomObj.getCreatureCache()) == 0:
            dLog(debugPrefix + "Populating room creature cache", self._instanceDebug)
            # loop through all possible creatures for room and fill cache
            for ccNum in roomObj.getEncounterList():
                ccObj = Creature(ccNum)
                ccObj.load()
                roomObj.creatureCachePush(ccObj)
                dLog(debugPrefix + "Cached " + ccObj.describe(), self._instanceDebug)

    def getEligibleCreatureList(self, roomObj):
        """ Determine which creatures, from the cache, can be encountered, by
            comparing their frequency attribute to a random roll.  Fill a
           eligibleCreatureList with possible creatures for encounter. """
        debugPrefix = "game.getEligibleCreatureList (" + str(roomObj.getId()) + "): "
        eligibleCreatureList = []
        for ccObj in roomObj.getCreatureCache():
            if ccObj.getFrequency() >= random.randint(1, 100):
                # Load creature to be encountered
                cObj = Creature(ccObj.getId())
                cObj.load()
                eligibleCreatureList.append(cObj)
                dLog(
                    debugPrefix + cObj.describe() + " is eligible", self._instanceDebug
                )
        return eligibleCreatureList

    def creatureEncounter(self, roomObj):
        """ As an encounter, add creature to room
            Chance based on
              * room encounter rates and encounter list
              * creature frequency
        """
        debugPrefix = "Game creatureEncounter (" + str(roomObj.getId()) + "): "
        if not roomObj.readyForEncounter():
            # dLog(debugPrefix + 'Room not ready for encounter',
            #      self._instanceDebug)
            return False

        if len(roomObj.getInventoryByType("Creature")) >= maxCreaturesInRoom:
            self.roomMsg(
                roomObj, "Others arrive, but wander off.\n", allowDupMsgs=False
            )
            return False

        self.populateRoomCreatureCache(roomObj)
        eligibleCreatureList = self.getEligibleCreatureList(roomObj)

        creatureObj = getRandomItemFromList(eligibleCreatureList)
        if creatureObj:
            roomObj.addToInventory(creatureObj)
            dLog(
                debugPrefix + str(creatureObj.describe()) + " added to room",
                self._instanceDebug,
            )
            self.roomMsg(roomObj, creatureObj.describe() + " has arrived\n")
            creatureObj.setEnterRoomTime()
            roomObj.setLastEncounter()
        return None

    def removeFromPlayerInventory(self, charObj, item, msg=""):
        """ display message and remove item from player's inventory
            * Has some canned responses, such as "disintegrate"     """
        if msg == "disint":
            msg = item.describe(article="The") + " disintegrates"

        if msg != "":
            self.charMsg(charObj, msg + "\n")

        # Remove item from player's inventory
        charObj.removeFromInventory(item)
        return None


class GameCmd(cmd.Cmd):
    """ Game loop - separate one for each player
        * Uses cmd loop with do_<action> methods
        * if do_ methods return True, then loop exits
    """

    def __init__(self, client=None):
        self.client = client
        if client:
            self.acctObj = client.acctObj
            self.gameObj = client.gameObj
            self.charObj = client.charObj
        else:
            self.acctObj = None
            self.gameObj = None
            self.charObj = None

        self._lastinput = ""
        self._instanceDebug = False

    def toggleInstanceDebug(self):
        self._instanceDebug = not self._instanceDebug

    def setInstanceDebug(self, val):
        self._instanceDebug = bool(val)

    def getInstanceDebug(self):
        return self._instanceDebug

    def getCmdPrompt(self):
        sp = "<"
        ep = ">"
        if self.charObj:
            promptsize = self.charObj.getPromptSize()
        else:
            promptsize = "full"

        if promptsize == "brief":
            promptStr = ep + " "
        else:
            promptStr = sp + "game" + ep + " "
        return promptStr

    def cmdloop(self):
        """ cmd method override - Game loop
            requires player to have character loaded """
        stop = False
        line = ""
        self.preloop()
        while not stop:
            if self.client.promptForCommand(self.getCmdPrompt()):  # send/recv
                line = self.client.getInputStr()
                stop = self.runcmd(line)
            else:
                stop = True
        self.postloop()

    def runcmd(self, cmd):
        """ workhorse of cmdloop
            * runcmd extracted from cmdloop so that tests can call it without
              prompting for input
        """
        self._lastinput = cmd
        dLog("GAME cmd = " + cmd, self._instanceDebug)
        if self.precmd() == "stop":
            return True
        stop = self.onecmd(cmd)
        if self.postcmd(cmd) == "stop":
            return True
        return stop

    def preloop(self):
        """ functionality that get run once before the input loop begins """
        # Set the input date when first entering the game.  Required for timeout
        # to work properly on characters that never input a command.
        self.charObj.setInputDate()

    def precmd(self):
        """ cmd method override """
        # If charater has timed out or been booted from the game
        # terminate the command loop.
        if self.charObj not in self.gameObj.getCharacterList():
            return("stop")
        self.charObj.setInputDate()
        if self.lastcmd != "":
            self.charObj.setLastCmd(self.lastcmd)
        return(False)

    def postcmd(self, line):
        """ cmd method override """
        if self.charObj:  # doesn't exist if there is a suicide
            self.charObj.save(logStr=__class__.__name__)
        return(False)

    def emptyline(self):
        """ cmd method override """
        return False

    def default(self, line):
        """ cmd method override """
        logger.warn("*** Invalid game command: %s\n" % line)
        self.charObj.client.spoolOut("Invalid Command\n")

    def getLastCmd(self):
        """ Returns the first part of the last command """
        return self.lastcmd.split(" ", 1)[0]

    def missingArgFailure(self):
        """ Print missing arg message and return False """
        self.selfMsg(self.getLastCmd() + " what?\n")
        return False

    def getObjFromCmd(self, itemList, cmdline):
        """ Returns a list of target Items, given the full cmdargs """
        targetItems = []
        for target in splitTargets(cmdline):
            obj = targetSearch(itemList, target)
            if obj:
                targetItems.append(obj)
        targetItems += [None] * 2  # Add two None items to the list
        return targetItems

    def getCombatTarget(self, line):
        """ All combat commands need to determine the target """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        creatureList = roomObj.getInventoryByType("Creature")
        targetList = self.getObjFromCmd(creatureList, line)
        target = targetList[0]

        if not target:
            # Re-use old target if it still exists
            lastTarget = charObj.getCurrentlyAttacking()
            if lastTarget:
                if lastTarget in creatureList:
                    target = lastTarget

        if not target:
            if line == "":
                self.selfMsg("No target.\n")
            else:
                self.selfMsg(line + " is not a valid target.\n")

            return None

        return target

    def parseSpellArgs(self, line):
        charObj = self.charObj
        roomObj = charObj.getRoom()

        charObjList = charObj.getInventory()
        roomInv = roomObj.getCharsAndInventory()
        targetList = self.getObjFromCmd(charObjList + roomInv, line)

        spellItem = None
        spellName = ""
        targetObj = None

        if self.getLastCmd() == "cast":
            # When casting a spell, there is no spellItem, so the first item
            # in the list is the target
            if len(targetList) >= 1:
                targetObj = targetList[0]
            spellName = line.split(" ", 1)[0]
        else:
            # When using a magic item, the first magic item encountered is the
            # spellItem and the next, if any, is the target
            for target in targetList:
                if not target:
                    continue
                if not target.isMagicItem():
                    continue
                if not spellItem:
                    spellItem = target
                if not targetObj:
                    targetObj = target
                break

            if spellItem:
                spellName = spellItem.getSpellName()

        if spellName != "":
            if not targetObj and spellCanTargetSelf(spellName):
                targetObj = charObj

        return (spellItem, spellName, targetObj)

    def selfMsg(self, msg):
        """ send message using Game communnication.  This simply allows us
            to call it without passing the extra arg) """
        return self.gameObj.charMsg(self.charObj, msg)

    def othersMsg(self, roomObj, msg, ignore):
        """ send message using Game communnication.  This simply allows us
            to call it without passing the extra arg) """
        return self.gameObj.othersInRoomMsg(self.charObj, roomObj, msg, ignore)

    def moveDirection(self, charObj, direction):
        """ move subcommand - move in one of the the basic directions """
        dLog("GAME move dir = " + direction, self._instanceDebug)

        exitDict = charObj.getRoom().getExits()

        if direction not in exitDict.keys():
            self.selfMsg("You can't move in that direction!\n")
            return False

        destRoomNum = exitDict[direction]
        roomObj = self.gameObj.roomLoader(destRoomNum)

        if not roomObj:
            logger.error("Could not create roomObj " + str(destRoomNum) + ".")
            return False

        if not roomObj.canBeJoined(charObj):
            logger.error(roomObj.getId() + " can not be joined.")
            return False

        if self.gameObj.joinRoom(roomObj, charObj):
            return True
        else:
            logger.error("joinRoom Failed\n")
            return False
        return False

    def moveThroughPortalOrDoor(self, charObj, itemObj):
        """ move subcommand - move through door or portal """
        if not itemObj:  # no object - take no action
            self.selfMsg("That is not somewhere you can go!\n")
            return False

        if not itemObj.canBeEntered(charObj):
            self.selfMsg("You can't go there!\n")
            return False

        if itemObj.hasToll():
            toll = itemObj.getToll()
            if charObj.canAffordAmount(toll):
                charObj.subtractCoins(toll)
                self.selfMsg("You paid a toll of {} coins.".format(toll))
            else:
                self.selfMsg("Opening this item requires more coins than you have\n")
                return False

        dLog(
            "GAME move through obj = {}".format(itemObj.describe()), self._instanceDebug
        )

        roomnum = itemObj.getToWhere()
        roomObj = self.gameObj.roomLoader(roomnum)
        if roomObj:
            if roomObj.canBeJoined(charObj):
                if self.gameObj.joinRoom(roomnum, charObj):
                    return True
                else:
                    logger.error("joinRoom Failed\n")
            else:
                logger.error(roomnum + " can not be joined")
        else:
            logger.error("Could not create roomObj " + roomnum)
        return False

    def move(self, line):
        """ move character from one room to another """
        cmdargs = line.split(" ")
        charObj = self.charObj
        moved = False
        currentRoom = charObj.getRoom()
        oldRoom = charObj.getRoom()
        if currentRoom.isDirection(cmdargs[0]):  # if command is a direction
            moved = self.moveDirection(charObj, cmdargs[0])
        else:
            # handle doors and Portals
            itemList = self.getObjFromCmd(currentRoom.getInventory(), line)

            moved = self.moveThroughPortalOrDoor(charObj, itemList[0])

        currentRoom = charObj.getRoom()

        if moved:
            # creatures in old room should stop attacking player
            self.gameObj.unAttack(oldRoom, charObj)
            # character possibly loses hidden
            charObj.possibilyLoseHiddenWhenMoving()
            self.selfMsg(charObj.getRoom().display(charObj))
            return True
        else:
            self.selfMsg("You can not go there!\n")
        return False

    def useObject(self, obj, line):
        """ Call method for using object, based on it's type/attributes """
        if not obj:
            logger.error("game.useObject: Could not use a non-existent obj")
            return False

        if not isObjectFactoryType(obj.getType()):
            logger.error("game.useObject: Could not use a non-obj obj")
            return False

        if not obj.isUsable():
            self.selfMsg(obj.describe(article="The") + "is not usable\n")

        if obj.isEquippable():
            if self.charObj.equip(obj):
                self.selfMsg("Ok\n")
            else:
                self.selfMsg("You can't equip that\n")
        elif obj.isMagicItem():
            self.useMagicItem(line)

    def useMagicItem(self, line):
        if line == "":
            return self.missingArgFailure()

        (spellItem, spellName, targetObj) = self.parseSpellArgs(line)

        if not spellItem:
            return self.missingArgFailure()

        if not targetObj:
            self.selfMsg("Invalid target for spell." + spellName + "\n")
            return False

        if spellItem.getType().lower() == "scroll":
            spellItem.readScroll(self.charObj, targetObj)
            # Note: A read scroll will already display the distintegrates
            # message via the item's cast method.  Don't add it here.
            self.gameObj.removeFromPlayerInventory(self.charObj, spellItem)
        else:
            spellItem.cast(self.charObj, targetObj)
        return None

    def parseIpc(self, line):
        roomObj = self.charObj.getRoom()

        lastCmd = self.getLastCmd()
        target = None
        msg = ""

        # Get recipient, if any
        possibleRecipients = []
        if lastCmd == "whisper":
            possibleRecipients = roomObj.getCharacterList()
        elif lastCmd == "send":
            possibleRecipients = self.gameObj.getCharacterList()
        # elif lastCmd in ['say', 'yell', 'shout', 'broadcast']:
        #     target = None

        if len(possibleRecipients) > 0:
            targetList = self.getObjFromCmd(possibleRecipients, line)
            if targetList[0]:
                target = targetList[0]

                if re.search("[^ ]+ [^ ]+", line):
                    # todo: fix this if target is more than one word.
                    #       i.e. Player #1.
                    junk, msg = line.split(" ", 1)

        if msg == "":
            msg = self.client.promptForInput(lastCmd + " what? ")

        return (target, msg)

    def do_accept(self, line):
        """ transaction - accept an offer """
        self.selfMsg(line + " not implemented yet\n")

    def do_action(self, line):
        """ communication - fun in-room communication """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if line == "":
            self.selfMsg("Usage: action <txt>\n")
            return False

        msg = charObj.getName() + " " + line
        self.gameObj.roomMsg(roomObj, msg + "\n")
        logger.info(msg)
        charObj.setHidden(False)

    def do_appeal(self, line):
        """ ask DMs for help """
        self.selfMsg(line + " not implemented yet\n")

    def do_att(self, line):
        """ combat - alias """
        return self.do_attack(line)

    def do_attack(self, line):
        """ combat """
        target = self.getCombatTarget(line)
        if not target:
            self.selfMsg("Attack what?\n")
            return False

        self.gameObj.attackCreature(self.charObj, target, self.getLastCmd())
        return False

    def do_auction(self, line):
        """ alias - sell """
        return self.do_sell(list)

    def do_backstab(self, line):
        """ combat """

        # monster gets double damage on next attack

        target = self.getCombatTarget(line)
        if not target:
            self.selfMsg("Backstab what?\n")
            return False

        self.gameObj.attackCreature(self.charObj, target, self.getLastCmd())
        return False

    def do_balance(self, line):
        """ info - view bank balance when in a bank """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == "Shop":
            self.selfMsg("You can't do that here.  Find a bank\n")
            return False
        if not roomObj.isBank():
            self.selfMsg("You can't do that here.  Find a bank.\n")
            return False

        amount = charObj.getBankBalance()
        self.selfMsg("Your account balance is " + str(amount) + " shillings.\n")

    def do_block(self, line):
        """ combat """
        target = self.getCombatTarget(line)
        if not target:
            self.selfMsg("Block what?\n")
            return False

        self.gameObj.attackCreature(self.charObj, target, self.getLastCmd())
        return False

    def do_break(self, line):
        """ alias - smash """
        return self.do_smash(line)

    def do_bribe(self, line):
        """ transaction - bribe a creature to vanish """
        cmdargs = line.split(" ")
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if len(cmdargs) < 2:
            self.selfMsg("Try 'bribe <creature> <amount>'\n")
            return False
        if not isIntStr(cmdargs[1]):
            self.selfMsg("How many shillings are you trying to bribe with?'\n")
            return False

        creatureName = cmdargs[0]
        coins = int(cmdargs[1])

        roomCreatureList = roomObj.getCreatureList()
        itemList = self.getObjFromCmd(roomCreatureList, creatureName)

        if not itemList[0]:
            self.selfMsg("Who are you trying to bribe?\n")
            return False

        creatureObj = itemList[0]
        if creatureObj:
            if creatureObj.acceptsBribe(charObj, coins):
                # Bribe succeeds - money is already subtracted
                self.selfMsg(
                    creatureObj.describe(article="The")
                    + " accepts your offer and leaves\n"
                )
                roomObj.removeFromInventory(creatureObj)
                return False
            else:
                # Bribe failed - contextual response already provided
                charObj.setHidden(False)
        return False

    def do_brief(self, line):
        """ set the prompt and room description to least verbosity """
        self.charObj.setPromptSize("brief")

    def do_broadcast(self, line):
        """ communication - send to everyone in the game
            * players are limited to X broadcasts per day (currently 5)
            * log broadcasted messages, in case of abuse.  """

        if not self.charObj.getLimitedBroadcastCount():
            self.selfMsg("You have used all of your broadcasts for today\n")
            return False

        if line == "":
            msg = self.client.promptForInput("Enter Input: ")
        else:
            msg = line

        if msg != "":
            fullmsg = self.charObj.getName() + " broadcasted, '" + msg + "'"
            if self.gameObj.gameMsg(fullmsg + "\n"):
                logger.info(fullmsg)
                self.charObj.reduceLimitedBroadcastCount()
            else:
                self.selfMsg("Message not received\n")

    def do_buy(self, line):
        """ transaction - buy something from a vendor """
        cmdargs = line.split(" ")
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == "Shop":
            self.selfMsg("You can't do that here.  Find a vendor\n")
            return False
        if not roomObj.isVendor():
            self.selfMsg("You can't do that here.  Find a vendor\n")
            return False

        if len(cmdargs) < 1 or not isIntStr(cmdargs[0]):
            self.selfMsg("usage: buy <item> [#]\n")
            return False
        catList = roomObj.getCatalog()
        if int(cmdargs[0]) < 0 or int(cmdargs[0]) > (len(catList)) - 1:
            self.selfMsg("Bad item number.  Aborted\n")
            return False
        catItem = catList[int(cmdargs[0])]
        oType, oNum = catItem.split("/")
        itemObj = ObjectFactory(oType, oNum)
        itemObj.load()
        price = self.gameObj.calculateObjectPrice(charObj, itemObj)

        # check if player has the funds
        if not charObj.canAffordAmount(price):
            self.selfMsg(roomObj.getCantAffordTxt())
            return False
        # check if player can carry the Weight
        weight = itemObj.getWeight()
        if not charObj.canCarryAdditionalWeight(weight):
            self.selfMsg(roomObj.getCantCarryTxt(weight))
            return False

        # prompt player for confirmation
        prompt = (
            "You are about to spend "
            + str(price)
            + " shillings for "
            + itemObj.getArticle()
            + " "
            + itemObj.getName()
            + ".  Proceed?"
        )
        successTxt = roomObj.getSuccessTxt()
        abortTxt = roomObj.getAbortedTxt()
        self.gameObj.buyTransaction(
            charObj, itemObj, price, prompt, successTxt, abortTxt
        )

    def do_cast(self, line):
        """ magic """
        cmdargs = line.split(" ")
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if len(cmdargs) < 1:
            self.selfMsg("Cast what spell?\n")
        spellName = cmdargs[0]
        line = line.lstrip(spellName)

        if spellName not in SpellList:
            self.selfMsg("That's not a valid spell.\n")
            return False

        if not charObj.knowsSpell(spellName):
            self.selfMsg("You haven't learned that spell.\n")
            return False

        if len(cmdargs) > 1:
            possibleTargets = charObj.getInventory() + roomObj.getCharsAndInventory()
            targetList = self.getObjFromCmd(possibleTargets, line)

            if targetList[0]:
                targetObj = targetList[0]
            else:
                self.selfMsg("Could not determine target for spell.\n")
                return False
        else:
            targetObj = self.charObj

        spellObj = Spell(charObj, targetObj, spellName)

        # Apply effects of spell
        spellObj.cast(roomObj)

    def do_catalog(self, line):
        """ info - get the catalog of items from a vendor """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == "Shop":
            self.selfMsg("You can't do that here.  Find a vendor\n")
            return False
        if not roomObj.isVendor():
            self.selfMsg("You can't do that here.  Find a vendor\n")
            return False

        # display # list by iterating, loading, & displaying objs
        itemBuf = ""
        for num, oneitem in enumerate(roomObj.getCatalog()):
            oType, oNum = oneitem.split("/")
            itemObj = ObjectFactory(oType, oNum)
            itemObj.load()
            # calculate price
            price = self.gameObj.calculateObjectPrice(charObj, itemObj)
            ROW_FORMAT = "  ({0:2}) {1:<7} {2:<60}\n"
            itemBuf += ROW_FORMAT.format(num, price, itemObj.describe())
        if itemBuf != "":
            self.selfMsg(
                "Catalog of items for sale\n"
                + ROW_FORMAT.format("#", "Price", "Description")
                + itemBuf
            )

    def do_circle(self, line):
        """ combat - If creature is not attacking, then delay their first
            attack by X seconds """

        target = self.getCombatTarget(line)
        if not target:
            self.selfMsg("Circle what?\n")
            return False

        if target.isAttacking():
            self.selfMsg("You can't circle an attacking creature\n")
            return False

        self.gameObj.circle(self.charObj, target, self.getLastCmd())
        self.selfMsg("Ok.\n")
        return False

    def do_climb(self, line):
        """ alias - go """
        return self.do_go(line)

    def do_clock(self, line):
        """ info - time """
        self.selfMsg(dateStr("now") + "\n")

    def do_close(self, line):
        """ close a door or container """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        itemList = self.getObjFromCmd(roomObj.getInventory(), line)

        if not itemList[0]:
            self.selfMsg("usage: close <item> [number]\n")
            return False

        targetObj = itemList[0]

        if not targetObj.isClosable(charObj):
            if targetObj.isClosed():
                self.selfMsg("It's already closed.\n")
            else:
                self.selfMsg("You can not close that!\n")
            return False

        if targetObj.close(charObj):
            self.selfMsg("Ok\n")
            if targetObj.getType() == "Door":
                self.gameObj.modifyCorrespondingDoor(targetObj, charObj)
            return False
        else:
            self.selfMsg(
                "You can not close " + targetObj.describe(article="the") + "\n"
            )

        return False

    def do_d(self, line):
        """ navigation """
        self.move(self._lastinput[0])  # pass first letter

    def do_debug(self, line):
        """ dm - show raw debug info abot an item/room/character/etc """
        cmdargs = line.split(" ")
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not charObj.isDm():
            self.selfMsg("Unknown Command\n")
            return False

        if len(cmdargs) == 0:
            self.selfMsg("usage: debug <room | self | object>")
            return False

        buf = ""
        if cmdargs[0].lower() == "room":
            buf += "=== Debug Info for Room " + str(roomObj.getId()) + " ===\n"
            buf += roomObj.debug() + "\n"
        elif cmdargs[0].lower() == "game":
            buf += "=== Debug Info for game ===\n"
            buf += self.gameObj.debug() + "\n"
        elif cmdargs[0].lower() == "self":
            buf += "=== Debug Info for Self " + str(charObj.getId()) + " ===\n"
            buf += charObj.debug() + "\n"
        else:
            itemList = self.getObjFromCmd(
                roomObj.getCharsAndInventory() + charObj.getInventory(), line
            )
            if itemList[0]:
                buf += (
                    "=== Debug Info for Object " + str(itemList[0].getId()) + " ===\n"
                )
                buf += itemList[0].debug() + "\n"
        self.selfMsg(buf)
        return None

    def do_deposit(self, line):
        """ transaction - make a deposit in the bank """
        cmdargs = line.split(" ")
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == "Shop":
            self.selfMsg("You can't do that here.  Find a bank\n")
            return False
        if not roomObj.isBank():
            self.selfMsg("You can't do that here.  Find a bank\n")
            return False

        if len(cmdargs) < 1 or not isIntStr(cmdargs[0]):
            self.selfMsg("usage: deposit <amount>\n")
            return False
        # check if player has the funds
        amount = int(cmdargs[0])
        if not charObj.canAffordAmount(amount):
            self.selfMsg(roomObj.getCantAffordTxt(amount))
            return False

        taxRate = roomObj.getTaxRate()
        bankfee, dAmount = charObj.calculateBankFees(amount, taxRate)
        prompt = (
            "You are about to deposit " + str(amount) + " shillings into the bank.\n"
        )
        if taxRate != 0:
            prompt += (
                "The bank charges "
                + "a "
                + str(taxRate)
                + "% deposit fee which comes to a "
                + str(bankfee)
                + " shilling charge.\n"
                + "Your account will increase by "
                + str(dAmount)
                + " shillings.\n"
            )
        prompt += "Continue?"
        if self.client.promptForYN(prompt):
            charObj.bankDeposit(amount, taxRate)
            roomObj.recordTransaction("deposit/" + str(dAmount))
            roomObj.recordTransaction("fees/" + str(bankfee))
            self.selfMsg(roomObj.getSuccessTxt())
            return False
        else:
            self.selfMsg(roomObj.getAbortedTxt())
            return False

    def do_destroy(self, line):
        """ dm - destroy an object or creature """
        if not self.charObj.isDm():
            self.selfMsg("Unknown Command\n")
            return False

        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomObjList = self.getObjFromCmd(roomObj.getInventory(), line)
        if roomObjList[0]:
            roomObj.removeObject(roomObjList[0])
            roomObj.save()
            self.selfMsg("ok\n")
            return False

        charObjList = self.getObjFromCmd(charObj.getInventory(), line)
        if charObjList[0]:
            roomObj.removeFromInventory(charObjList[0])
            self.selfMsg("ok\n")
            return False

    def do_dminfo(self, line):
        """ dm - show char info that isn't directly avaliable to players """
        if not self.charObj.isDm():
            return False
        self.selfMsg(self.charObj.dmInfo())

    def do_dm_on(self, line):
        """ admin - Turn DM mode on """
        if self.acctObj.isAdmin():
            self.charObj.setDm()
            self.selfMsg("ok\n")

    def do_dm_off(self, line):
        """ dm - turn dm mode off """
        if self.charObj.isDm():
            self.charObj.removeDm()
            self.selfMsg("ok\n")
        else:
            self.selfMsg("Unknown Command\n")

    def do_down(self, line):
        """ navigation """
        self.move(self._lastinput[0])  # pass first letter

    def do_draw(self, line):
        """ alias - use """
        return self.do_use(line)

    def do_drink(self, line):
        """ alias - use """
        return self.do_use(line)

    def do_drop(self, line):
        """ drop an item """

        charObj = self.charObj
        roomObj = charObj.getRoom()

        charObjList = charObj.getInventory()

        targetList = self.getObjFromCmd(charObjList, line)

        if not targetList[0]:
            self.selfMsg("What are you trying to drop?\n")
            return False

        if charObj.removeFromInventory(targetList[0]):
            charObj.unEquip(targetList[0])
            roomObj.addObject(targetList[0])
            self.selfMsg("Ok\n")
        else:
            self.selfMsg("Didn't work\n")

    def do_e(self, line):
        """ navigation """
        self.move(self._lastinput[0])  # pass first letter

    def do_east(self, line):
        """ navigation """
        self.move(self._lastinput[0])  # pass first letter

    def do_echo(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_enter(self, line):
        """ alias - go """
        if line == "":
            return self.missingArgFailure()
        self.move(line)

    def do_equip(self, line):
        """ alias - use """
        return self.do_use(line)

    def do_examine(self, line):
        """ alias - look """
        return self.do_look(line)

    def do_exit(self, line):
        """ exit game - returns True to exit command loop """
        return True

    def do_exp(self, line):
        self.selfMsg(self.charObj.expInfo())

    def do_experience(self, line):
        """ info - show character's exp info """
        self.selfMsg(self.charObj.expInfo())

    def do_feint(self, line):
        """ combat """
        target = self.getCombatTarget(line)
        if not target:
            self.selfMsg("Feint at what?\n")
            return False

        self.gameObj.attackCreature(self.charObj, target, self.getLastCmd())
        return False

    def do_file(self, line):
        """ info - show characters attached to account """
        self.selfMsg(self.acctObj.showCharacterList())

    def do_follow(self, line):
        """ follow another player - follower is moved when they move """
        self.selfMsg(line + " not implemented yet\n")

    def do_full(self, line):
        """ set the prompt and room descriptions to maximum verbosity """
        self.charObj.setPromptSize("full")

    def do_get(self, line):  # noqa: C901
        """ pick up an item """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        itemList = self.getObjFromCmd(roomObj.getInventory(), line)

        itemObj = itemList[0]
        containerObj = itemList[1]

        if not itemObj:
            return self.missingArgFailure()

        if itemObj.getType() == "Container":
            if containerObj:
                # Player is trying to put a container from the room into a
                # container in the room.  Let's just say no to that
                self.selfMsg("You can't put a container in a container\n")
                return False
            else:
                # The 1st item was not found, so the container is the 1st item
                containerObj = itemObj

        if containerObj:
            if not containerObj.getType() == "Container":
                self.selfMsg("That's not a container?\n")
                return False

            # Find target item in the container
            cList = self.getObjFromCmd(containerObj.getInventory(), line)
            itemObj = cList[0]
            if not itemObj:
                self.selfMsg("Put what in there?\n")
                return False

        if not itemObj.isCarryable():
            self.selfMsg(itemObj.describe() + " can not be carried.\n")
            return False

        if not charObj.canCarryAdditionalWeight(itemObj.getWeight()):
            self.selfMsg("You are not strong enough.\n")
            return False

        guardingCreatureObj = roomObj.getGuardingCreature()
        if guardingCreatureObj:
            self.selfMsg(
                guardingCreatureObj.describe() + " blocks you from taking that.\n"
            )
            return False

        if containerObj:
            if containerObj.withdraw(charObj, itemObj):
                self.selfMsg("ok\n")
        else:
            # Get item from room
            roomObj.removeObject(itemObj)
            if itemObj.getType() == "Coins":
                charObj.addCoins(itemObj.getValue())
            else:
                charObj.addToInventory(itemObj)
            self.selfMsg("Ok\n")

    def do_go(self, line):
        """ go through a door or portal """
        if line == "":
            self.selfMsg("Go where?\n")
        self.move(line)

    def do_goto(self, line):
        """ dm - teleport directly to a room """
        cmdargs = line.split(" ")
        charObj = self.charObj

        if not self.charObj.isDm():
            self.selfMsg("Unknown Command\n")
            return False

        if len(cmdargs) == 0:
            self.selfMsg("usage: goto <room>\n")
            return False

        self.gameObj.joinRoom(cmdargs[0], charObj)
        self.selfMsg(charObj.getRoom().display(charObj))

    def do_h(self, line):
        """ alias - health """
        charObj = self.charObj
        self.selfMsg(charObj.healthInfo())

    def do_hea(self, line):
        """ alias - health """
        charObj = self.charObj
        self.selfMsg(charObj.healthInfo())

    def do_health(self, line):
        """ info - show character's health """
        charObj = self.charObj
        self.selfMsg(charObj.healthInfo())

    def do_help(self, line):
        """ info - enter the help system """
        enterHelp(self.client)

    def do_hide(self, line):
        """ attempt to hide player or item
            * hidden players aren't attacked by creatures and don't show
              up in room listings unless they are searched for.
            * hidden items don't show up in room listings. """
        # cmdargs = line.split(' ')
        charObj = self.charObj

        if line == "":
            canhide = True
            # can't hide if there are engaged creatures in the room, even if
            # they are attacking someone else.
            for creatObj in charObj.getRoom().getCreatureList():
                if creatObj.isAttacking():
                    canhide = False
            if canhide:
                charObj.attemptToHide()
                msg = "You hide in the shadows"
            else:
                msg = "You are noticed as you hide in the shadows"
                charObj.setHidden(False)

            if charObj.isDm():
                msg += "(" + str(charObj.isHidden()) + ")"
            self.selfMsg(msg + "\n")
        else:
            self.selfMsg(line + " not implemented yet\n")

    def do_hint(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_hit(self, line):
        """ combat """
        target = self.getCombatTarget(line)
        if not target:
            self.selfMsg("Hit what?\n")
            return False

        self.gameObj.attackCreature(self.charObj, target, self.getLastCmd())
        return False

    def do_hold(self, line):
        """ alias - use """
        return self.do_use(line)

    def do_identify(self, line):
        """ info - Show detailed information about a item or character
            * this is considered a limited use spell """
        self.selfMsg(line + " not implemented yet\n")

    def do_info(self, line):
        """ alias - information """
        self.selfMsg(self.charObj.getInfo())

    def do_information(self, line):
        """ info - show all information about a character to that character """
        self.selfMsg(self.charObj.getInfo())

    def do_inv(self, line):
        """ alias - inventory """
        self.selfMsg(self.charObj.inventoryInfo())

    def do_inventory(self, line):
        """ info - show items that character is carrying """
        self.selfMsg(self.charObj.inventoryInfo())

    def do_kill(self, line):
        """ combat """
        target = self.getCombatTarget(line)
        if not target:
            self.selfMsg("Kill what?\n")
            return False

        self.gameObj.attackCreature(self.charObj, target, self.getLastCmd())
        return False

    def do_laugh(self, line):
        """ communication - reaction """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        extramsg = ""
        if line != "":
            extramsg = " " + line

        self.gameObj.roomMsg(roomObj, charObj.getName() + " laughs" + extramsg + "\n")
        charObj.setHidden(False)

    def do_list(self, line):
        """ alias - file """
        return self.do_catalog(line)

    def do_lock(self, line):
        """ lock an object with a key """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomObjList = roomObj.getInventory()
        fullObjList = charObj.getInventory() + roomObjList

        itemList = self.getObjFromCmd(fullObjList, line)

        itemObj = itemList[0]
        keyObj = itemList[1]

        if not itemList[0]:
            return self.missingArgFailure()

        if not keyObj:
            self.selfMsg("You can't lock anything without a key\n")
            return False

        if not itemObj.isLockable():
            if itemObj.isLocked():
                self.selfMsg("It's already locked!\n")
            elif itemObj.isOpen():
                self.selfMsg("You can't lock it when it's open!\n")
            else:
                self.selfMsg("This is not lockable!\n")
            return False

        if keyObj.getLockId() != itemObj.getLockId():
            self.selfMsg("The key doesn't fit the lock\n")
            return False

        itemObj.lock()
        if itemObj.getType() == "Door":
            self.gameObj.modifyCorrespondingDoor(itemObj, charObj)

        self.selfMsg("Ok\n")

        return False

    def do_look(self, line):
        """ examine a creature, object, or player
            * includes items in both the room and in the character inventory
        """
        roomObj = self.charObj.getRoom()

        # Experimenting with sorting.  Not sure if we want this, so we have a
        # Flag for now
        sortList = False
        if sortList:
            allItems = itemSort(roomObj.getCharsAndInventory()) + itemSort(
                self.charObj.getInventory()
            )
        else:
            allItems = roomObj.getCharsAndInventory() + self.charObj.getInventory()

        itemList = self.getObjFromCmd(allItems, line)

        if line == "":  # display the room
            msg = roomObj.display(self.charObj)
            if not re.search("\n$", msg):
                msg += "\n"
            self.selfMsg(msg)
            return False

        if not itemList[0]:
            self.selfMsg("You must be blind because you " + "don't see that here\n")
            return False

        msg = itemList[0].examine()
        if not re.search("\n$", msg):
            msg += "\n"  # append newline if needed
        self.selfMsg(msg)  # display the object
        return False

    def do_lose(self, line):
        """ attempt to ditch someone that is following you """
        self.selfMsg(line + " not implemented yet\n")

    def do_lunge(self, line):
        """ combat """
        target = self.getCombatTarget(line)
        if not target:
            self.selfMsg("Lunge at what?\n")
            return False

        self.gameObj.attackCreature(self.charObj, target, self.getLastCmd())
        return False

    def do_n(self, line):
        """ navigation """
        self.move(self._lastinput[0])  # pass first letter

    def do_north(self, line):
        """ navigation """
        self.move(self._lastinput[0])  # pass first letter

    def do_now(self, line):
        """ alias - clock """
        return self.do_clock()

    def do_o(self, line):
        """ navigation """
        self.move(self._lastinput[0])  # pass first letter

    def do_offer(self, line):
        """ transaction - offer player money/items [in return for $/items] """
        self.selfMsg(self.getLastCmd() + " not implemented yet\n")

    def do_open(self, line):
        """ Open a door or a chest """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        itemList = self.getObjFromCmd(roomObj.getInventory(), line)

        if not itemList[0]:
            return self.missingArgFailure()

        itemObj = itemList[0]

        if not itemObj.isOpenable(charObj):
            if itemObj.isOpen():
                self.selfMsg("It's already open.\n")
            elif itemObj.isLocked():
                self.selfMsg("You can't.  It's locked.\n")
            else:
                self.selfMsg("You can't open that.\n")
            return False

        if itemObj.getType() == "Container":
            if itemObj.hasToll():
                toll = itemObj.getToll()
                if charObj.canAffordAmount(toll):
                    charObj.subtractCoins(toll)
                    self.selfMsg("You paid a toll of {} coins.".format(toll))
                else:
                    self.selfMsg(
                        "Opening this item requires more coins than you have\n"
                    )
                    return False

        if itemObj.open(charObj):
            self.selfMsg("You open it.\n")
            self.othersMsg(
                roomObj,
                charObj.getName() + " opens the " + itemObj.getSingular() + "\n",
                charObj.isHidden(),
            )
            if itemObj.getType() == "Door":
                self.gameObj.modifyCorrespondingDoor(itemObj, charObj)
            return False
        else:
            self.selfMsg("You fail to open the door.\n")
        return False

    def do_out(self, line):
        """ navigation """
        self.move(self._lastinput[0])  # pass first letter

    def do_panic(self, line):
        """ alias - run """
        self.selfMsg(line + " not implemented yet\n")

    def do_parley(self, line):
        """ communication - talk to a npc """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomCreatureList = roomObj.getCreatureList()
        itemList = self.getObjFromCmd(roomCreatureList, line)

        if not itemList[0]:
            self.selfMsg(self.getLastCmd() + " with whom?\n")
            return False

        creat1 = itemList[0]

        msg = creat1.getParleyTxt() + "\n"
        if creat1.getParleyAction().lower() == "teleport":
            self.selfMsg(msg)
            self.gameObj.joinRoom(creat1.getParleyTeleportRoomNum(), charObj)
        elif creat1.getParleyAction().lower() == "sell":
            saleItem = creat1.getParleySaleItem()
            if saleItem:
                price = int(saleItem.getValue() * 0.9)
                prompt = (
                    msg
                    + "  Would you like to buy "
                    + saleItem.describe()
                    + " for "
                    + price
                    + "?"
                )
                successTxt = (
                    "It's all yours.  Don't tell anyone " + "that you got it from me"
                )
                abortTxt = "Another time, perhaps."
                self.gameObj.buyTransaction(
                    charObj, saleItem, price, prompt, successTxt, abortTxt
                )
            else:
                self.selfMsg("I have nothing to sell.\n")
        else:
            self.selfMsg(msg)
        charObj.setHidden(False)

    def do_parry(self, line):
        """ combat """
        target = self.getCombatTarget(line)
        if not target:
            self.selfMsg("Parry at what?\n")
            return False

        self.gameObj.attackCreature(self.charObj, target, self.getLastCmd())
        return False

    def do_pawn(self, line):
        """ alias - sell """
        return self.do_sell(list)

    def do_picklock(self, line):
        """ attempt to pick the lock on a door or container and open it """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        itemList = self.getObjFromCmd(roomObj.getInventory(), line)

        if not itemList[0]:
            self.selfMsg("pick which item with a lock?\n")
            return False

        itemObj = itemList[0]

        if not itemObj.isPickable():
            self.selfMsg("You can't pick that.\n")
            return False

        if itemObj.pick(charObj):
            self.selfMsg("You pick the lock.\n")
            self.othersMsg(
                roomObj,
                charObj.getName()
                + " picks the "
                + "lock on the "
                + itemObj.getSingular()
                + "\n",
                charObj.isHidden(),
            )
            return False
        else:
            self.selfMsg("You fail to pick the lock.\n")
            self.othersMsg(
                roomObj,
                charObj.getName()
                + " fails to pick the lock on the "
                + itemObj.getSingular()
                + "\n",
                charObj.isHidden(),
            )
            return False
        return False

    def do_prompt(self, line):
        """ set verbosity """
        self.charObj.setPromptSize("")

    def do_purse(self, line):
        """ info - display money """
        charObj = self.charObj
        self.selfMsg(charObj.financialInfo())

    def do_put(self, line):
        """ place an item in a container """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        charObjList = charObj.getInventory()
        roomObjList = roomObj.getInventory()

        targetList = self.getObjFromCmd(charObjList + roomObjList, line)

        if not targetList[0]:
            return self.missingArgFailure()

        itemObj = targetList[0]
        containerObj = targetList[1]

        if not itemObj:
            self.selfMsg("What are you trying to put?\n")
            return False

        if not containerObj:
            self.selfMsg("What are you trying to put where?\n")
            return False

        if containerObj.getType() != "Container":
            self.selfMsg("You can't put anything in that!\n")
            return False

        if containerObj.deposit(charObj, itemObj):
            charObj.unEquip(itemObj)
            self.selfMsg("ok\n")
            return False

        self.selfMsg("Didn't work!\n")
        return False

    def do_quit(self, line):
        """ quit the game """
        return self.do_exit(line)

    def do_read(self, line):
        """ magic - read a scroll to use the spell """
        if line == "":
            return self.missingArgFailure()

        self.useMagicItem(line)

        return False

    def do_reloadperm(self, line):
        ''' dm - reload permanents from disk (i.e. after modification) '''
        roomObj = self.charObj.getRoom()

        if not self.charObj.isDm():
            self.selfMsg("Unknown Command\n")
            return False

        itemList = self.getObjFromCmd(roomObj.getInventory(), line)
        if not itemList[0]:
            self.selfMsg("usage: reloadperm <objectname>\n")
            return False

        roomObj.reloadPermanent(itemList[0].getId())
        self.selfMsg("Ok\n")
        return False

    def do_remove(self, line):
        """ unequip an item that you have equipped """
        return self.do_unequip(line)

    def do_repair(self, line):
        """ transaction - repair character's item in a repair shop """
        cmdargs = line.split(" ")
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == "Shop":
            self.selfMsg("You can't do that here.  Find a wright\n")
            return False
        if not roomObj.isRepairShop():
            self.selfMsg("You can't do that here.  Find a wright\n")
            return False

        if len(cmdargs) < 1 or not isIntStr(cmdargs[0]):
            self.selfMsg("usage: repair <item> [#]\n")

        playerInventory = charObj.getInventory()
        itemList = self.getObjFromCmd(playerInventory, line)

        if not itemList[0]:
            return self.missingArgFailure()

        itemObj = itemList[0]

        if not itemObj.canBeRepaired():
            self.selfMsg("This can't be repaired\n")
            return False

        price = self.gameObj.calculateObjectPrice(charObj, itemObj) * 100
        prompt = (
            "You are about to repair "
            + itemObj.getArticle()
            + " "
            + itemObj.getName()
            + " for "
            + str(price)
            + " shillings.  Proceed?"
        )
        if self.client.promptForYN(prompt):
            itemObj.repair()
            roomObj.recordTransaction(itemObj)
            roomObj.recordTransaction("repair/" + str(price))
            charObj.recordTax(roomObj.getTaxAmount(price))
            self.selfMsg(roomObj.getSuccessTxt())
            return False
        else:
            self.selfMsg(roomObj.getAbortedTxt())
            return False

    def do_return(self, line):
        """ alias - unequip """
        return self.do_unequip()

    def do_roominfo(self, line):
        """' dm - show room info """
        if not self.charObj.isDm():
            self.selfMsg("Unknown Command\n")
            return False
        self.selfMsg(self.charObj.getRoom().getInfo())

    def do_run(self, line):
        """ drop weapon and escape room in random direction """
        self.gameObj.run(self.charObj)

    def do_s(self, line):
        """ navigation """
        self.move(self._lastinput[0])  # pass first letter

    def do_save(self, line):
        """ save character """
        if self.client.charObj.save():
            self.selfMsg("Saved\n")
        else:
            self.selfMsg("Could not save\n")

    def do_say(self, line):
        """ communication within room """
        if line == "":
            msg = self.client.promptForInput("Say what? ")
        else:
            msg = line

        if msg != "":
            fullmsg = self.charObj.getName() + " said, '" + msg + "'"
            if self.gameObj.roomMsg(self.charObj.getRoom(), fullmsg + "\n"):
                self.charObj.setHidden(False)
                logger.info(fullmsg)
            else:
                self.selfMsg("Message not received\n")

    def do_search(self, line):
        """ attempt to find items, players, or creatures that are hidden """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        foundSomething = False
        for obj in roomObj.getInventory():
            if obj.isHidden():
                if charObj.searchSucceeds(obj):
                    self.selfMsg("You find " + obj.describe() + "\n")
                    foundSomething = True

        if not foundSomething:
            self.selfMsg("Your search turns up nothing\n")

    def do_sell(self, line):
        """ transaction - Sell an item to a pawnshop """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == "Shop":
            self.selfMsg("You can't do that here.  Find a buyer\n")
            return False
        if not roomObj.isPawnShop():
            self.selfMsg("You can't do that here.  Find a buyer.\n")
            return False

        itemList = self.getObjFromCmd(charObj.getInventory(), line)
        if not itemList[0]:
            return self.missingArgFailure()

        itemObj = itemList[0]

        price = int(self.gameObj.calculateObjectPrice(charObj, itemObj) * 0.8)

        # prompt player for confirmation
        prompt = (
            "You are about to pawn "
            + itemObj.getArticle()
            + " "
            + itemObj.getName()
            + " for "
            + str(price)
            + " shillings.  Proceed?"
        )
        self.gameObj.sellTransaction(
            charObj,
            itemObj,
            price,
            prompt,
            roomObj.getSuccessTxt(),
            roomObj.getAbortedTxt(),
        )

    def do_send(self, line):
        """ communication - direct message to another player """

        if line == "":
            self.selfMsg("usage: send <playerName> [msg]\n")
            return False

        target, msg = self.parseIpc(line)

        if msg != "":
            fullmsg = self.charObj.getName() + " sent, '" + msg + "'"
            if self.gameObj.directMsg(target, fullmsg + "\n"):
                self.charObj.setHidden(False)
                logger.info("To " + target.getName() + ", " + fullmsg)
            else:
                self.selfMsg("Message not received\n")

        return False

    def do_shout(self, line):
        """ communication - alias for yell """
        return self.do_yell(line)

    def do_skills(self, line):
        """ info - show character's skills """
        self.selfMsg(self.charObj.SkillsInfo())

    def do_slay(self, line):
        """ dm - combat - do max damage to creature, effectively killing it """
        target = self.getCombatTarget(line)
        if not target:
            self.selfMsg("Slay what?\n")
            return False

        if self.charObj.isDm():
            atkcmd = "slay"
        else:
            atkcmd = "attack"  # if your not a dm, this is a standard attack

        self.gameObj.attackCreature(self.charObj, target, atkcmd)

        return False

    def do_smash(self, line):
        """ attempt to open a door/chest with brute force """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        itemList = self.getObjFromCmd(roomObj.getInventory(), line)

        if not itemList[0]:
            return self.missingArgFailure()

        itemObj = itemList[0]

        if not itemObj.isSmashable():
            self.selfMsg("This is not smashable!\n")
            return False

        if itemObj.smash(charObj):
            self.othersMsg(
                roomObj,
                charObj.getName()
                + " smashes the "
                + itemObj.getSingular()
                + " open.\n",
            )
            self.selfMsg("You smash it open!\n")
            otherRoom = self.gameObj.getCorrespondingRoomObj(itemObj)
            if otherRoom:
                self.gameObj.roomMsg(
                    otherRoom, itemObj.getSingular() + " smashes open\n"
                )
            if itemObj.getType() == "Door":
                self.gameObj.modifyCorrespondingDoor(itemObj, charObj)
            return False
        else:
            self.othersMsg(
                roomObj,
                charObj.getName()
                + " fails to smash "
                + itemObj.describe()
                + " open.\n",
            )
            self.selfMsg("Bang! You fail to smash it open!\n")
            otherRoom = self.gameObj.getCorrespondingRoomObj(itemObj)
            if otherRoom:
                self.gameObj.roomMsg(
                    otherRoom,
                    "You hear a noise on the "
                    + "other side of the "
                    + itemObj.getSingular()
                    + "\n",
                )
        return False

    def do_south(self, line):
        """ navigation """
        self.move(self._lastinput[0])  # pass first letter

    def do_stats(self, line):
        """ info - show character's stats """
        self.selfMsg(self.charObj.StatsInfo())

    def do_status(self, line):
        """ alias - health """
        return self.do_health()

    def do_steal(self, line):
        """ transaction - attempt to steal from another player """
        self.selfMsg(line + " not implemented yet\n")

    def do_strike(self, line):
        """ combat """
        target = self.getCombatTarget(line)
        if not target:
            self.selfMsg("Strike what?\n")
            return False

        self.gameObj.attackCreature(self.charObj, target, self.getLastCmd())
        return False

    def do_study(self, line):
        """ magic - study a scroll to learn the chant """
        charObj = self.charObj

        if line == "":
            return self.missingArgFailure()

        (spellItem, spellName, targetObj) = self.parseSpellArgs(line)

        if not spellItem:
            self.selfMsg("Study what?\n")
            return False

        if not spellItem.getType().lower() == "scroll":
            self.selfMsg("You can't study that.\n")
            return False

        # Learn the spell and display the chant
        msg = spellItem.study(charObj)
        self.selfMsg(msg)

        # Remove item from player's inventory
        self.gameObj.removeFromPlayerInventory(charObj, spellItem, "disint")

        return False

    def do_suicide(self, line):
        if not self.client.promptForYN(
            "DANGER: This will permanently "
            + "delete your character."
            + "  Are you sure?"
        ):
            return False
        charObj = self.charObj
        charName = charObj.getName()
        self.gameObj.leaveGame(self.client, saveChar=False)
        msg = self.client.txtBanner(
            charName + " has shuffled off this mortal coil", bChar="="
        )
        charObj.delete()
        charObj = None
        self.charObj = None
        self.acctObj.removeCharacterFromAccount(charName)
        self.gameObj.gameMsg(msg)
        logger.info("Character deleted: " + charName)
        return True

    def do_take(self, line):
        """ alias - get """
        return self.do_get(line)

    def do_talk(self, line):
        """ alias - parley """
        return self.do_parley(line)

    def do_teach(self, line):
        """ teach another player a spell """
        self.selfMsg(line + " not implemented yet\n")

    def do_toggle(self, line):
        """ dm command to set flags """
        if self.charObj.isDm():
            if (
                line.lower() == "character"
                or line.lower() == "char"
                or line.lower() == "self"
            ):
                obj = self.charObj
            elif line.lower() == "room":
                obj = self.charObj.getRoom()
            elif line.lower() == "game":
                obj = self.gameObj
            elif line.lower() == "gamecmd":
                obj = self
            elif line.lower() == "client":
                obj = self.client
            else:
                roomObj = self.charObj.getRoom()
                itemList = self.getObjFromCmd(roomObj.getCharsAndInventory(), line)
                if itemList[0]:
                    obj = itemList[0]
                else:
                    self.selfMsg("Can't toggle " + line + "\n")
                    self.selfMsg(
                        "Fixed toggles:\n" + "  self, room, game, gamecmd, client\n"
                    )
                    return False
        else:
            self.selfMsg("Unknown Command\n")
            return False

        obj.toggleInstanceDebug()
        self.selfMsg(
            "Toggled " + line + ": debug=" + str(obj.getInstanceDebug()) + "\n"
        )
        return False

    def do_thrust(self, line):
        """ combat """
        target = self.getCombatTarget(line)
        if not target:
            self.selfMsg("Thrust at what?\n")
            return False

        self.gameObj.attackCreature(self.charObj, target, self.getLastCmd())
        return False

    def do_track(self, line):
        """ show direction last player traveled """
        self.selfMsg(line + " not implemented yet\n")

    def do_train(self, line):
        """ increase level if exp and location allow """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomObj.train(charObj)

    def do_turn(self, line):
        """ magic - chance for clerics/paladins to destroy creatures """
        self.selfMsg(line + " not implemented yet\n")

    def do_u(self, line):
        """ navigation """
        self.move(self._lastinput[0])  # pass first letter

    def do_unequip(self, line):
        """ stop using a piece of equiptment """
        charObj = self.charObj

        targetList = self.getObjFromCmd(charObj.getInventory(), line)

        if not targetList[0]:
            return self.missingArgFailure()
        elif len(targetList) > 0:
            itemObj = targetList[0]
        else:
            itemObj = None

        if charObj.unEquip(itemObj):
            self.selfMsg("Ok\n")
        else:
            self.selfMsg("You can't do that\n")

    def do_unlock(self, line):
        """ unlock a door/chest with a key """
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomObjList = roomObj.getInventory()
        fullObjList = charObj.getInventory() + roomObjList

        itemList = self.getObjFromCmd(fullObjList, line)

        if not itemList[0]:
            return self.missingArgFailure()

        itemObj = itemList[0]
        keyObj = itemList[1]

        if not keyObj:
            self.selfMsg("You can't lock anything without a key\n")
            return False

        if not itemObj.isUnlockable():
            if itemObj.isUnlocked():
                self.selfMsg("It's already unlocked!\n")
            elif itemObj.isOpen():
                self.selfMsg("You can't unlock it when it's open!\n")
            else:
                self.selfMsg("This is not unlockable!\n")
            return False

        if keyObj.getLockId() != itemObj.getLockId():
            self.selfMsg("The key doesn't fit the lock\n")
            return False

        if itemObj.unlock(keyObj):
            if itemObj.getType() == "Door":
                self.gameObj.modifyCorrespondingDoor(itemObj, charObj)
            self.selfMsg("You unlock the lock.\n")
            self.othersMsg(
                roomObj,
                charObj.getName()
                + " unlocks the "
                + "lock on the "
                + itemObj.getSingular()
                + "\n",
                charObj.isHidden(),
            )
            return False
        else:
            self.selfMsg("You fail to unlock the lock.\n")
            self.othersMsg(
                roomObj,
                charObj.getName()
                + " fails to "
                + "unlock the lock on the "
                + itemObj.getSingular()
                + "\n",
                charObj.isHidden(),
            )
            return False

        return False

    def do_up(self, line):
        """ navigation """
        self.move(self._lastinput[0])  # pass first letter

    def do_use(self, line):
        """ equip an item or use a scroll or magic item """

        if line == "":
            return self.missingArgFailure()

        charObj = self.charObj
        roomObj = charObj.getRoom()

        objList = charObj.getInventory() + roomObj.getCharsAndInventory()
        targetList = self.getObjFromCmd(objList, line)

        itemObj = None

        # Require at least one arg after command
        for target in targetList:
            if not target:
                continue
            if not target.isUsable():
                continue
            if not itemObj:
                itemObj = target

        if not itemObj:
            return self.missingArgFailure()

        type = itemObj.getType()
        if type == "Character" or type == "Creature":
            return self.missingArgFailure()

        if isObjectFactoryType(type):
            self.useObject(itemObj, line)
            return False

        logger.warn(
            "game.do_use: Attempt to use: "
            + itemObj.describe()
            + " - with type "
            + type
        )

        if roomObj:  # tmp - remove later if room object is not needed here
            pass  # but there may be spells/items that affect the room.

    def do_w(self, line):
        """ navigation """
        self.move(self._lastinput[0])  # pass first letter

    def do_wear(self, line):
        """ alias - use """
        return self.do_use(line)

    def do_west(self, line):
        """ navigation """
        self.move(self._lastinput[0])  # pass first letter

    def do_where(self, line):
        """ alias - look """
        return self.do_look(line)

    def do_whisper(self, line):
        """ communication - char to char, with chance of being overheard """
        if line == "":
            self.selfMsg("usage: whisper <playerName> [txt]\n")
            return False

        target, msg = self.parseIpc(line)

        received = False
        charName = self.charObj.getName()
        for oneChar in self.charObj.getRoom().getCharacterList():
            if target == oneChar:  # if is recipient
                oneChar.client.spoolOut(
                    charName + " whispers, '" + msg + "'\n"  # notify
                )
                received = True
            else:
                if not oneChar.hearsWhispers():
                    continue
                oneChar.client.spoolOut(
                    "You overhear " + charName + " whisper " + msg + "\n"
                )
                self.charObj.setHidden(False)
        if received:
            self.selfMsg("ok\n")
        else:
            self.selfMsg("Message not received\n")

        return False

    def do_who(self, line):
        """ info - show who is playing the game """
        charTxt = ""
        charObj = self.charObj
        for onechar in charObj.getRoom().getCharacterList():
            if onechar != charObj:
                charTxt += onechar.getName() + "\n"
        if charTxt == "":
            buf = "You are the only one in the game\n"
        else:
            buf = "Characters in the Game:\n" + charTxt
        self.selfMsg(buf)
        return None

    def do_wield(self, line):
        """ alias - use """
        return self.do_use(line)

    def do_withdraw(self, line):
        """ transaction - take money out of the bank """
        cmdargs = line.split(" ")
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == "Shop":
            self.selfMsg("You can't do that here.  Find a bank\n")
            return False
        if not roomObj.isBank():
            self.selfMsg("You can't do that here.  Find a bank\n")
            return False

        if len(cmdargs) < 1 or not isIntStr(cmdargs[0]):
            self.selfMsg("usage: withdraw <amount>\n")
            return False
        amount = int(cmdargs[0])
        if not charObj.canWithdraw(amount):
            self.selfMsg(roomObj.getCantAffordTxt(amount))
            return False
        taxRate = roomObj.getTaxRate()
        bankfee, wAmount = charObj.calculateBankFees(amount, taxRate)
        prompt = (
            "You are about to withdraw " + str(amount) + " shillings from the bank.\n"
        )
        if taxRate != 0:
            prompt += (
                "The bank charges a "
                + str(taxRate)
                + "% withdrawl fee which comes to a charge of "
                + str(bankfee)
                + "shillings.\n"
                + "As a result, you will receive "
                + str(wAmount)
                + " shillings.\n"
            )
        prompt += "Continue?"
        if self.client.promptForYN(prompt):
            charObj.bankWithdraw(amount, taxRate)
            roomObj.recordTransaction("withdrawl/" + str(wAmount))
            roomObj.recordTransaction("fees/" + str(bankfee))
            self.selfMsg(roomObj.getSuccessTxt())
            return False
        else:
            self.selfMsg(roomObj.getAbortedTxt())
            return False

    def do_yell(self, line):
        """ communication - all in room and adjoining rooms """
        if line == "":
            msg = self.client.promptForInput(self.getLastCmd() + " what? ")
        else:
            msg = line

        if msg != "":
            fullmsg = self.charObj.getName() + " yelled, '" + msg + "'"
            if self.gameObj.yellMsg(self.charObj.getRoom(), fullmsg + "\n"):
                logger.info(fullmsg)
                self.charObj.setHidden(False)
            else:
                self.selfMsg("Message not received\n")


# instanciate the _Game class
_game = _Game()


def Game():
    """ return a reference to the single, existing _game instance
        Thus, when we try to instanciate Game, we are just returning
        a ref to the existing Game """

    return _game
