''' game class '''  # noqa

# We want only one implementation of the Game Class.
# To do this, create a single instance of the Game class on import.  Then
# each time we try to instanciate Game(), we just return a reference to
# the game class.

import cmd
from datetime import datetime
import logging
import pprint
import random
import re
from time import sleep

from common.combat import Combat
from common.ipc import Ipc
from common.general import isIntStr, dateStr, dLog
from common.general import splitTargets, targetSearch
from common.general import getRandomItemFromList
from common.help import enterHelp
from common.magic import Spell, SpellList
from room import Room, RoomFactory
from object import ObjectFactory
# from object import Potion, Scroll, Teleport, Staff
from object import Scroll
from character import Character
from creature import Creature


class _Game(cmd.Cmd, Combat, Ipc):
    ''' Single instance of the Game class, shared by all users
        (see instanciation magic at the bottom of the file)'''

    _instanceDebug = False

    def __init__(self):
        ''' game-wide attributes '''
        self.instance = "Instance at %d" % self.__hash__()
        self._activeRooms = []
        self._activePlayers = []
        self._startdate = datetime.now()

        self._instanceDebug = _Game._instanceDebug

        self._asyncStopFlag = False    # If true, the async thread will halt
        return(None)

    def debug(self):
        return(pprint.pformat(vars(self)))

    def toggleInstanceDebug(self):
        self._instanceDebug = not self._instanceDebug

    def getInstanceDebug(self):
        return(self._instanceDebug)

    def _asyncTasks(self):
        ''' Tasks that run in a separate thread with ~1 sec intervals '''
        logging.info("Thread started - async worker")
        while not self._asyncStopFlag:
            self.asyncNonPlayerActions()
            self.asyncCharacterActions()
            sleep(1)

    def haltAsyncThread(self):
        self._asyncStopFlag = True

    def joinGame(self, client):
        ''' Perform required actions related to joining the game '''
        charObj = client.charObj
        if not charObj:
            logging.warn("Game: Character not defined - returning False")
            return(False)

        gameCmd = GameCmd(client)      # each user gets their own cmd shell

        self.addToActivePlayerList(charObj)

        # in-game broadcast announcing game entry
        msg = client.txtBanner(charObj.getName() +
                               ' has entered the game', bChar='=')
        self.gameMsg(msg + '\n')
        logging.info("JOINED GAME " + charObj.getId())

        # add room to charObj and then display the room
        if self.joinRoom(1, charObj):
            self.charMsg(charObj, charObj.getRoom().display(charObj))
            try:
                gameCmd.cmdloop()           # start the game cmdloop
            finally:
                if client.charObj:
                    self.leaveGame(client)
        return(False)

    def leaveGame(self, client, saveChar=True):
        ''' Handle details of leaving a game '''
        charObj = client.charObj

        self.leaveRoom(charObj)

        # remove character from game character list
        self.removeFromActivePlayerList(charObj)

        # final character save before throwing away charObj
        if saveChar:
            # saveChar is False when it's a suicide
            charObj.save(logStr=__class__.__name__)

        # notification and logging
        msg = client.txtBanner(charObj.getName() +
                               ' has left the game', bChar='=')
        self.gameMsg(msg + '\n')
        logging.info("LEFT GAME " + charObj.getId())

        # Discard charObj
        charObj = None
        client.charObj = None
        return(True)

    def getCharacterList(self):
        return(self._activePlayers)

    def addToActivePlayerList(self, charObj):
        ''' add character to list of characters in game '''
        if charObj not in self.getCharacterList():
            self._activePlayers.append(charObj)

    def removeFromActivePlayerList(self, charObj):
        ''' remove character from list of characters in game '''
        if charObj in self.getCharacterList():
            self._activePlayers.remove(charObj)

    def getActiveRoomList(self):
        return(self._activeRooms)

    def addToActiveRooms(self, roomObj):
        ''' Add room to active room list '''
        if roomObj not in self.getActiveRoomList():
            self._activeRooms.append(roomObj)
        return(True)

    def removeFromActiveRooms(self, roomObj):
        ''' Remove room from active room list '''
        if self.isActiveRoom(roomObj):
            self._activeRooms.remove(roomObj)
        return(True)

    def isActiveRoom(self, roomObj):
        ''' Return true if room is in active room list '''
        if roomObj in self.getActiveRoomList():
            return(True)
        return(False)

    def getActiveRoom(self, num):
        ''' Return the roomObj for an active room, given the room number '''
        for roomObj in self.getActiveRoomList():
            if roomObj.getId() == num:
                return(roomObj)
        return(None)

    def deActivateEmptyRoom(self, roomObj):
        ''' deactiveates room if empty.  Returns true if deactiveated '''
        if len(roomObj.getCharacterList()) == 0:
            self.removeFromActiveRooms(roomObj)
            return(True)
        return(False)

    def asyncCharacterActions(self):
        ''' asyncronous actions that occur to players. '''
        for charObj in self.getCharacterList():
            charObj.processPoisonAndRegen()

    def asyncNonPlayerActions(self):
        ''' asyncronous actions that are not tied to a player. '''
        for roomObj in self.getActiveRoomList():
            if self.deActivateEmptyRoom(roomObj):
                continue
            self.creatureEncounter(roomObj)
            self.creaturesAttack(roomObj)
        return(None)

    def roomLoader(self, roomStr):
        ''' returns a roomObj, given a roomStr '''
        logPrefix = 'game.roomLoader (' + str(roomStr) + ')'
        roomObj = None
        roomType = 'room'

        roomStr = str(roomStr)
        if isIntStr(roomStr):
            roomNum = int(roomStr)
        else:
            # if it's not a number, assume it's in the form: Room/35
            roomType, roomNum = roomStr.split('/')

        if isIntStr(roomNum):
            roomNum = int(roomNum)
            if roomNum == 0:
                logging.error(logPrefix + "Room number is 0")
                return(None)
        else:
            logging.error(logPrefix + "Room number is invalid")
            return(None)

        # See if room is already active
        for oneroom in self.getActiveRoomList():
            if oneroom.getRoomNum() == roomNum:  # if the room alread exists
                roomObj = oneroom                # use existing roomObj

        if not roomObj:
            roomObj = RoomFactory(roomType, roomNum)  # instanciate room object
            roomObj.load(logStr=__class__.__name__)  # load room from disk

        if roomObj is None:
            logging.error(logPrefix + "Room object is None")

        return(roomObj)

    def joinRoom(self, roomThing, charObj):
        ''' insert player into a room
            * can accept room number or roomObj
            * create or join room instance
            * add character to room instance
            * add room to character instance
            * add room to active rooms list
            * close spring loaded doors if room is empty
            # roomStr can be a room number or can be in the form Shop/35
        '''

        if isinstance(roomThing, Room):
            roomObj = roomThing
        else:
            roomObj = self.roomLoader(roomThing)

        if not roomObj:
            logging.error("joinRoom: Could not get roomObj")
            return(False)

        existingRoom = charObj.getRoom()
        if existingRoom:
            if existingRoom == roomObj:         # if already in desired room
                return(True)                    # do nothing
            else:
                self.leaveRoom(charObj)         # leave the previous room

        charObj.setRoom(roomObj)        # Add room to character
        roomObj.addCharacter(charObj)   # Add character to room
        self.addToActiveRooms(roomObj)  # Add room to active room list
        return(True)

    def leaveRoom(self, charObj):
        ''' Handle details of leaving a room
            * Remove room from active rooms list if it's empty
            * remove character from room instance
            * remove room from character instance
            * toDo - check if other players/creatures follow
            * toDo - notify others that character has left the room
            * toDo - stop/reassign attackers
        '''

        if not charObj:
            return(False)
        if not charObj.getRoom():  # There is no previous room, so just return
            return(True)
        if charObj.getRoom().getId() == 0:   # Not a real room - just loaded?
            return(True)

        charObj.getRoom().savePermanents()

        charObj.getRoom().removeCharacter(charObj)  # remove charact from room
        # if room's character list is empty, remove room from activeRoomList
        if len(charObj.getRoom().getCharacterList()) == 0:
            self.removeFromActiveRooms(charObj.getRoom())
        charObj.removeRoom()                       # Remove room from character
        return(True)

    def calculateObjectPrice(self, charObj, obj):
        ''' return adjusted price for an object based on many factors '''
        if obj.isCursed():
            return(1)

        price = obj.getValue()
        price = obj.adjustPrice(price)   # object adjustment
        price = charObj.getRoom().adjustPrice(price)  # room adjustment
        price = charObj.adjustPrice(price)  # char adjust
        return(price)

    def getCorrespondingRoomObj(self, doorObj, activeOnly=False):
        ''' Get the room object that correcponds to a door '''
        roomObj = self.getActiveRoom(doorObj.getToWhere())
        if not roomObj:                       # If active room doesn't exist
            if not activeOnly:
                # Load room from disk into separate instance
                roomObj = RoomFactory("room", doorObj.getToWhere())
                roomObj.load()
            else:
                roomObj = None
        return(roomObj)

    def modifyCorrespondingDoor(self, doorObj):
        ''' When a door is opened/closed on one side, the corresponing door
            needs to be updated '''

        # Persist the current door state to disk
        doorObj.save()

        roomObj = self.getCorrespondingRoomObj()

        if roomObj:
            for obj in roomObj.getInventory():
                if obj.getId() == doorObj.getCorresspondingDoorId():
                    if doorObj.isClosed():
                        obj.close()
                    else:
                        obj.open()
                    obj.save()
            return(True)
        else:
            roomObj = RoomFactory("room", doorObj.getToWhere())

        return(True)

    def buyTransaction(self, charObj, obj, price, prompt,
                       successTxt='Ok.', abortTxt='Ok.'):
        ''' buy an item '''
        roomObj = charObj.getRoom()

        if charObj.client.promptForYN(prompt):
            charObj.subtractCoins(price)           # tax included
            charObj.addToInventory(obj)         # add item
            if roomObj.getType() == 'Shop':
                roomObj.recordTransaction(obj)      # update stats
                roomObj.recordTransaction("sale/" + str(price))
                charObj.recordTax(roomObj.getTaxAmount(price))
            self.charMsg(charObj, successTxt)
            logging.info("PURCHASE " + charObj.getId() + " bought " +
                         obj.describe() + " for " + str(price))
            return(True)
        else:
            self.charMsg(charObj, abortTxt)
        return(False)

    def sellTransaction(self, charObj, obj, price, prompt,
                        successTxt='Ok.', abortTxt='Ok.'):
        ''' sell an item '''
        roomObj = charObj.getRoom()

        if charObj.client.promptForYN(prompt):
            charObj.removeFromInventory(obj)     # remove item
            charObj.addCoins(price)              # tax included
            if roomObj.getType() == 'Shop':
                roomObj.recordTransaction(obj)       # update stats
                roomObj.recordTransaction("purchase/" + str(price))
                charObj.recordTax(roomObj.getTaxAmount(price))
            self.charMsg(charObj, successTxt)
            logging.info("SALE " + charObj.getId() + " sold " +
                         obj.describe() + " for " + str(price))

            return(True)
        else:
            self.charMsg(charObj, abortTxt)
            return(False)

    def use_scroll(self, charObj, itemObj, targetObj):
        ''' using a scroll will cast a spell, but then it disintegrates '''
        spellObj = Spell(charObj.getClass(), itemObj.getSpell())
        self.charMsg(charObj, "The scroll disintegrates\n")

        if not targetObj:           # if second target is not defined
            targetObj = charObj     # current character is the target

        self.castSpell(charObj, spellObj, targetObj)
        charObj.removeFromInventory(itemObj)     # remove item

    def use_magicitem(self, charObj, itemObj, targetObj):
        ''' using a magic casts a spell and depletes one charge of the item '''
        if itemObj.getCharges() <= 0:
            self.charMsg(charObj, "This item has no charges left\n")
            return(False)
        if itemObj.getCharges() == 1:
            self.charMsg(charObj, itemObj.getName() + "fizzles\n")

        spellObj = Spell(charObj.getClass(), itemObj.getSpell())

        if not targetObj:           # if second target is not defined
            targetObj = charObj     # current character is the target

        self.castSpell(charObj, spellObj, targetObj)
        itemObj.decrementChargeCounter()

    def castSpell(self, charObj, spellObj, target):
        ''' perform the spell
            * assume that all other checks are complete
        '''
        if not spellObj:
            return(False)

        if not target:
            return(False)

        # charObj.setlastAttackDamageType("magic")

        # roll/check for spell success
        if isinstance(target, Character):   # use on Character
            pass
        elif isinstance(target, Creature):  # use on Creature
            pass
        else:                             # use on object
            pass
        return(False)

    def creatureEncounter(self, roomObj):
        ''' As an encounter, add creature to room
            Chance based on
              * room encounter rates and encounter list
              * creature frequency
        '''
        debugPrefix = 'Game creatureEncounter (' + str(roomObj.getId()) + '): '
        if not roomObj.readyForEncounter():
            # dLog(debugPrefix + 'Room not ready for encounter',
            #      self._instanceDebug)
            return(False)

        if len(roomObj.getInventoryByType('Creature')) >= 6:
            self.roomMsg(roomObj, 'Others arrive, but wander off.\n',
                         allowDupMsgs=False)
            return(False)

        # Create a creature cache, so that we don't have to load the
        # creatures every time we check for encounters.  These creatures are
        # never actually encountered.  They just exist for reference
        if len(roomObj.getCreatureCache()) == 0:
            dLog(debugPrefix + 'Populating room creature cache',
                 self._instanceDebug)
            # loop through all possible creatures for room and fill cache
            for ccNum in roomObj.getEncounterList():
                ccObj = Creature(ccNum)
                ccObj.load()
                roomObj.creatureCachePush(ccObj)
                dLog(debugPrefix + 'Cached ' + ccObj.describe(),
                     self._instanceDebug)

        # Determine which creatures, from the cache, can be encountered, by
        # comparing their frequency attribute to a random roll.  Fill a
        # eligibleCreatureList with possible creatures for encounter.
        eligibleCreatureList = []
        for ccObj in roomObj.getCreatureCache():
            if ccObj.getFrequency() >= random.randint(1, 100):
                # Load creature to be encountered
                cObj = Creature(ccObj.getId())
                cObj.load()
                eligibleCreatureList.append(cObj)
                dLog(debugPrefix + cObj.describe() + ' is eligible',
                     self._instanceDebug)

        creatureObj = getRandomItemFromList(eligibleCreatureList)
        if creatureObj:
            roomObj.addToInventory(creatureObj)
            dLog(debugPrefix + str(creatureObj.describe()) + ' added to room',
                 self._instanceDebug)
            self.roomMsg(roomObj, creatureObj.describe() + ' has arrived\n')
            creatureObj.setEnterRoomTime()
            roomObj.setLastEncounter()
        return(None)


class GameCmd(cmd.Cmd):
    ''' Game loop - separate one for each player
        * Uses cmd loop with do_<action> methods
        * if do_ methods return True, then loop exits
    '''
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

        self._lastinput = ''
        self._instanceDebug = False

    def getCmdPrompt(self):
        sp = '<'
        ep = '>'
        if self.charObj:
            promptsize = self.charObj.getPromptSize()
        else:
            promptsize = 'full'

        if promptsize == 'brief':
            promptStr = ep + ' '
        else:
            promptStr = sp + 'game' + ep + ' '
        return(promptStr)

    def cmdloop(self):
        ''' cmd method override - Game loop
            requires player to have character loaded '''
        stop = False
        line = ""
        self.preloop()
        while not stop:
            if self.client.promptForCommand(self.getCmdPrompt()):  # send/recv
                line = self.client.getInputStr()
                self._lastinput = line
                dLog("GAME cmd = " + line, self._instanceDebug)
                self.precmd(line)
                stop = self.onecmd(line)
                self.postcmd(stop, line)
            else:
                stop = True
        self.postloop()

    def precmd(self, line):
        ''' cmd method override '''
        pass

    def postcmd(self, stop, line):
        ''' cmd method override '''
        if self.charObj:  # doesn't exist if there is a suicide
            self.charObj.save(logStr=__class__.__name__)
        return(stop)

    def emptyline(self):
        ''' cmd method override '''
        return(False)

    def default(self, line):
        ''' cmd method override '''
        logging.warn('*** Invalid game command: %s\n' % line)
        self.charObj.client.spoolOut("Invalid Command\n")

    def getObjFromCmd(self, itemList, cmdline):
        ''' Returns a list of target Items, given the full cmdargs '''
        targetItems = []
        for target in splitTargets(cmdline):
            obj = targetSearch(itemList, target)
            if obj:
                targetItems.append(obj)
        targetItems += [None] * 2          # Add two None items to the list
        return(targetItems)

    def getCombatTarget(self, line):
        ''' All combat commands need to determine the target '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        creatureList = roomObj.getInventoryByType('Creature')
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

            return(None)

        return(target)

    def selfMsg(self, msg):
        ''' send message using Game communnication.  This simply allows us
            to call it without passing the extra arg) '''
        return(self.gameObj.charMsg(self.charObj, msg))

    def othersMsg(self, roomObj, msg, ignore):
        ''' send message using Game communnication.  This simply allows us
            to call it without passing the extra arg) '''
        return(self.gameObj.othersInRoomMsg(self.charObj, roomObj,
                                            msg, ignore))

    def move(self, line):
        cmdargs = line.split(' ')
        charObj = self.charObj
        moved = False
        currentRoom = charObj.getRoom()
        oldRoom = charObj.getRoom()
        if currentRoom.isDirection(cmdargs[0]):  # if command is a direction
            # Handle the primary directions
            direction = cmdargs[0]
            dLog("GAME move dir = " + direction, self._instanceDebug)
            exitDict = currentRoom.getExits()
            if direction in exitDict.keys():
                roomObj = self.gameObj.roomLoader(exitDict[direction])
                if roomObj:
                    if roomObj.canBeJoined(charObj):
                        self.gameObj.joinRoom(roomObj, charObj)
                        currentRoom = charObj.getRoom()
                        moved = True
        else:
            # handle doors and Portals
            itemList = self.getObjFromCmd(currentRoom.getInventory(), line)

            if not itemList[0]:       # no object - take no action
                self.selfMsg("That is not somewhere you can go!\n")
                return(False)

            if not itemList[0].canBeEntered(charObj):
                return(False)

            roomnum = itemList[0].getToWhere()
            roomObj = self.gameObj.roomLoader(roomnum)
            if roomObj:
                if roomObj.canBeJoined(charObj):
                    self.gameObj.joinRoom(roomnum, charObj)
                    currentRoom = charObj.getRoom()
                    moved = True

        if moved:
            dLog("GAME move obj = " + str(roomObj.describe()),
                 self._instanceDebug)
            # creatures in old room should stop attacking player
            self.gameObj.unAttack(oldRoom, charObj)
            # character possibly loses hidden
            charObj.possibilyLoseHiddenWhenMoving()
            self.selfMsg(charObj.getRoom().display(charObj))
            return(True)
        else:
            self.selfMsg("You can not go there!\n")
        return(False)

    def do_accept(self, line):
        ''' transaction - accept an offer '''
        self.selfMsg(line + " not implemented yet\n")

    def do_appeal(self, line):
        ''' ask DMs for help '''
        self.selfMsg(line + " not implemented yet\n")

    def do_attack(self, line):
        ''' combat '''
        target = self.getCombatTarget(line)
        if not target:
            return(False)

        self.gameObj.attackCreature(self.charObj, target,
                                    self.lastcmd.split(" ", 1)[0])
        return(False)

    def do_backstab(self, line):
        ''' combat '''

        # monster gets double damage on next attack

        target = self.getCombatTarget(line)
        if not target:
            return(False)

        self.gameObj.attackCreature(self.charObj, target,
                                    self.lastcmd.split(" ", 1)[0])
        return(False)

    def do_balance(self, line):
        ''' info - view bank balance when in a bank '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == 'Shop':
            self.selfMsg("You can't do that here.  Find a bank\n")
            return(False)
        if not roomObj.isBank():
            self.selfMsg("You can't do that here.  Find a bank.\n")
            return(False)

        amount = charObj.getBankBalance()
        self.selfMsg("Your account balance is " + str(amount) +
                     " shillings.\n")

    def do_block(self, line):
        ''' combat '''
        target = self.getCombatTarget(line)
        if not target:
            return(False)

        self.gameObj.attackCreature(self.charObj, target,
                                    self.lastcmd.split(" ", 1)[0])
        return(False)

    def do_break(self, line):
        ''' alias - smash '''
        return(self.do_smash(line))

    def do_bribe(self, line):
        ''' transaction - bribe a creature to vanish '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if len(cmdargs) < 2:
            self.selfMsg("Try 'bribe <creature> <amount>'\n")
            return(False)
        if not isIntStr(cmdargs[1]):
            self.selfMsg("How many shillings are you trying to bribe with?'\n")
            return(False)

        creatureName = cmdargs[0]
        coins = int(cmdargs[1])

        roomCreatureList = roomObj.getCreatureList()
        itemList = self.getObjFromCmd(roomCreatureList, creatureName)

        if not itemList[0]:
            self.selfMsg("Who are you trying to bribe?\n")
            return(False)

        creatureObj = itemList[0]
        if creatureObj:
            if creatureObj.acceptsBribe(charObj, coins):
                # Bribe succeeds - money is already subtracted
                self.selfMsg(creatureObj.describe(article="The") +
                             " accepts your offer and leaves\n")
                roomObj.removeFromInventory(creatureObj)
                return(False)
            else:
                # Bribe failed - contextual response already provided
                charObj.setHidden(False)
        return(False)

    def do_brief(self, line):
        ''' set the prompt and room description to least verbosity '''
        self.charObj.setPromptSize("brief")

    def do_broadcast(self, line):
        ''' communication '''
        pass

    def do_buy(self, line):
        ''' transaction - buy something from a vendor '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == 'Shop':
            self.selfMsg("You can't do that here.  Find a vendor\n")
            return(False)
        if not roomObj.isVendor():
            self.selfMsg("You can't do that here.  Find a vendor\n")
            return(False)

        if len(cmdargs) < 1 or not isIntStr(cmdargs[0]):
            self.selfMsg("usage: buy <item> [#]\n")
            return(False)
        catList = roomObj.getcatalog()
        if ((int(cmdargs[0]) < 0 or
             int(cmdargs[0]) > (len(catList)) - 1)):
            self.selfMsg("Bad item number.  Aborted\n")
            return(False)
        catItem = catList[int(cmdargs[0])]
        oType, oNum = catItem.split('/')
        obj1 = ObjectFactory(oType, oNum)
        obj1.load()
        price = self.gameObj.calculateObjectPrice(charObj, obj1)

        # check if player has the funds
        if not charObj.canAffordAmount(price):
            self.selfMsg(roomObj.getCantAffordTxt())
            return(False)
        # check if player can carry the Weight
        weight = obj1.getWeight()
        if not charObj.canCarryAdditionalWeight(weight):
            self.selfMsg(roomObj.getCantCarryTxt(weight))
            return(False)

        # prompt player for confirmation
        prompt = ("You are about to spend " + str(price) +
                  " shillings for " + obj1.getArticle() + " " +
                  obj1.getName() + ".  Proceed?")
        successTxt = roomObj.getSuccessTxt()
        abortTxt = roomObj.getAbortedTxt()
        self.gameObj.buyTransaction(charObj, obj1, price, prompt,
                                    successTxt, abortTxt)

    def do_cast(self, line):
        ''' magic '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if line == '':
            self.selfMsg("Cast what spell?\n")

        parts = line.split(' ', 1)
        spell = parts[0]
        if len(parts) > 1:
            targetline = parts[1]

        if spell not in SpellList:
            self.selfMsg("That's not a valid spell.\n")
            return(False)

        if not charObj.knowsSpell(spell):
            self.selfMsg("You haven't learned that spell.\n")
            return(False)

        allTargets = roomObj.getCharsAndInventory()
        targetList = self.getObjFromCmd(allTargets, targetline)

        if targetList[0]:
            target = targetList[0]
        else:
            if targetline != '':
                self.selfMsg("Could not determine target for spell.\n")
                return(False)
            target = charObj

        spellObj = Spell(charObj.getClass(), spell)

        self.castSpell(charObj, spellObj, target)

    def do_catalog(self, line):
        ''' info - get the catalog of items from a vendor '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == 'Shop':
            self.selfMsg("You can't do that here.  Find a vendor\n")
            return(False)
        if not roomObj.isVendor():
            self.selfMsg("You can't do that here.  Find a vendor\n")
            return(False)

        # display # list by iterating, loading, & displaying objs
        itemBuf = ''
        for num, oneitem in enumerate(roomObj.getcatalog()):
            oType, oNum = oneitem.split('/')
            obj1 = ObjectFactory(oType, oNum)
            obj1.load()
            # calculate price
            price = self.gameObj.calculateObjectPrice(charObj, obj1)
            ROW_FORMAT = "  ({0:2}) {1:<7} {2:<60}\n"
            itemBuf += ROW_FORMAT.format(num, price, obj1.describe())
        if itemBuf != '':
            self.selfMsg("Catalog of items for sale\n" +
                         ROW_FORMAT.format('#', 'Price', 'Description') +
                         itemBuf)

    def do_circle(self, line):
        ''' combat '''
        target = self.getCombatTarget(line)
        if not target:
            return(False)

        self.gameObj.attackCreature(self.charObj, target,
                                    self.lastcmd.split(" ", 1)[0])
        return(False)

    def do_climb(self, line):
        ''' alias - go '''
        if line == '':
            self.selfMsg(self.lastcmd + " what?\n")
        self.move(line)

    def do_clock(self, line):
        ''' info - time '''
        self.selfMsg(dateStr('now') + "\n")

    def do_close(self, line):
        ''' close a door or container '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        itemList = self.getObjFromCmd(roomObj.getInventory(), line)

        if not itemList[0]:
            self.selfMsg("usage: close <item> [number]\n")
            return(False)

        targetObj = itemList[0]

        if not targetObj.isClosable(charObj):
            self.selfMsg("This is not closable!\n")
            return(False)

        if targetObj.close():
            self.selfMsg("Ok\n")
            if targetObj.gettype() == "Door":
                self.gameObj.modifyCorrespondingDoor(targetObj)
            return(False)
        else:
            self.selfMsg("You can not close" +
                         targetObj.describe(article="The") + "\n")

        return(False)

    def do_d(self, line):
        ''' navigation '''
        self.move(self._lastinput[0])  # pass first letter

    def do_debug(self, line):
        ''' dm - show raw debug info abot an item/room/character/etc '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not charObj.isDm():
            self.selfMsg("Unknown Command\n")
            return(False)

        if len(cmdargs) == 0:
            self.selfMsg("usage: debug <room | self | object>")
            return(False)

        buf = ''
        if cmdargs[0].lower() == 'room':
            buf += ('=== Debug Info for Room ' +
                    str(roomObj.getId()) + " ===\n")
            buf += roomObj.debug() + '\n'
        elif cmdargs[0].lower() == 'game':
            buf += ('=== Debug Info for game ===\n')
            buf += self.gameObj.debug() + '\n'
        elif cmdargs[0].lower() == 'self':
            buf += ('=== Debug Info for Self ' +
                    str(charObj.getId()) + " ===\n")
            buf += charObj.debug() + '\n'
        else:
            itemList = self.getObjFromCmd(roomObj.getCharsAndInventory() +
                                          charObj.getInventory(), line)
            if itemList[0]:
                buf += ('=== Debug Info for Object ' +
                        str(itemList[0].getId()) + " ===\n")
                buf += itemList[0].debug() + '\n'
        self.selfMsg(buf)
        return(None)

    def do_deposit(self, line):
        ''' transaction - make a deposit in the bank '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == 'Shop':
            self.selfMsg("You can't do that here.  Find a bank\n")
            return(False)
        if not roomObj.isBank():
            self.selfMsg("You can't do that here.  Find a bank\n")
            return(False)

        if len(cmdargs) < 1 or not isIntStr(cmdargs[0]):
            self.selfMsg("usage: deposit <amount>\n")
            return(False)
        # check if player has the funds
        amount = int(cmdargs[0])
        if not charObj.canAffordAmount(amount):
            self.selfMsg(roomObj.getCantAffordTxt(amount))
            return(False)

        taxRate = roomObj.getTaxRate()
        bankfee, dAmount = charObj.calculateBankFees(amount, taxRate)
        prompt = ("You are about to deposit " + str(amount) +
                  " shillings into the bank.\n")
        if taxRate != 0:
            prompt += ("The bank charges " +
                       "a " + str(taxRate) +
                       "% deposit fee which comes to a " +
                       str(bankfee) + " shilling charge.\n" +
                       "Your account will increase by " +
                       str(dAmount) + " shillings.\n")
        prompt += "Continue?"
        if self.client.promptForYN(prompt):
            charObj.bankDeposit(amount, taxRate)
            roomObj.recordTransaction("deposit/" + str(dAmount))
            roomObj.recordTransaction("fees/" + str(bankfee))
            self.selfMsg(roomObj.getSuccessTxt())
            return(False)
        else:
            self.selfMsg(roomObj.getAbortedTxt())
            return(False)

    def do_destroy(self, line):
        ''' dm - destroy an object or creature '''
        if not self.charObj.isDm():
            self.selfMsg("Unknown Command\n")
            return(False)

        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomObjList = self.getObjFromCmd(roomObj.getInventory(), line)
        if roomObjList[0]:
            roomObj.removeObject(roomObjList[0])
            self.selfMsg("ok\n")
            return(False)

        charObjList = self.getObjFromCmd(charObj.getInventory(), line)
        if charObjList[0]:
            roomObj.removeFromInventory(charObjList[0])
            self.selfMsg("ok\n")
            return(False)

    def do_dminfo(self, line):
        ''' dm - show char info that isn't directly avaliable to players '''
        if not self.charObj.isDm():
            return(False)
        self.selfMsg(self.charObj.dmInfo())

    def do_dm_on(self, line):
        ''' admin - Turn DM mode on '''
        if self.acctObj.isAdmin():
            self.charObj.setDm()
            self.selfMsg("ok\n")

    def do_dm_off(self, line):
        ''' dm - turn dm mode off '''
        if self.charObj.isDm():
            self.charObj.removeDm()
            self.selfMsg("ok\n")
        else:
            self.selfMsg("Unknown Command\n")

    def do_down(self, line):
        ''' navigation '''
        self.move(self._lastinput[0])  # pass first letter

    def do_draw(self, line):
        ''' alias - use '''
        return(self.do_use(line))

    def do_drink(self, line):
        ''' alias - use '''
        return(self.do_use(line))

    def do_drop(self, line):
        ''' drop an item '''

        charObj = self.charObj
        roomObj = charObj.getRoom()

        charObjList = charObj.getInventory()

        targetList = self.getObjFromCmd(charObjList, line)

        if not targetList[0]:
            self.selfMsg("What are you trying to drop?\n")
            return(False)

        if charObj.removeFromInventory(targetList[0]):
            roomObj.addObject(targetList[0])
            self.selfMsg("Ok\n")
        else:
            self.selfMsg("Didn't work\n")

    def do_e(self, line):
        ''' navigation '''
        self.move(self._lastinput[0])  # pass first letter

    def do_east(self, line):
        ''' navigation '''
        self.move(self._lastinput[0])  # pass first letter

    def do_echo(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_enter(self, line):
        ''' alias - go '''
        if line == '':
            self.selfMsg(self.lastcmd + " what?\n")
        self.move(line)

    def do_equip(self, line):
        ''' alias - use '''
        return(self.do_use(line))

    def do_examine(self, line):
        ''' alias - look '''
        return(self.do_look(line))

    def do_exit(self, line):
        ''' exit game - returns True to exit command loop '''
        return(True)

    def do_exp(self, line):
        self.selfMsg(self.charObj.expInfo())

    def do_experience(self, line):
        ''' info - show character's exp info '''
        self.selfMsg(self.charObj.expInfo())

    def do_feint(self, line):
        ''' combat '''
        target = self.getCombatTarget(line)
        if not target:
            return(False)

        self.gameObj.attackCreature(self.charObj, target,
                                    self.lastcmd.split(" ", 1)[0])
        return(False)

    def do_file(self, line):
        ''' info - show characters attached to account '''
        self.selfMsg(self.acctObj.showCharacterList())

    def do_follow(self, line):
        ''' follow another player - follower is moved when they move '''
        self.selfMsg(line + " not implemented yet\n")

    def do_full(self, line):
        ''' set the prompt and room descriptions to maximum verbosity '''
        self.charObj.setPromptSize("full")

    def do_get(self, line):
        ''' pick up an item '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        itemList = self.getObjFromCmd(roomObj.getInventory(), line)

        obj1 = itemList[0]
        obj2 = itemList[1]

        if not obj1:
            self.selfMsg(self.lastcmd + " what?\n")
            return(False)

        if obj2:
            # todo: check if we're getting item from a chest
            pass

        if not obj1.isCarryable():
            self.selfMsg(obj1.describe() + " can not be carried.\n")
            return(False)

        if not charObj.canCarryAdditionalWeight(obj1.getWeight()):
            self.selfMsg("You are not strong enough.\n")
            return(False)

        guardingCreatureObj = roomObj.getGuardingCreature()
        if guardingCreatureObj:
            self.selfMsg(guardingCreatureObj.describe() +
                         " blocks you from taking that.\n")
            return(False)

        roomObj.removeObject(obj1)
        charObj.addToInventory(obj1)
        self.selfMsg("Ok\n")

    def do_go(self, line):
        ''' go through a door or portal '''
        if line == '':
            self.selfMsg("Go where?\n")
        self.move(line)

    def do_goto(self, line):
        ''' dm - teleport directly to a room '''
        cmdargs = line.split(' ')
        charObj = self.charObj

        if not self.charObj.isDm():
            self.selfMsg("Unknown Command\n")
            return(False)

        if len(cmdargs) == 0:
            self.selfMsg("usage: goto <room>\n")
            return(False)

        self.gameObj.joinRoom(cmdargs[0], charObj)
        self.selfMsg(charObj.getRoom().display(charObj))

    def do_h(self, line):
        ''' alias - health '''
        charObj = self.charObj
        self.selfMsg(charObj.healthInfo())

    def do_hea(self, line):
        ''' alias - health '''
        charObj = self.charObj
        self.selfMsg(charObj.healthInfo())

    def do_health(self, line):
        ''' info - show character's health '''
        charObj = self.charObj
        self.selfMsg(charObj.healthInfo())

    def do_help(self, line):
        ''' info - enter the help system '''
        enterHelp(self.client)

    def do_hide(self, line):
        ''' attempt to hide player or item
            * hidden players aren't attacked by creatures and don't show
              up in room listings unless they are searched for.
            * hidden items don't show up in room listings. '''
        # cmdargs = line.split(' ')
        charObj = self.charObj

        if line == '':
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
            self.selfMsg(msg + '\n')
        else:
            self.selfMsg(line + " not implemented yet\n")

    def do_hint(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_hit(self, line):
        ''' combat '''
        target = self.getCombatTarget(line)
        if not target:
            return(False)

        self.gameObj.attackCreature(self.charObj, target,
                                    self.lastcmd.split(" ", 1)[0])
        return(False)

    def do_hold(self, line):
        ''' alias - use '''
        return(self.do_use(line))

    def do_identify(self, line):
        ''' info - Show detailed information about a item or character
            * this is considered a limited use spell '''
        self.selfMsg(line + " not implemented yet\n")

    def do_info(self, line):
        ''' alias - information '''
        self.selfMsg(self.charObj.getInfo())

    def do_information(self, line):
        ''' info - show all information about a character to that character '''
        self.selfMsg(self.charObj.getInfo())

    def do_inv(self, line):
        ''' alias - inventory '''
        self.selfMsg(self.charObj.inventoryInfo())

    def do_inventory(self, line):
        ''' info - show items that character is carrying '''
        self.selfMsg(self.charObj.inventoryInfo())

    def do_kill(self, line):
        ''' combat '''
        target = self.getCombatTarget(line)
        if not target:
            return(False)

        self.gameObj.attackCreature(self.charObj, target,
                                    self.lastcmd.split(" ", 1)[0])
        return(False)

    def do_laugh(self, line):
        ''' communication - reaction '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        self.gameObj.roomMsg(roomObj, charObj.getName() +
                             " falls down laughing\n")
        charObj.setHidden(False)

    def do_list(self, line):
        ''' alias - file '''
        return(self.do_catalog())

    def do_lock(self, line):
        ''' lock an object with a key '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomObjList = roomObj.getInventory()
#        fullObjList = charObj.getInventory() + roomObjList

        itemList = self.getObjFromCmd(roomObjList, line)

        obj1 = itemList[0]
        obj2 = itemList[1]

        if not itemList[0]:
            self.selfMsg(self.lastcmd + " what?\n")
            return(False)

        if not obj2:
            self.selfMsg("You can't lock anything without a key\n")
            return(False)
        if not obj1.isLockable():
            self.selfMsg("This is not lockable!\n")
            return(False)
        self.selfMsg("Not implemented yet.\n")
        return(False)

    def do_look(self, line):
        ''' examine a creature, object, or player
            * includes items in both the room and in the character inventory
        '''
        roomObj = self.charObj.getRoom()

        allItems = roomObj.getCharsAndInventory() + self.charObj.getInventory()
        itemList = self.getObjFromCmd(allItems, line)

        if line == '':  # display the room
            msg = roomObj.display(self.charObj)
            if not re.match("\n$", msg):
                msg += "\n"
            self.selfMsg(msg)
            return(False)

        if not itemList[0]:
            self.selfMsg("You must be blind because you " +
                         "don't see that here\n")
            return(False)

        self.selfMsg(itemList[0].examine() + "\n")  # display the object
        return(False)

    def do_lose(self, line):
        ''' attempt to ditch someone that is following you '''
        self.selfMsg(line + " not implemented yet\n")

    def do_lunge(self, line):
        ''' combat '''
        target = self.getCombatTarget(line)
        if not target:
            return(False)

        self.gameObj.attackCreature(self.charObj, target,
                                    self.lastcmd.split(" ", 1)[0])
        return(False)

    def do_n(self, line):
        ''' navigation '''
        self.move(self._lastinput[0])  # pass first letter

    def do_north(self, line):
        ''' navigation '''
        self.move(self._lastinput[0])  # pass first letter

    def do_now(self, line):
        ''' alias - clock '''
        return(self.do_clock())

    def do_o(self, line):
        ''' navigation '''
        self.move(self._lastinput[0])  # pass first letter

    def do_offer(self, line):
        ''' transaction - offer player money/items [in return for $/items] '''
        self.selfMsg(self.lastcmd + " not implemented yet\n")

    def do_open(self, line):
        ''' Open a door or a chest '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        itemList = self.getObjFromCmd(roomObj.getInventory(), line)

        if not itemList[0]:
            self.selfMsg(self.lastcmd + " what?\n")
            return(False)

        obj1 = itemList[0]

        if not obj1.isOpenable(charObj):
            self.selfMsg("You can't open that.\n")
            return(False)

        if obj1.open(charObj):
            self.selfMsg("It opens.")
            self.othersMsg(roomObj, charObj.getName() + " opens the " +
                           obj1.getSingular(), charObj.isHidden() + '\n')
            if obj1.gettype() == "Door":
                self.gameObj.modifyCorrespondingDoor(obj1)
            return(False)
        else:
            self.selfMsg("You fail to open the door.\n")
        return(False)

    def do_out(self, line):
        ''' navigation '''
        self.move(self._lastinput[0])  # pass first letter

    def do_panic(self, line):
        ''' alias - run '''
        self.selfMsg(line + " not implemented yet\n")

    def do_parley(self, line):
        ''' communication - talk to a npc '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomCreatureList = roomObj.getCreatureList()
        itemList = self.getObjFromCmd(roomCreatureList, line)

        if not itemList[0]:
            self.selfMsg(self.lastcmd + " with whom?\n")
            return(False)

        creat1 = itemList[0]

        msg = creat1.getParleyTxt() + '\n'
        if creat1.getParleyAction().lower() == "teleport":
            self.selfMsg(msg)
            self.gameObj.joinRoom(creat1.getParleyTeleportRoomNum(), charObj)
        elif creat1.getParleyAction().lower() == "sell":
            saleItem = creat1.getParleySaleItem()
            if saleItem:
                price = int(saleItem.getValue() * .9)
                prompt = (msg + "  Would you like to buy " +
                          saleItem.describe() + " for " + price + "?")
                successTxt = ("It's all yours.  Don't tell anyone " +
                              "that you got it from me")
                abortTxt = "Another time, perhaps."
                self.gameObj.buyTransaction(charObj, saleItem, price, prompt,
                                            successTxt, abortTxt)
            else:
                self.selfMsg("I have nothing to sell.\n")
        else:
            self.selfMsg(msg)
        charObj.setHidden(False)

    def do_parry(self, line):
        ''' combat '''
        pass

    def do_pawn(self, line):
        ''' alias - sell '''
        return(self.do_sell(list))

    def do_picklock(self, line):
        ''' attempt to pick the lock on a door or container and open it '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        itemList = self.getObjFromCmd(roomObj.getInventory(), line)

        if not itemList[0]:
            self.selfMsg("pick which item with a lock?\n")
            return(False)

        obj1 = itemList[0]

        if not obj1.isPickable():
            self.selfMsg("You can't pick that.\n")
            return(False)

        if obj1.pick(charObj):
            self.selfMsg("You pick the lock.\n")
            self.othersMsg(roomObj, charObj.getName() + " picks the " +
                           "lock on the " + obj1.getSingular() + '\n',
                           charObj.isHidden())
            return(False)
        else:
            self.selfMsg("You fail to pick the lock.\n")
            self.othersMsg(roomObj, charObj.getName() +
                           " fails to pick the lock on the " +
                           obj1.getSingular() + '\n', charObj.isHidden())
            return(False)
        return(False)

    def do_prompt(self, line):
        ''' set verbosity '''
        self.charObj.setPromptSize('')

    def do_purse(self, line):
        ''' info - display money '''
        charObj = self.charObj
        self.selfMsg(charObj.financialInfo())

    def do_put(self, line):
        ''' place an item in a container '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        charObjList = charObj.getInventory()

        targetList = self.getObjFromCmd(charObjList, line)

        if not targetList[0]:
            self.selfMsg(self.lastcmd + " what?\n")
            return(False)

        obj1 = targetList[0]
        obj2 = targetList[1]

        if roomObj or obj1 or obj2:  # tmp - delete when implemented
            pass

        self.selfMsg("'put' not implemented yet\n")

    def do_quit(self, line):
        ''' quit the game '''
        return(self.do_exit(line))

    def do_read(self, line):
        ''' magic - read a scroll to get the chant '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        charObjList = charObj.getInventory()

        targetList = self.getObjFromCmd(charObjList, line)

        if not targetList[0]:
            self.selfMsg(self.lastcmd + " what?\n")
            return(False)

        obj1 = targetList[0]
        obj2 = targetList[1]

        if roomObj or obj1 or obj2:  # tmp - delete when implemented
            pass

        self.selfMsg("'read' not implemented yet\n")

    def do_remove(self, line):
        ''' unequip an item that you have equipped '''
        return(self.do_unequip(line))

    def do_repair(self, line):
        ''' transaction - repair character's item in a repair shop '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == 'Shop':
            self.selfMsg("You can't do that here.  Find a wright\n")
            return(False)
        if not roomObj.isRepairShop():
            self.selfMsg("You can't do that here.  Find a wright\n")
            return(False)

        if len(cmdargs) < 1 or not isIntStr(cmdargs[0]):
            self.selfMsg("usage: repair <item> [#]\n")

        playerInventory = charObj.getInventory()
        itemList = self.getObjFromCmd(playerInventory, line)

        if not itemList[0]:
            self.selfMsg(self.lastcmd + " what?\n")
            return(False)

        obj1 = itemList[0]

        if not obj1.canBeRepaired():
            self.selfMsg("This can't be repaired\n")
            return(False)

        price = self.gameObj.calculateObjectPrice(charObj, obj1) * 100
        prompt = ("You are about to repair " + obj1.getArticle() + " " +
                  obj1.getName() + " for " + str(price) +
                  " shillings.  Proceed?")
        if self.client.promptForYN(prompt):
            obj1.repair()
            roomObj.recordTransaction(obj1)
            roomObj.recordTransaction("repair/" + str(price))
            charObj.recordTax(roomObj.getTaxAmount(price))
            self.selfMsg(roomObj.getSuccessTxt())
            return(False)
        else:
            self.selfMsg(roomObj.getAbortedTxt())
            return(False)

    def do_return(self, line):
        ''' alias - unequip '''
        return(self.do_unequip())

    def do_roominfo(self, line):
        '''' dm - show room info '''
        if not self.charObj.isDm():
            self.selfMsg("Unknown Command\n")
            return(False)
        self.selfMsg(self.charObj.getRoom().getInfo())

    def do_run(self, line):
        ''' drop weapon and escape room in random direction '''
        self.selfMsg(line + " not implemented yet\n")

    def do_s(self, line):
        ''' navigation '''
        self.move(self._lastinput[0])  # pass first letter

    def do_save(self, line):
        ''' save character '''
        if self.client.charObj.save():
            self.selfMsg("Saved\n")
        else:
            self.selfMsg("Could not save\n")

    def do_say(self, line):
        ''' communication within room '''
        msg = self.client.promptForInput()
        self.gameObj.roomMsg(self.charObj.roomObj, msg)
        self.charObj.setHidden(False)

    def do_search(self, line):
        ''' attempt to find items, players, or creatures that are hidden '''
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
        ''' transaction - Sell an item to a pawnshop '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == 'Shop':
            self.selfMsg("You can't do that here.  Find a fence\n")
            return(False)
        if not roomObj.isPawnShop():
            self.selfMsg("You can't do that here.  Find a fence.\n")
            return(False)

        itemList = self.getObjFromCmd(charObj.getInventory(), line)
        if not itemList[0]:
            self.selfMsg(self.lastcmd + " what?\n")
            return(False)

        obj1 = itemList[0]

        price = int(self.gameObj.calculateObjectPrice(charObj, obj1) * .8)

        # prompt player for confirmation
        prompt = ("You are about to pawn " + obj1.getArticle() +
                  " " + obj1.getName() + " for " + str(price) +
                  " shillings.  Proceed?")
        self.gameObj.sellTransaction(charObj, obj1, price, prompt,
                                     roomObj.getSuccessTxt(),
                                     roomObj.getAbortedTxt())

    def do_send(self, line):
        ''' communication - direct message to another player '''
        msg = self.client.promptForInput()
        self.gameObj.gameMsg(msg)
        return(False)

    def do_shout(self, line):
        ''' communication - talk to players in room and adjoining rooms '''
        msg = self.client.promptForInput()
        self.yellMsg(self.charObj.roomObj, msg)

    def do_skills(self, line):
        ''' info - show character's skills '''
        self.selfMsg(self.charObj.SkillsInfo())

    def do_slay(self, line):
        ''' dm - combat - do max damage to creature, effectively killing it '''
        target = self.getCombatTarget(line)
        if not target:
            return(False)

        if self.charObj.isDm():
            atkcmd = 'slay'
        else:
            atkcmd = 'attack'  # if your not a dm, this is a standard attack

        self.gameObj.attackCreature(self.charObj, target, atkcmd)

        return(False)

    def do_smash(self, line):
        ''' attempt to open a door/chest with brute force '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        itemList = self.getObjFromCmd(roomObj.getInventory(), line)

        if not itemList[0]:
            self.selfMsg(self.lastcmd + " what?\n")
            return(False)

        obj1 = itemList[0]

        if not obj1.isSmashable():
            self.selfMsg("This is not smashable!\n")
            return(False)

        if obj1.smash(charObj):
            self.othersMsg(roomObj, charObj.getName() + " smashes the " +
                           obj1.getSingular() + " open.\n")
            self.selfMsg("You smash it open!\n")
            otherRoom = self.gameObj.getCorrespondingRoomObj(obj1)
            if otherRoom:
                self.gameObj.roomMsg(otherRoom, obj1.getSingular() +
                                     " smashes open\n")
            if obj1.gettype() == "Door":
                self.gameObj.modifyCorrespondingDoor(obj1)
            return(False)
        else:
            self.othersMsg(roomObj, charObj.getName() +
                           " fails to smash " + obj1.describe() + " open.\n")
            self.selfMsg("Bang! You fail to smash it open!\n")
            otherRoom = self.gameObj.getCorrespondingRoomObj(obj1)
            if otherRoom:
                self.gameObj.roomMsg(otherRoom, "You hear a noise on the " +
                                     "other side of the " +
                                     obj1.getSingular() + '\n')
        return(False)

    def do_south(self, line):
        ''' navigation '''
        self.move(self._lastinput[0])  # pass first letter

    def do_stats(self, line):
        ''' info - show character's stats '''
        self.selfMsg(self.charObj.StatsInfo())

    def do_status(self, line):
        ''' alias - health '''
        return(self.do_health())

    def do_steal(self, line):
        ''' transaction - attempt to steal from another player '''
        self.selfMsg(line + " not implemented yet\n")

    def do_strike(self, line):
        ''' combat '''
        target = self.getCombatTarget(line)
        if not target:
            return(False)

        self.gameObj.attackCreature(self.charObj, target,
                                    self.lastcmd.split(" ", 1)[0])
        return(False)

    def do_suicide(self, line):
        if not self.client.promptForYN("DANGER: This will permanently " +
                                       "delete your character." +
                                       "  Are you sure?"):
            return(False)
        charObj = self.charObj
        charName = charObj.getName()
        self.gameObj.leaveGame(self.client, saveChar=False)
        msg = self.client.txtBanner(charName +
                                    ' has shuffled off this mortal coil',
                                    bChar='=')
        charObj.delete()
        charObj = None
        self.charObj = None
        self.acctObj.removeCharacterFromAccount(charName)
        self.gameObj.gameMsg(msg)
        logging.info("Character deleted: " + charName)
        return(True)

    def do_take(self, line):
        ''' alias - get '''
        return(self.do_get(line))

    def do_talk(self, line):
        ''' alias - parley '''
        return(self.do_parley(line))

    def do_teach(self, line):
        ''' teach another player a spell '''
        self.selfMsg(line + " not implemented yet\n")

    def do_toggle(self, line):
        ''' dm command to set flags '''
        if self.charObj.isDm():
            if ((line.lower() == "character" or line.lower() == "char" or
                 line.lower() == "self")):
                obj = self.charObj
            elif line.lower() == "room":
                obj = self.charObj.getRoom()
            elif line.lower() == "game":
                obj = self.gameObj
            elif line.lower() == "client":
                obj = self.client
            else:
                roomObj = self.charObj.getRoom()
                itemList = self.getObjFromCmd(roomObj.getCharsAndInventory(),
                                              line)
                if itemList[0]:
                    obj = itemList[0]
                else:
                    self.selfMsg("Can't toggle " + line + '\n')
                    return(False)
        else:
            self.selfMsg("Unknown Command\n")
            return(False)

        obj.toggleInstanceDebug()
        self.selfMsg("Toggled " + line + ": debug=" +
                     str(obj.getInstanceDebug()) + '\n')
        return(False)

    def do_thrust(self, line):
        ''' combat '''
        target = self.getCombatTarget(line)
        if not target:
            return(False)

        self.gameObj.attackCreature(self.charObj, target,
                                    self.lastcmd.split(" ", 1)[0])
        return(False)

    def do_track(self, line):
        ''' show direction last player traveled '''
        self.selfMsg(line + " not implemented yet\n")

    def do_train(self, line):
        ''' increase level if exp and location allow '''
        self.selfMsg(line + " not implemented yet\n")

    def do_turn(self, line):
        ''' magic - chance for clerics/paladins to destroy creatures '''
        self.selfMsg(line + " not implemented yet\n")

    def do_u(self, line):
        ''' navigation '''
        self.move(self._lastinput[0])  # pass first letter

    def do_unequip(self, line):
        ''' stop using a piece of equiptment '''
        charObj = self.charObj

        targetList = self.getObjFromCmd(charObj.getInventory(), line)

        if not targetList[0]:
            self.selfMsg(self.lastcmd + " what?\n")
            return(False)
        elif len(targetList) > 0:
            obj1 = targetList[0]
        else:
            obj1 = None

        if charObj.unEquip(obj1):
            self.selfMsg("Ok\n")
        else:
            self.selfMsg("You can't do that\n")

    def do_unlock(self, line):
        ''' unlock a door/chest with a key '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        itemList = self.getObjFromCmd(roomObj.getInventory(), line)

        if not itemList[0]:
            self.selfMsg(self.lastcmd + " what?\n")
            return(False)

        obj1 = itemList[0]
        obj2 = itemList[1]

        if not obj2:
            self.selfMsg("You need a key before you can unlock anything\n")
        if not obj1.isUnlockable():
            self.selfMsg("You can't unlock that.\n")
            return(False)
        # need to get lock ID and see if the given key matches
        # if keys have charges, we need to modify key
        if obj1.unlock(charObj):
            self.selfMsg("You unlock the lock.\n")
            self.othersMsg(roomObj, charObj.getName() + " unlocks the " +
                           "lock on the " + obj1.getSingular() + '\n',
                           charObj.isHidden())
            return(False)
        else:
            self.selfMsg("You fail to unlock the lock.\n")
            self.othersMsg(roomObj, charObj.getName() + " fails to " +
                           "unlock the lock on the " +
                           obj1.getSingular() + '\n', charObj.isHidden())
            return(False)
        return(False)

    def do_up(self, line):
        ''' navigation '''
        self.move(self._lastinput[0])  # pass first letter

    def do_use(self, line):
        ''' equip an item or use a scroll or magic item '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        charObjList = charObj.getInventory()

        targetList = self.getObjFromCmd(charObjList, line)

        if not targetList[0]:
            self.selfMsg(self.lastcmd + "what?\n")
            return(False)

        obj1 = targetList[0]
        obj2 = targetList[1]

        if obj1.isEquippable():
            if charObj.equip(obj1):
                self.selfMsg("Ok\n")
            else:
                self.selfMsg("You can't do that\n")
        elif isinstance(obj1, Scroll):
            self.gameObj.use_scroll(charObj, obj1, obj2)
        elif obj1.isMagicItem():
            self.gameObj.use_magicitem(charObj, obj1, obj2)

        if roomObj:  # tmp - remove later if room object is not needed here
            pass     # but there may be spells/items that affect the room.

    def do_w(self, line):
        ''' navigation '''
        self.move(self._lastinput[0])  # pass first letter

    def do_wear(self, line):
        ''' alias - use '''
        return(self.do_use(line))

    def do_west(self, line):
        ''' navigation '''
        self.move(self._lastinput[0])  # pass first letter

    def do_where(self, line):
        ''' alias - look '''
        return(self.do_look(line))

    def do_whisper(self, line):
        ''' communication - char to char, with chance of being overheard '''
        cmdargs = line.split(' ')
        if not cmdargs[0]:
            self.selfMsg("usage: whisper <playerName>\n")
            return(False)
        msg = self.client.promptForInput()
        self.gameObj.directMsg(cmdargs[0], msg)  # wrong method for this??
        recieved = False

        for oneChar in self.charObj.getRoom().getCharacterList():
            if re.match(cmdargs[0], oneChar.getName()):   # if name matches
                oneChar.client.spoolOut(msg)            # notify
                recieved = True
            else:
                if oneChar.hearsWhispers():
                    oneChar.client.spoolOut("You overhear " +
                                            self.charObj.getName() +
                                            ' whisper ' + msg + '\n')
                    self.charObj.setHidden(False)
        return(recieved)

    def do_who(self, line):
        ''' info - show who is playing the game '''
        charTxt = ''
        charObj = self.charObj
        for onechar in charObj.getRoom().getCharacterList():
            if onechar != charObj:
                charTxt += onechar.getName() + '\n'
        if charTxt == '':
            buf = "You are the only one online\n"
        else:
            buf = "Characters in the Game:\n" + charTxt
        self.selfMsg(buf)
        return(None)

    def do_wield(self, line):
        ''' alias - use '''
        return(self.do_use(line))

    def do_withdraw(self, line):
        ''' transaction - take money out of the bank '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == 'Shop':
            self.selfMsg("You can't do that here.  Find a bank\n")
            return(False)
        if not roomObj.isBank():
            self.selfMsg("You can't do that here.  Find a bank\n")
            return(False)

        if len(cmdargs) < 1 or not isIntStr(cmdargs[0]):
            self.selfMsg("usage: withdraw <amount>\n")
            return(False)
        amount = int(cmdargs[0])
        if not charObj.canWithdraw(amount):
            self.selfMsg(roomObj.getCantAffordTxt(amount))
            return(False)
        taxRate = roomObj.getTaxRate()
        bankfee, wAmount = charObj.calculateBankFees(amount,
                                                     taxRate)
        prompt = ("You are about to withdraw " + str(amount) +
                  " shillings from the bank.\n")
        if taxRate != 0:
            prompt += ("The bank charges a " + str(taxRate) +
                       "% withdrawl fee which comes to a charge of " +
                       str(bankfee) + "shillings.\n" +
                       "As a result, you will receive " + str(wAmount) +
                       " shillings.\n")
        prompt += "Continue?"
        if self.client.promptForYN(prompt):
            charObj.bankWithdraw(amount, taxRate)
            roomObj.recordTransaction("withdrawl/" + str(wAmount))
            roomObj.recordTransaction("fees/" + str(bankfee))
            self.selfMsg(roomObj.getSuccessTxt())
            return(False)
        else:
            self.selfMsg(roomObj.getAbortedTxt())
            return(False)

    def do_yell(self, line):
        ''' communication - all in room and adjoining rooms '''
        msg = self.client.promptForInput()
        self.yellMsg(self.charObj.roomObj, msg)


# instanciate the _Game class
_game = _Game()


def Game():
    ''' return a reference to the single, existing _game instance
        Thus, when we try to instanciate Game, we are just returning
        a ref to the existing Game '''

    return(_game)
