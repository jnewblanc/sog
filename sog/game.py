''' game class '''  # noqa

# We want only one implementation of the Game Class.
# To do this, create a single instance of the Game class on import.  Then
# each time we try to instanciate Game(), we just return a reference to
# the game class.

import cmd
from datetime import datetime
import logging
import re

from common.general import isIntStr, dateStr, dLog
from common.general import splitCmd, itemSearch, targetSearch
from help import enterHelp
from room import RoomFactory
from object import ObjectFactory
# from object import Potion, Scroll, Teleport, Staff
from object import Scroll
from character import Character
from creature import Creature
from magic import Spell


class _Game(cmd.Cmd):
    ''' Single instance of the Game class, shared by all users
        (see instanciation magic at the bottom of the file)'''

    debugGame = False

    def __init__(self):
        ''' game-wide attributes '''
        self.instance = "Instance at %d" % self.__hash__()
        self._activeRooms = []
        self._characterList = []
        self._startdate = datetime.now()
        return(None)

    def joinGame(self, svrObj):
        ''' Perform required actions related to joining the game '''
        charObj = svrObj.charObj
        if not charObj:
            logging.warn("Game: Character not defined - returning False")
            return(False)

        gameCmd = GameCmd(svrObj)      # each user gets their own cmd shell

        # in-game broadcast announcing game entry
        msg = svrObj.txtBanner(charObj.getName() +
                               ' has entered the game', bChar='=')
        self.gameMsg(msg)

        self.addCharacterToGame(charObj)

        # add room to charObj and then display the room
        if self.joinRoom(1, charObj):
            gameCmd.selfMsg(charObj.getRoom().display(charObj))
            try:
                gameCmd.cmdloop()           # start the game cmdloop
            finally:
                svrObj.charObj.save()
                self.leaveRoom(svrObj.charObj)
                self.leaveGame(svrObj)
        return(False)

    def leaveGame(self, svrObj):
        ''' Handle details of leaving a game '''
        self.removeCharacterFromGame(svrObj.charObj)
        svrObj.charObj.save(logStr=__class__.__name__)
        msg = svrObj.txtBanner(svrObj.charObj.getName() +
                               ' has left the game', bChar='=')
        svrObj.charObj = None
        self.gameMsg(msg)
        logging.info(msg)
        return(True)

    def getCharacterList(self):
        return(self._characterList)

    def gameMsg(self, msg):
        ''' shown to everyone in the game '''
        for oneChar in self.getCharacterList():
            oneChar.svrObj.spoolOut(msg)

    def directMsg(self, charName, msg):
        ''' show only to specified user '''
        recieved = False
        if not charName:
            return(False)

        for oneChar in self.getCharacterList():         # get chars in game
            if re.match(charName, oneChar.getName()):   # if name matches
                oneChar.svrObj.spoolOut(msg)            # notify
                recieved = True
        return(recieved)

    def addCharacterToGame(self, charObj):
        ''' add character to list of characters in game '''
        if charObj not in self.getCharacterList():
            self._characterList.append(charObj)

    def removeCharacterFromGame(self, charObj):
        ''' remove character to list of characters in game '''
        if charObj in self.getCharacterList():
            self._characterList.remove(charObj)

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

    def joinRoom(self, roomStr, charObj):
        ''' insert player into a room
            * create or join room instance
            * add character to room instance
            * add room to character instance
            * add room to active rooms list
            * close spring loaded doors if room is empty
            # roomStr can be a room number or can be in the form Shop/35
        '''
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
                return(False)
        else:
            logging.error("Room number " + str(roomNum) + ' is invalid\n')
            return(False)

        # See if room is already active
        for oneroom in self.getActiveRoomList():
            if oneroom.getRoomNum() == roomNum:  # if the room alread exists
                logging.debug(charObj.getName() + " joined existing room " +
                              str(roomNum))
                roomObj = oneroom             # use existing roomObj

        if not roomObj:
            roomObj = RoomFactory(roomType, roomNum)  # instanciate room object
            roomObj.load(logStr=__class__.__name__)  # load room from disk
            logging.debug(charObj.getName() + " spun up room " + str(roomNum))

        if charObj.getRoom():
            if charObj.getRoom() == roomObj:    # if already in desired room
                pass                            # do nothing
            else:
                self.leaveRoom(charObj)         # leave the previous room

        charObj.setRoom(roomObj)                # Add room to character
        roomObj.addCharacter(charObj)           # Add character to room
        self.addToActiveRooms(roomObj)    # Add room to active room list

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

        # if room's character list is empty, remove room from activeRoomList
        if len(charObj.getRoom().getCharacterList()) == 0:
            self.removeFromActiveRooms(charObj.getRoom())
        charObj.getRoom().removeCharacter(charObj)  # remove charact from room
        charObj.removeRoom()                       # Remove room from character
        return(True)


class GameCmd(cmd.Cmd):
    ''' Game loop - separate one for each player
        * Uses cmd loop with do_<action> methods
        * if do_ methods return True, then loop exits
    '''
    def __init__(self, svrObj=None):
        self.svrObj = svrObj
        if svrObj:
            self.acctObj = svrObj.acctObj
            self.gameObj = svrObj.gameObj
            self.charObj = svrObj.charObj
        else:
            self.acctObj = None
            self.gameObj = None
            self.charObj = None

        self._lastinput = ''

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
        ''' Game cmd loop - requires player to have character loaded '''
        stop = False
        line = ""
        self.preloop()
        while not stop:
            if self.svrObj.promptForCommand(self.getCmdPrompt()):  # send/recv
                line = self.svrObj.getInputStr()
                self._lastinput = line
                dLog("GAME cmd = " + line, self.gameObj.debugGame)
                self.precmd(line)
                stop = self.onecmd(line)
                self.postcmd(stop, line)
            else:
                stop = True
        self.postloop()

    def postcmd(self, stop, line):
        if self.charObj:  # doesn't exist if there is a suicide
            self.charObj.save(logStr=__class__.__name__)
        return(stop)

    def emptyline():
        return(False)

    def selfMsg(self, msg):
        ''' show only to yourself '''
        recieved = False
        if self.svrObj:
            self.svrObj.spoolOut(msg)
            recieved = True
        return(recieved)

    def roomMsg(self, roomObj, msg):
        ''' shown to everyone in the room '''
        recieved = False
        if not roomObj:
            return(False)

        for oneChar in roomObj.getCharacterList():
            oneChar.svrObj.spoolOut(msg)
            recieved = True
        return(recieved)

    def othersMsg(self, msg, ignore=False):
        ''' shown to others in room, but not you '''
        recieved = False
        if not self.svrObj:
            return(False)

        if ignore:             # may get set to True if player is hidden
            return(False)

        for oneChar in self.charObj.getRoom().getCharacterList():
            if oneChar != self.charObj:            # if not yourself
                oneChar.svrObj.spoolOut(msg)
                recieved = True
        return(recieved)

    def yellMsg(self, roomObj, msg):
        ''' shown to your room and rooms in adjoining directions '''
        recieved = False
        if not roomObj:
            return(False)

        exitDict = roomObj.getExits()
        for oneRoom in self.gameObj.getActiveRoomList():  # foreach active room
            if oneRoom.getId() in exitDict.keys():  # if room id is an exit
                for oneChar in oneRoom.getCharacterList():  # get chars in room
                    oneChar.svrObj.spoolOut(msg)            # notify
                    recieved = True
        return(recieved)

    def do_accept(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_appeal(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_attack(self, line):
        ''' combat '''
        self.selfMsg(line + " not implemented yet\n")

    def do_backstab(self, line):
        ''' combat '''
        self.selfMsg(line + " not implemented yet\n")

    def do_balance(self, line):
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == 'Shop':
            self.selfMsg("You can't do that here.  Find a bank\n")
            return(False)
        if not roomObj.isBank():
            self.selfMsg("You can't do that here.  Find a bank\n")
            return(False)

        amount = charObj.getBankBalance()
        self.selfMsg("Your account balance is " + str(amount) +
                     " shillings.\n")

    def do_block(self, line):
        ''' combat '''
        self.selfMsg(line + " not implemented yet\n")

    def do_break(self, line):
        return(self.do_smash(line))

    def do_bribe(self, line):
        ''' bribe a creature to vanish '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomCreatureList = roomObj.getAllCreatures()
        creatList = self.getObjFromCmd(roomCreatureList, cmdargs)

        if len(creatList) >= 1:
            creat1 = creatList[0]
        else:
            self.selfMsg("usage: parley <creature> [number]\n")

        if creat1:
            creat1.describe()  # tmp - remove once implemented
        self.selfMsg(line + " not implemented yet\n")

    def do_brief(self, line):
        self.charObj.setPromptSize("brief")

    def do_broadcast(self, line):
        pass

    def do_buy(self, line):
        ''' buy something from a vendor '''
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
            price = self.calculateObjectPrice(self.svrObj, obj1)

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
            self.buyTransaction(obj1, price, prompt, successTxt, abortTxt)

    def do_cast(self, line):
        ''' magic '''
        self.selfMsg(line + " not implemented yet\n")

    def do_catalog(self, line):
        ''' get the catalog of items from a vendor '''
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
            price = self.calculateObjectPrice(self.svrObj, obj1)
            ROW_FORMAT = "  ({0:2}) {1:<7} {2:<60}\n"
            itemBuf += ROW_FORMAT.format(num, price, obj1.describe())
        if itemBuf != '':
            self.selfMsg("Catalog of items for sale\n" +
                         ROW_FORMAT.format('#', 'Price', 'Description') +
                         itemBuf)

    def do_circle(self, line):
        ''' combat '''
        self.selfMsg(line + " not implemented yet\n")

    def do_climb(self, line):
        cmdargs = line.split(' ')

        if cmdargs[0]:
            if not self.move(self.svrObj, cmdargs):
                self.selfMsg("You can't climb that\n")
        else:
            self.selfMsg("You can't climb that\n")

    def do_clock(self, line):
        self.selfMsg(dateStr('now') + "\n")

    def do_close(self, line):
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomObjList = roomObj.getAllObjects()
#        fullObjList = charObj.getInventory() + roomObjList

        objList = self.getObjFromCmd(roomObjList, cmdargs)

        if len(objList) >= 1:
            obj1 = objList[0]
        else:
            self.selfMsg("usage: close <item> [number]\n")
            return(False)

        if not obj1.isClosable():
            self.selfMsg("This is not closable!\n")
            return(False)

        if obj1.close(charObj):
            self.selfMsg("Ok\n")
            if obj1.gettype() == "Door":
                self.modifyCorrespondingDoor(obj1)
            return(False)
        return(False)

    def do_d(self, line):
        self.move(self.svrObj, [self._lastinput[0]])  # pass first letter

    def do_debug(self, line):
        ''' dm - show raw debug info abot an item/room/character/etc '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not self.charObj.isDm():
            return(False)

        if len(cmdargs) == 0:
            self.selfMsg("usage: debug <room | self | object>")
            return(False)

        buf = ''
        if cmdargs[0].lower() == 'room':
            buf += ('=== Debug Info for Room ' +
                    str(roomObj.getId()) + " ===\n")
            buf += roomObj.debug() + '\n'
        if cmdargs[0].lower() == 'self':
            buf += ('=== Debug Info for Self ' +
                    str(charObj.getId()) + " ===\n")
            buf += charObj.debug() + '\n'
        else:
            objList = (self.getObjFromCmd(roomObj.getAllObjects(),
                       cmdargs))
            if len(objList) >= 1:
                buf += ('=== Debug Info for Object ' +
                        str(objList[0].getId()) + " ===\n")
                buf += objList[0].debug() + '\n'

    def do_deposit(self, line):
        ''' make a deposit in the bank '''
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
        if self.svrObj.promptForYN(prompt):
            charObj.bankDeposit(amount, taxRate)
            roomObj.recordTransaction("deposit/" + str(dAmount))
            roomObj.recordTransaction("fees/" + str(bankfee))
            self.selfMsg(roomObj.getSuccessTxt())
            return(False)
        else:
            self.selfMsg(roomObj.getAbortedTxt())
            return(False)

    def do_dm_on(self, line):
        ''' admin - Turn DM mode on '''
        if self.acctObj.isAdmin():
            self.charObj.setDm()
            self.selfMsg("ok")

    def do_dm_off(self, line):
        ''' dm - turn dm mode off '''
        if self.charObj.isDm():
            self.charObj.removeDm()
            self.selfMsg("ok")

    def do_dmstats(self, line):
        ''' dm - show char info that isn't directly avaliable to players '''
        if not self.charObj.isDm():
            return(False)
        self.selfMsg(self.charObj.getDmStats())

    def do_down(self, line):
        self.move(self.svrObj, [self._lastinput[0]])  # pass first letter

    def do_draw(self, line):
        return(self.do_use(line))

    def do_drink(self, line):
        return(self.do_use(line))

    def do_drop(self, line):
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        charObjList = charObj.getInventory()

        targetList = self.getObjFromCmd(charObjList, cmdargs)

        if not targetList:
            self.selfMsg("usage: drop <item> [number]\n")
            return(False)
        elif len(targetList) == 1:
            obj1 = targetList[0]
        elif len(targetList) == 2:
            obj1 = targetList[0]

        if charObj.removeFromInventory(obj1):
            roomObj.addObject(obj1)
            self.selfMsg("Ok\n")
        else:
            self.selfMsg("Didn't work\n")

    def do_e(self, line):
        self.move(self.svrObj, [self._lastinput[0]])  # pass first letter

    def do_east(self, line):
        self.move(self.svrObj, [self._lastinput[0]])  # pass first letter

    def do_echo(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_enter(self, line):
        cmdargs = line.split(' ')

        if cmdargs[0]:
            if not self.move(self.svrObj, cmdargs):
                self.selfMsg("You can't enter that\n")
        else:
            self.selfMsg("You can't enter that\n")

    def do_equip(self, line):
        return(self.do_use(line))

    def do_examine(self, line):
        return(self.do_look(line))

    def do_exit(self, line):
        ''' exit game - returns True to exit command loop '''
        return(True)

    def do_exp(self, line):
        self.selfMsg(self.charObj.expInfo())

    def do_experience(self, line):
        self.selfMsg(self.charObj.expInfo())

    def do_feint(self, line):
        ''' combat '''
        self.selfMsg(line + " not implemented yet\n")

    def do_file(self, line):
        self.selfMsg(self.acctObj.showCharacterList())

    def do_follow(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_full(self, line):
        self.charObj.setPromptSize("full")

    def do_get(self, line):
        ''' pick up an item '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomObjList = roomObj.getAllObjects()
#        fullObjList = charObj.getInventory() + roomObjList

        objList = self.getObjFromCmd(roomObjList, cmdargs)

        if len(objList) >= 1:
            obj1 = objList[0]
            if len(objList) >= 2:
                obj2 = objList[1]
        else:
            self.selfMsg("usage: get <item> [number]\n")
            return(False)

        # todo: check if we're getting item from a chest
        if obj2:
            pass

        if not obj1.isCarryable():
            self.selfMsg("That can not be carried.\n")
            return(False)

        if charObj.canCarryAdditionalWeight(obj1.getWeight()):
            roomObj.removeObject(obj1)
            charObj.addToInventory(obj1)
            self.selfMsg("Ok\n")
        else:
            self.selfMsg("You are not strong enough.\n")

    def do_go(self, line):
        cmdargs = line.split(' ')

        if cmdargs[0]:
            if not self.move(self.svrObj, cmdargs):
                self.selfMsg("You can't go there\n")
        else:
            self.selfMsg("You can't go there\n")

    def do_goto(self, line):
        ''' dm - teleport directly to a room '''
        cmdargs = line.split(' ')
        charObj = self.charObj

        if not self.charObj.isDm():
            return(False)

        if len(cmdargs) == 0:
            self.selfMsg("usage: goto <room>")
            return(False)

        self.gameObj.joinRoom(cmdargs[0], charObj)
        self.selfMsg(charObj.getRoom().display(charObj))

    def do_h(self, line):
        charObj = self.charObj
        self.selfMsg(charObj.healthInfo())

    def do_hea(self, line):
        charObj = self.charObj
        self.selfMsg(charObj.healthInfo())

    def do_health(self, line):
        charObj = self.charObj
        self.selfMsg(charObj.healthInfo())

    def do_help(self, line):
        enterHelp()

    def do_hide(self, line):
        cmdargs = line.split(' ')
        charObj = self.charObj

        if len(cmdargs) == 0:
            charObj.attemptToHide()
            self.selfMsg("You hide in the shadows\n")
        else:
            self.selfMsg(line + " not implemented yet\n")

    def do_hint(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_hit(self, line):
        ''' combat '''
        self.selfMsg(line + " not implemented yet\n")

    def do_hold(self, line):
        return(self.do_use(line))

    def do_identify(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_info(self, line):
        self.selfMsg(self.charObj.getInfo())

    def do_information(self, line):
        self.selfMsg(self.charObj.getInfo())

    def do_inv(self, line):
        self.selfMsg(self.charObj.inventoryInfo())

    def do_inventory(self, line):
        self.selfMsg(self.charObj.inventoryInfo())

    def do_kill(self, line):
        ''' combat '''
        self.selfMsg(line + " not implemented yet\n")

    def do_list(self, line):
        pass

    def do_lock(self, line):
        ''' lock an object with a key '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomObjList = roomObj.getAllObjects()
#        fullObjList = charObj.getInventory() + roomObjList

        objList = self.getObjFromCmd(roomObjList, cmdargs)

        if len(objList) >= 1:
            obj1 = objList[0]
            if len(objList) >= 2:
                obj2 = objList[1]
        else:
            self.selfMsg("usage: lock <item> [#] <key> [#]\n")
            return(False)

        if not obj2:
            self.selfMsg("usage: lock <obj> [#] <key>\n")
            return(False)
        if not obj1.isLockable():
            self.selfMsg("This is not lockable!\n")
            return(False)
        self.selfMsg("Not implemented yet.\n")
        return(False)

    def do_look(self, line):
        cmdargs = line.split(' ')
        charObj = self.charObj

        roomObj = charObj.getRoom()
        if len(cmdargs) == 0:
            self.selfMsg(roomObj.display(charObj) + "\n")
        else:
            objList = self.getObjFromCmd(roomObj.getAllObjects(), cmdargs)
            if len(objList) >= 1:
                self.selfMsg(objList[0].describe() + "\n")
            else:
                # need to handle characters and creatures
                self.selfMsg("You must be blind because you " +
                             "don't see " + line + " here\n")

    def do_lose(self, line):
        pass

    def do_n(self, line):
        self.move(self.svrObj, [self._lastinput[0]])  # pass first letter

    def do_north(self, line):
        self.move(self.svrObj, [self._lastinput[0]])  # pass first letter

    def do_now(self, line):
        pass

    def do_o(self, line):
        self.move(self.svrObj, [self._lastinput[0]])  # pass first letter

    def do_offer(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_open(self, line):
        ''' Open a door or a chest '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomObjList = roomObj.getAllObjects()
#        fullObjList = charObj.getInventory() + roomObjList

        objList = self.getObjFromCmd(roomObjList, cmdargs)

        if len(objList) >= 1:
            obj1 = objList[0]
        else:
            self.selfMsg("usage: open <item> [number]\n")
            return(False)

        if not obj1.isOpenable():
            self.selfMsg("You can't open that.\n")
            return(False)

        if obj1.open(charObj):
            self.selfMsg("It opens.")
            self.othersMsg(charObj.getName() + " opens the " +
                           obj1.getSingular(), charObj.isHidden())
            if obj1.gettype() == "Door":
                self.modifyCorrespondingDoor(obj1)
            return(False)
        else:
            self.selfMsg("You fail to open the door.")
        return(False)

    def do_out(self, line):
        self.move(self.svrObj, [self._lastinput[0]])  # pass first letter

    def do_panic(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_parley(self, line):
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomCreatureList = roomObj.getAllCreatures()
        creatList = self.getObjFromCmd(roomCreatureList, cmdargs)

        if len(creatList) >= 1:
            creat1 = creatList[0]
        else:
            self.selfMsg("usage: parley <creature> [number]\n")

        msg = creat1.getParleyTxt()
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
                self.buyTransaction(saleItem, price, prompt,
                                    successTxt, abortTxt)
            else:
                self.selfMsg("I have nothing to sell.\n")
        else:
            self.selfMsg(msg)
        charObj.setHidden(False)

    def do_parry(self, line):
        pass

    def do_pawn(self, line):
        return(self.do_sell(list))

    def do_picklock(self, line):
        ''' Process commands that are related to object manipulation '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomObjList = roomObj.getAllObjects()
#        fullObjList = charObj.getInventory() + roomObjList

        objList = self.getObjFromCmd(roomObjList, cmdargs)

        if len(objList) >= 1:
            obj1 = objList[0]
        else:
            self.selfMsg("usage: picklock <item> [number]\n")
            return(False)

        if not obj1.isPickable():
            self.selfMsg("You can't pick that.\n")
            return(False)

        if obj1.pick(charObj):
            self.selfMsg("You pick the lock.\n")
            self.othersMsg(charObj.getName() + " picks the " +
                           "lock on the " + obj1.getSingular() + '\n',
                           charObj.isHidden())
            return(False)
        else:
            self.selfMsg("You fail to pick the lock.\n")
            self.othersMsg(charObj.getName() +
                           " fails to pick the lock on the " +
                           obj1.getSingular() + '\n', charObj.isHidden())
            return(False)
        return(False)

    def do_prompt(self, line):
        ''' set verbosity '''
        self.charObj.setPromptSize('')

    def do_purse(self, line):
        ''' display money '''
        charObj = self.charObj
        self.selfMsg(charObj.financialInfo())

    def do_put(self, line):
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        charObjList = charObj.getInventory()

        targetList = self.getObjFromCmd(charObjList, cmdargs)

        if not targetList:
            self.selfMsg("usage: " + cmdargs[0] +
                         " <item> [number]\n")
            return(False)
        elif len(targetList) == 1:
            obj1 = targetList[0]
            obj2 = None
        elif len(targetList) == 2:
            obj1 = targetList[0]
            obj2 = targetList[1]

        if roomObj or obj1 or obj2:  # tmp - delete when implemented
            pass

        self.selfMsg("'put' not implemented yet\n")

    def do_quit(self, line):
        ''' quit the game '''
        return(self.do_exit(line))

    def do_read(self, line):
        ''' read a scroll to get the chant '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        charObjList = charObj.getInventory()

        targetList = self.getObjFromCmd(charObjList, cmdargs)

        if not targetList:
            self.selfMsg("usage: read <item> [number]\n")
            return(False)
        elif len(targetList) == 1:
            obj1 = targetList[0]
            obj2 = None
        elif len(targetList) == 2:
            obj1 = targetList[0]
            obj2 = targetList[1]

        if roomObj or obj1 or obj2:  # tmp - delete when implemented
            pass

        self.selfMsg("'read' not implemented yet\n")

    def do_remove(self, line):
        ''' unequip an item that you have equipped '''
        return(self.do_unequip(line))

    def do_repair(self, line):
        ''' repair an item in a repair shop '''
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
        objList = self.getObjFromCmd(playerInventory, cmdargs)

        if len(objList) >= 1:
            obj1 = objList[0]
        else:
            self.selfMsg("Invalid item\n")
            return(False)

        if not obj1.canBeRepaired():
            self.selfMsg("This can't be repaired\n")
            return(False)

        price = self.calculateObjectPrice(self.svrObj, obj1) * 100
        prompt = ("You are about to repair " + obj1.getArticle() + " " +
                  obj1.getName() + " for " + str(price) +
                  " shillings.  Proceed?")
        if self.svrObj.promptForYN(prompt):
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
        self.selfMsg(line + " not implemented yet\n")

    def do_roominfo(self, line):
        '''' dm - show room info '''
        if not self.charObj.isDm():
            return(False)
        self.selfMsg(self.charObj.getRoom().getInfo())

    def do_run(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_s(self, line):
        self.move(self.svrObj, [self._lastinput[0]])  # pass first letter

    def do_save(self, line):
        if self.scrObj.charObj.save():
            self.selfMsg("Saved\n")
        else:
            self.selfMsg("Could not save\n")

    def do_say(self, line):
        msg = self.svrObj.promptForInput()
        self.roomMsg(self.charObj.roomObj, msg)
        self.charObj.setHidden(False)

    def do_search(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_sell(self, line):
        ''' Sell an item to a pawnshop '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if not roomObj.getType() == 'Shop':
            self.selfMsg("You can't do that here.  Find a fence\n")
            return(False)
        if not roomObj.isPawnShop():
            self.selfMsg("You can't do that here.  Find a fence\n")
            return(False)

        if len(cmdargs) < 1:
            self.selfMsg("usage: sell <item> [#]\n")
            return(False)
        playerInventory = charObj.getInventory()
        objList = self.getObjFromCmd(playerInventory, cmdargs)
        if len(objList) >= 1:
            obj1 = objList[0]
        else:
            self.selfMsg("Invalid item\n")
            return(False)

        price = int(self.calculateObjectPrice(self.svrObj, obj1) * .8)

        # prompt player for confirmation
        prompt = ("You are about to pawn " + obj1.getArticle() +
                  " " + obj1.getName() + " for " + str(price) +
                  " shillings.  Proceed?")
        self.sellTransaction(obj1, price, prompt, roomObj.getSuccessTxt(),
                             roomObj.getAbortedTxt())

    def do_send(self, line):
        msg = self.svrObj.promptForInput()
        self.gameObj.gameMsg(msg)
        return(False)

    def do_shout(self, line):
        msg = self.svrObj.promptForInput()
        self.yellMsg(self.charObj.roomObj, msg)

    def do_skills(self, line):
        self.selfMsg(self.charObj.SkillsInfo())

    def do_smash(self, line):
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomObjList = roomObj.getAllObjects()
#        fullObjList = charObj.getInventory() + roomObjList

        objList = self.getObjFromCmd(roomObjList, cmdargs)

        if len(objList) >= 1:
            obj1 = objList[0]
        else:
            self.selfMsg("usage: smash <item> [number]\n")
            return(False)

        if not obj1.isSmashable():
            self.selfMsg("This is not smashable!")
            return(False)

        if obj1.smash(charObj):
            self.othersMsg(charObj.getName() + " smashes the " +
                           obj1.getSingular() + " open.")
            self.selfMsg("You smash it open!")
            otherRoom = self.getCorrespondingRoomObj(obj1)
            if otherRoom:
                self.roomMsg(otherRoom, obj1.getSingular() +
                             " smashes open")
            if obj1.gettype() == "Door":
                self.modifyCorrespondingDoor(obj1)
            return(False)
        else:
            self.othersMsg(charObj.getName() +
                           " fails to smash " + obj1.describe() + " open.")
            self.selfMsg("Bang! You fail to smash it open!")
            otherRoom = self.getCorrespondingRoomObj(obj1)
            if otherRoom:
                self.roomMsg(otherRoom, "You hear a noise on " +
                             "the other side of the " + obj1.getSingular())
        return(False)

    def do_south(self, line):
        self.move(self.svrObj, [self._lastinput[0]])  # pass first letter

    def do_stats(self, line):
        self.selfMsg(self.charObj.StatsInfo())

    def do_status(self, line):
        pass

    def do_steal(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_strike(self, line):
        ''' combat '''
        self.selfMsg(line + " not implemented yet\n")

    def do_suicide(self, line):
        self.suicide(self.svrObj)
        return(False)

    def do_take(self, line):
        return(self.do_get(line))

    def do_talk(self, line):
        return(self.do_parley(line))

    def do_teach(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_thrust(self, line):
        ''' combat '''
        self.selfMsg(line + " not implemented yet\n")

    def do_track(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_train(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_turn(self, line):
        self.selfMsg(line + " not implemented yet\n")

    def do_u(self, line):
        self.move(self.svrObj, [self._lastinput[0]])  # pass first letter

    def do_unequip(self, line):
        cmdargs = line.split(' ')
        charObj = self.charObj

        charObjList = charObj.getInventory()

        targetList = self.getObjFromCmd(charObjList, cmdargs)

        if not targetList:
            self.selfMsg("usage: " + cmdargs[0] +
                         " <item> [number]\n")
            return(False)
        elif len(targetList) > 0:
            obj1 = targetList[0]
        else:
            obj1 = None

        if charObj.unequip(obj1):
            self.selfMsg("Ok\n")
        else:
            self.selfMsg("You can't do that\n")

    def do_unlock(self, line):
        ''' unlock a door/chest with a key '''
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        roomObjList = roomObj.getAllObjects()
#        fullObjList = charObj.getInventory() + roomObjList

        objList = self.getObjFromCmd(roomObjList, cmdargs)

        if len(objList) >= 1:
            obj1 = objList[0]
            if len(objList) >= 2:
                obj2 = objList[1]
        else:
            self.selfMsg("usage: unlock <item> [number] <key> [#]\n")
            return(False)

        if not obj2:
            self.selfMsg("usage: unlock <obj> <key>")
        if not obj1.isUnlockable():
            self.selfMsg("You can't unlock that.")
            return(False)
        # need to get lock ID and see if the given key matches
        # if keys have charges, we need to modify key
        if obj1.unlock(charObj):
            self.selfMsg("You unlock the lock.")
            self.othersMsg(charObj.getName() + " unlocks the " +
                           "lock on the " + obj1.getSingular(),
                           charObj.isHidden())
            return(False)
        else:
            self.selfMsg("You fail to unlock the lock.")
            self.othersMsg(charObj.getName() + " fails to " +
                           "unlock the lock on the " +
                           obj1.getSingular(), charObj.isHidden())
            return(False)
        return(False)

    def do_up(self, line):
        self.move(self.svrObj, [self._lastinput[0]])  # pass first letter

    def do_use(self, line):
        cmdargs = line.split(' ')
        charObj = self.charObj
        roomObj = charObj.getRoom()

        charObjList = charObj.getInventory()

        targetList = self.getObjFromCmd(charObjList, cmdargs)

        if not targetList:
            self.selfMsg("usage: use <item> [number]\n")
            return(False)
        elif len(targetList) == 1:
            obj1 = targetList[0]
            obj2 = None
        elif len(targetList) == 2:
            obj1 = targetList[0]
            obj2 = targetList[1]

        if obj1.isEquippable():
            if charObj.equip(obj1):
                self.selfMsg("Ok\n")
            else:
                self.selfMsg("You can't do that\n")
        elif isinstance(obj1, Scroll):
            spellObj = Spell(charObj.getClass(), obj1.getSpell())
            self.selfMsg("The scroll disintegrates\n")

            if not obj2:           # if second target is not defined
                obj2 = charObj     # current character is the target

            self.castSpell(spellObj, obj2)
            charObj.removeFromInventory(obj1)     # remove item
        elif obj1.isMagicItem():
            if obj1.getCharges() <= 0:
                self.selfMsg("This item has no charges left\n")
                return(False)
            if obj1.getCharges() == 1:
                self.selfMsg(obj1.getName() + "fizzles\n")

            spellObj = Spell(charObj.getClass(), obj1.getSpell())

            if not obj2:           # if second target is not defined
                obj2 = charObj     # current character is the target

            self.castSpell(spellObj, obj2)
            obj1.decrementChargeCounter()

            if roomObj:  # tmp - remove later if not needed
                pass

    def do_w(self, line):
        self.move(self.svrObj, [self._lastinput[0]])  # pass first letter

    def do_wear(self, line):
        return(self.do_use(line))

    def do_west(self, line):
        self.move(self.svrObj, [self._lastinput[0]])  # pass first letter

    def do_where(self, line):
        return(self.do_look(line))

    def do_whisper(self, line):
        cmdargs = line.split(' ')
        if not cmdargs[0]:
            self.selfMsg("usage: whisper <playerName>\n")
            return(False)
        msg = self.svrObj.promptForInput()
        self.gameObj.directMsg(cmdargs[0], msg)  # wrong method for this??
        recieved = False

        for oneChar in self.charObj.getRoom().getCharacterList():
            if re.match(cmdargs[0], oneChar.getName()):   # if name matches
                oneChar.svrObj.spoolOut(msg)            # notify
                recieved = True
            else:
                if oneChar.hearsWhispers():
                    oneChar.svrObj.spoolOut("You overhear " +
                                            self.charObj.getName() +
                                            ' whisper ' + msg)
                    self.charObj.setHidden(False)
        return(recieved)

    def do_who(self, line):
        charTxt = ''
        charObj = self.charObj
        for onechar in charObj.getRoom().getCharacterList():
            if onechar != charObj:
                charTxt += onechar.getName() + '\n'
        if charTxt == '':
            buf = "You are the only one online"
        else:
            buf = "Characters in the Game:\n" + charTxt
        self.selfMsg(buf)

    def do_wield(self, line):
        return(self.do_use(line))

    def do_withdraw(self, line):
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
        if self.svrObj.promptForYN(prompt):
            charObj.bankWithdraw(amount, taxRate)
            roomObj.recordTransaction("withdrawl/" + str(wAmount))
            roomObj.recordTransaction("fees/" + str(bankfee))
            self.selfMsg(roomObj.getSuccessTxt())
            return(False)
        else:
            self.selfMsg(roomObj.getAbortedTxt())
            return(False)

    def do_yell(self, line):
        msg = self.svrObj.promptForInput()
        self.yellMsg(self.charObj.roomObj, msg)

    # --------------------------------------

    def look(self):
        buf = self.charObj.getRoom().display(self.charObj)
        return(buf)

    def move(self, svrObj, cmdargs):
        charObj = svrObj.charObj
        moved = False
        currentRoom = charObj.getRoom()
        if currentRoom.isDirection(cmdargs[0]):  # if command is a direction
            # Handle the primary directions
            direction = cmdargs[0]
            exitDict = currentRoom.getExits()
            if direction in exitDict.keys():
                roomnum = exitDict[direction]
                if roomnum and roomnum != 0:
                    self.gameObj.joinRoom(roomnum, charObj)
                    currentRoom = charObj.getRoom()
                    moved = True
                else:
                    moved = False
        else:
            # handle doors and Portals
            if len(cmdargs) == 1:       # no object - take no action
                oneobj = None
            elif len(cmdargs) == 2:      # object, but no number
                objname = cmdargs[1]
                oneobj = itemSearch(currentRoom.getAllObjects(), objname,
                                    typeList=['door', 'portal'])
            elif len(cmdargs) > 2:      # object with number
                objname = cmdargs[1]
                desirednum = cmdargs[2]
                oneobj = itemSearch(currentRoom.getAllObjects(), objname,
                                    desirednum, typeList=['door', 'portal'])
            if oneobj:
                if oneobj.canBeEntered(svrObj):
                    roomnum = oneobj.getToWhere()
                    self.gameObj.joinRoom(roomnum, charObj)
                    currentRoom = charObj.getRoom()
                    moved = True
        if moved:
            charObj.setHidden(False)
            self.selfMsg(self.look())
            return(True)
        else:
            self.selfMsg("You can not go there!\n")
        return(False)

    def getCorrespondingRoomObj(self, doorObj, activeOnly=False):
        ''' Get the room object that correcponds to a door '''
        roomObj = self.gameObj.getActiveRoom(doorObj.getToWhere())
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
            for obj in roomObj.getObjectList():
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

    def suicide(self, svrObj):
        if svrObj.promptForYN("DANGER: This will permanently delete " +
                              "your character.  Are you sure?"):
            charObj = svrObj.charObj
            charName = charObj.getName()
            self.leaveRoom(charObj)
            self.removeCharacterFromGame(charObj)
            msg = svrObj.txtBanner(charName +
                                   ' has shuffled off this mortal coil',
                                   bChar='=')
            charObj.delete()
            charObj = None
            svrObj.acctObj.removeCharacterFromAccount(charName)
            self.gameObj.gameMsg(msg)
            logging.info("Character deleted: " + charName)
            return(True)
        return(False)

    def combat(self, svrObj, cmdargs):
        ''' Process commands that are related to combat '''
        charObj = svrObj.charObj

        charObj.setHidden(False)
        self.selfMsg("Combat not implemented yet\n")
        return(True)

    def buyTransaction(self, obj, price, prompt,
                       successTxt='Ok.', abortTxt='Ok.'):
        ''' buy an item '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if self.svrObj.promptForYN(prompt):
            charObj.subtractCoins(price)           # tax included
            charObj.addToInventory(obj)         # add item
            if roomObj.getType() == 'Shop':
                roomObj.recordTransaction(obj)      # update stats
                roomObj.recordTransaction("sale/" + str(price))
                charObj.recordTax(roomObj.getTaxAmount(price))
            self.selfMsg(successTxt)
            return(True)
        else:
            self.selfMsg(abortTxt)
        return(False)

    def sellTransaction(self, obj, price, prompt,
                        successTxt='Ok.', abortTxt='Ok.'):
        ''' sell an item '''
        charObj = self.charObj
        roomObj = charObj.getRoom()

        if self.svrObj.promptForYN(prompt):
            charObj.removeFromInventory(obj)     # remove item
            charObj.addCoins(price)              # tax included
            if roomObj.getType() == 'Shop':
                roomObj.recordTransaction(obj)       # update stats
                roomObj.recordTransaction("purchase/" + str(price))
                charObj.recordTax(roomObj.getTaxAmount(price))
            self.selfMsg(successTxt)
            return(True)
        else:
            self.selfMsg(abortTxt)
            return(False)

    def kidnap(self, charObj, roomNum=184):
        ''' Instead of death:
        * Player is teleported to room
        * ??? monster will placed in the room connected to the door in room 7.
        '''
        self.gameObj.joinRoom(roomNum, charObj)
        return(True)

    def getObjFromCmd(self, itemList, cmdargs):
        ''' Returns a list of target Items, given the full cmdargs '''
        targetItems = []
        for target in splitCmd(cmdargs):
            obj = targetSearch(itemList, target)
            if obj:
                targetItems.append(obj)
        return(targetItems)

    def castSpell(self, spellObj, target):
        ''' perform the spell
            * assume that all other checks are complete
        '''
        if not spellObj:
            return(False)

        if not target:
            return(False)

        # roll/check for spell success
        if isinstance(target, Character):   # use on Character
            pass
        elif isinstance(target, Creature):  # use on Creature
            pass
        else:                             # use on object
            pass
        return(False)

    def calculateObjectPrice(self, svrObj, obj):
        ''' return adjusted price for an object based on many factors '''
        if obj.isCursed():
            return(1)

        price = obj.getValue()
        price = obj.adjustPrice(price)   # object adjustment
        price = svrObj.charObj.getRoom().adjustPrice(price)  # room adjustment
        price = svrObj.charObj.adjustPrice(price)  # char adjust
        return(price)


# instanciate the _Game class
_game = _Game()


def Game():
    ''' return a reference to the single, existing _game instance
        Thus, when we try to instanciate Game, we are just returning
        a ref to the existing Game '''

    return(_game)
