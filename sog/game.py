''' game class '''  # noqa

# We want only one implementation of the Game Class.
# To do this, create a single instance of the Game class on import.  Then
# each time we try to instanciate Game(), we just return a reference to
# the game class.

from datetime import datetime
import logging
import re

from common.general import isIntStr, dateStr
from common.general import splitCmd, itemSearch, targetSearch
from help import enterHelp
from room import RoomFactory
from object import ObjectFactory
# from object import Potion, Scroll, Teleport, Staff
from object import Scroll
from character import Character
from creature import Creature
from magic import Spell


class _Game():
    ''' game class '''

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

        # in-game broadcast announcing game entry
        msg = svrObj.txtBanner(charObj.getName() +
                               ' has entered the game', bChar='=')
        self.gameMsg(msg)

        self.addCharacterToGame(charObj)

        # add room to charObj and then display the room
        if self.joinRoom(1, charObj):
            self.selfMsg(charObj, charObj.getRoom().display(charObj))
            return(True)
        return(False)

    def selfMsg(self, charObj, msg):
        ''' show only to yourself '''
        recieved = False
        if charObj:
            charObj.svrObj.spoolOut(msg)
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

    def othersMsg(self, svrObj, msg, ignore=False):
        ''' shown to others in room, but not you '''
        recieved = False
        if not svrObj:
            return(False)

        if ignore:             # may get set to True if player is hidden
            return(False)

        for oneChar in svrObj.charObj.getRoom().getCharacterList():
            if oneChar != svrObj.charObj:            # if not yourself
                oneChar.svrObj.spoolOut(msg)
                recieved = True
        return(recieved)

    def yellMsg(self, roomObj, msg):
        ''' shown to your room and rooms in adjoining directions '''
        recieved = False
        if not roomObj:
            return(False)

        exitDict = roomObj.getExits()
        for oneRoom in self.getActiveRoomList():    # loop through active rooms
            if oneRoom.getId() in exitDict.keys():  # if room id is an exit
                for oneChar in oneRoom.getCharacterList():  # get chars in room
                    oneChar.svrObj.spoolOut(msg)            # notify
                    recieved = True
        return(recieved)

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

    def gameMsg(self, msg):
        ''' shown to everyone in the game '''
        for oneChar in self.getCharacterList():
            oneChar.svrObj.spoolOut(msg)

    def processCommand(self, svrObj):    # noqa: C901
        ''' Process the game commands '''
        charObj = svrObj.charObj
        acctObj = svrObj.acctObj
        buf = ''

        cmdargs = svrObj.getInputStr().split(' ')
        cmd = cmdargs[0]

        logging.debug("GAME input = " + svrObj.getInputStr())

        self.addCharacterToGame(charObj)

        if charObj.isDm():
            if self.processDmCommand(svrObj, cmdargs):
                return(True)

        if cmd == '':
            pass
        elif (cmd == 'accept' or cmd == 'offer' or cmd == 'broadcast' or
              cmd == 'say' or cmd == 'shout' or cmd == 'send' or
              cmd == 'whisper' or cmd == 'yell'):
            self.converse(svrObj, cmdargs)
        elif cmd == 'appeal':
            pass
        elif (cmd == 'attack' or cmd == 'backstab' or cmd == 'block' or
              cmd == 'circle' or cmd == 'feint' or cmd == 'hit' or
              cmd == 'kill' or cmd == 'parry' or cmd == 'strike' or
              cmd == 'thrust'):
            self.combat(svrObj, cmdargs)
        elif (cmd == 'balance' or cmd == 'deposit' or cmd == 'withdraw'):
            self.bankTransaction(svrObj, cmdargs)
        elif (cmd == 'buy' or cmd == 'catalog' or cmd == 'list' or
              cmd == 'pawn' or cmd == 'repair' or cmd == 'sell'):
            self.shopTransaction(svrObj, cmdargs)
        elif (cmd == 'bribe' or cmd == 'parley' or cmd == 'talk'):
            self.npcInteraction(svrObj, cmdargs)
        elif cmd == 'brief':
            charObj.setPromptSize("brief")
        elif cmd == 'cast':
            pass
        elif cmd == 'clock':
            buf += dateStr('now') + "\n"
        elif cmd == 'dm-on' and acctObj.isAdmin():
            charObj.setDm()
        elif cmd == 'echo':
            pass
        elif cmd == 'exit' or cmd == "quit":
            charObj.save()
            self.leaveRoom(charObj)
            self.leaveGame(svrObj)
            return(False)
        elif cmd == 'experience' or cmd == 'exp':
            buf += charObj.expInfo()
        elif cmd == 'file':
            buf += acctObj.showCharacterList()
        elif cmd == 'follow':
            pass
        elif cmd == 'full':   # not in original game
            charObj.setPromptSize("full")
        elif cmd == 'go' or cmd == 'climb' or cmd == 'enter':
            if cmdargs[1]:
                if not self.move(svrObj, cmdargs):
                    buf += "You can't go there\n"
            else:
                buf += "You can't go there\n"
        elif cmd == 'health' or cmd == 'hea' or cmd == 'h':
            buf += charObj.healthInfo()
        elif cmd == 'help':
            enterHelp()
        elif cmd == 'hide':
            if len(cmdargs) == 1:
                charObj.attemptToHide()
                buf += "You hide in the shadows\n"
            else:
                self.roomObjectInteraction(svrObj, cmdargs)
        elif cmd == 'hint':
            pass
        elif cmd == 'identify':
            pass
        elif cmd == 'information' or cmd == 'info':
            buf += charObj.getInfo()
        elif cmd == 'inventory' or cmd == "inv":
            buf += charObj.inventoryInfo()
        elif cmd == 'look' or cmd == 'examine' or cmd == 'where':
            roomObj = charObj.getRoom()
            if len(cmdargs) == 1:
                buf += roomObj.display(charObj) + "\n"
            else:
                objList = self.getObjFromCmd(roomObj.getAllObjects(), cmdargs)
                if len(objList) >= 1:
                    buf += objList[0].describe() + "\n"
                else:
                    # need to handle characters and creatures
                    buf += "You must be blind because you don't see that\n"
        elif cmd == 'prompt':
            charObj.setPromptSize('')
        elif cmd == 'purse':
            buf += charObj.financialInfo()
        elif cmd == 'return':
            pass
        elif cmd == 'run' or cmd == 'panic':
            pass
        elif cmd == 'save':
            if charObj.save():
                buf += "Saved\n"
            else:
                buf += "Could not save\n"
        elif cmd == 'search':
            pass
        elif cmd == 'skills':
            buf += charObj.SkillsInfo()
        elif cmd == 'status':
            pass
        elif cmd == 'stats':
            buf += charObj.StatsInfo()
        elif cmd == 'steal':
            pass
        elif cmd == 'suicide' or cmd == 'lose':
            self.suicide(svrObj)
            return(False)
        elif cmd == 'teach':
            pass
        elif cmd == 'track':
            pass
        elif cmd == 'train':
            pass
        elif cmd == 'turn':
            pass
        elif (cmd == 'break' or cmd == 'close' or cmd == 'get' or
              cmd == 'lock' or cmd == 'open' or cmd == 'picklock' or
              cmd == 'smash' or cmd == 'take' or cmd == 'unlock'):
            self.roomObjectInteraction(svrObj, cmdargs)
        elif (cmd == 'drink' or cmd == 'drop' or cmd == 'draw' or
              cmd == 'equip' or cmd == 'hold' or cmd == 'put' or
              cmd == 'read' or cmd == 'remove' or cmd == 'unequip' or
              cmd == 'use' or cmd == 'wield' or cmd == 'wear'):
            self.inventoryObjectInteraction(svrObj, cmdargs)
        elif cmd == 'who':
            charTxt = ''
            for onechar in charObj.getRoom().getCharacterList():
                if onechar != charObj:
                    charTxt += onechar.getName() + '\n'
            if charTxt == '':
                buf += "You are the only one online"
            else:
                buf += "Characters in the Game:\n" + charTxt
        elif (cmd == 'north' or cmd == 'south' or cmd == 'east' or
              cmd == 'west' or cmd == 'up' or cmd == 'down' or
              cmd == 'out' or re.match("^[nsewudo]$", cmd)):
            directionChar = cmd[0]     # get the first letter
            self.move(svrObj, [directionChar])
        else:
            buf += 'Unknown Command: ' + cmd + '\n'
            self.selfMsg(charObj, buf)
            return(True)

        self.selfMsg(charObj, buf)
        if charObj:  # doesn't exist if there is a suicide
            charObj.save(logStr=__class__.__name__)
        return(True)

    def look(self, svrObj):
        buf = svrObj.charObj.getRoom().display(svrObj.charObj)
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
                    self.joinRoom(roomnum, charObj)
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
                    self.joinRoom(roomnum, charObj)
                    currentRoom = charObj.getRoom()
                    moved = True
        if moved:
            charObj.setHidden(False)
            self.selfMsg(charObj, self.look(svrObj))
            return(True)
        else:
            self.selfMsg(charObj, "You can not go there!\n")
        return(False)

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
            self.removeFromActiveRooms(charObj.getRoom())  # Remove from active
        charObj.getRoom().removeCharacter(charObj)  # remove charact from room
        charObj.removeRoom()                       # Remove room from character
        return(True)

    def getCharacterList(self):
        return(self._characterList)

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

    def getCorrespondingRoomObj(self, doorObj, activeOnly=False):
        ''' Get the room object that correcponds to a door '''
        roomObj = self.getActiveRoom(doorObj.getToWhere())  # get active room
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
            self.gameMsg(msg)
            logging.info("Character deleted: " + charName)
            return(True)
        return(False)

    def combat(self, svrObj, cmdargs):
        ''' Process commands that are related to combat '''
        charObj = svrObj.charObj

        charObj.setHidden(False)
        self.selfMsg(charObj, "Combat not implemented yet\n")
        return(True)

    def converse(self, svrObj, cmdargs):
        ''' Process commands that are related to player communication '''
        charObj = svrObj.charObj

        if cmdargs[0] == 'accept':
            self.selfMsg(charObj, cmdargs[0] + " not implemented yet\n")
        elif cmdargs[0] == 'offer':
            self.selfMsg(charObj, cmdargs[0] + " not implemented yet\n")
        elif cmdargs[0] == 'say':
            msg = svrObj.promptForInput()
            self.roomMsg(svrObj.charObj.roomObj, msg)
            charObj.setHidden(False)
        elif cmdargs[0] == 'send':
            msg = svrObj.promptForInput()
            self.gameMsg(msg)
            return(True)
        elif cmdargs[0] == 'shout' or cmdargs[0] == 'yell':
            msg = svrObj.promptForInput()
            self.yellMsg(svrObj.charObj.roomObj, msg)
        elif cmdargs[0] == 'whisper':
            if not cmdargs[1]:
                self.selfMsg(charObj, "usage: " + cmdargs[0] +
                             " <playerName>\n")
                return(False)
            msg = svrObj.promptForInput()
            self.directMsg(self, cmdargs[1], msg)
            # toDo: if overheard
            # becomes unhidden and other players hear the msg
            # charObj.setHidden(False)
        else:
            self.selfMsg(charObj, "Conversation not implemented yet\n")
        return(True)

    def processDmCommand(self, svrObj, cmdargs):
        ''' Process commands that are related to npc communication '''
        charObj = svrObj.charObj
        buf = ''

        if cmdargs[0] == 'adminstats':
            buf += charObj.getDmStats()
        elif cmdargs[0] == 'dm-off':
            charObj.removeDm()
            buf += "Ok"
        elif cmdargs[0] == 'debug':
            if len(cmdargs) == 1:
                self.selfMsg(charObj, "usage: debug <room | self | object>")
                return(True)

            roomObj = charObj.getRoom()
            if cmdargs[1].lower() == 'room':
                buf += ('=== Debug Info for Room ' +
                        str(roomObj.getId()) + " ===\n")
                buf += roomObj.debug() + '\n'
            if cmdargs[1].lower() == 'self':
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
        elif cmdargs[0] == 'goto':
            if len(cmdargs) == 1:
                self.selfMsg(charObj, "usage: goto <room>")
                return(True)

            self.joinRoom(cmdargs[1], charObj)
            buf += charObj.getRoom().display(charObj)
        elif cmdargs[0] == 'roominfo':
            buf += charObj.getRoom().getInfo()

        if buf != '':
            self.selfMsg(charObj, buf)
            return(True)
        return(False)

    def npcInteraction(self, svrObj, cmdargs):
        ''' Process commands that are related to npc communication '''
        charObj = svrObj.charObj

        charObj.setHidden(False)
        self.selfMsg(charObj, "NPC interaction not implemented yet\n")
        return(True)

    def getObjFromCmd(self, itemList, cmdargs):
        ''' Returns a list of target Items, given the full cmdargs '''
        targetItems = []
        cmd, targets = splitCmd(cmdargs)
        for target in targets:
            obj = targetSearch(itemList, target)
            if obj:
                targetItems.append(obj)
        return(targetItems)

    def inventoryObjectInteraction(self, svrObj, cmdargs):    # noqa: C901
        cmd = cmdargs[0]
        charObj = svrObj.charObj
        roomObj = charObj.getRoom()

        charObjList = charObj.getInventory()

        targetList = self.getObjFromCmd(charObjList, cmdargs)

        if not targetList:
            self.selfMsg(charObj, "usage: " + cmdargs[0] +
                         " <item> [number]\n")
            return(True)
        elif len(targetList) == 1:
            obj1 = targetList[0]
            obj2 = None
        elif len(targetList) == 2:
            obj1 = targetList[0]
            obj2 = targetList[1]

        if cmd == 'drink':
            pass
        elif cmd == 'drop':
            if charObj.removeFromInventory(obj1):
                roomObj.addObject(obj1)
                self.selfMsg(charObj, "Ok\n")
            else:
                self.selfMsg(charObj, "Didn't work\n")
        elif cmd == 'put':
            pass
        elif cmd == 'read':
            pass
        elif cmd == 'use':
            if obj1.isEquippable():
                if charObj.equip(obj1):
                    self.selfMsg(charObj, "Ok\n")
                else:
                    self.selfMsg(charObj, "You can't do that\n")
            elif isinstance(obj1, Scroll):
                spellObj = Spell(charObj.getClass(), obj1.getSpell())
                self.selfMsg(charObj, "The scroll disintegrates\n")

                if not obj2:           # if second target is not defined
                    obj2 = charObj     # current character is the target

                self.castSpell(spellObj, obj2)
                charObj.removeFromInventory(obj1)     # remove item
            elif obj1.isMagicItem():
                if obj1.getCharges() <= 0:
                    self.selfMsg(charObj, "This item has no charges left\n")
                    return(False)
                if obj1.getCharges() == 1:
                    self.selfMsg(charObj, obj1.getName() + "fizzles\n")

                spellObj = Spell(charObj.getClass(), obj1.getSpell())

                if not obj2:           # if second target is not defined
                    obj2 = charObj     # current character is the target

                self.castSpell(spellObj, obj2)
                obj1.decrementChargeCounter()

        elif (cmd == 'wield' or cmd == 'hold' or
              cmd == 'wear' or cmd == 'draw') or cmd == 'equip':
            if charObj.equip(obj1):
                self.selfMsg(charObj, "Ok\n")
            else:
                self.selfMsg(charObj, "You can't do that\n")
        elif (cmd == 'unequip' or cmd == 'remove'):
            if charObj.unequip(obj1):
                self.selfMsg(charObj, "Ok\n")
            else:
                self.selfMsg(charObj, "You can't do that\n")
        return(True)

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

    def roomObjectInteraction(self, svrObj, cmdargs):     # noqa: C901
        ''' Process commands that are related to object manipulation '''
        cmd = cmdargs[0]
        charObj = svrObj.charObj
        roomObj = charObj.getRoom()

        roomObjList = roomObj.getAllObjects()
#        fullObjList = charObj.getInventory() + roomObjList

        objList = self.getObjFromCmd(roomObjList, cmdargs)

        if len(objList) >= 1:
            obj1 = objList[0]
            if len(objList) >= 2:
                obj2 = objList[1]
        else:
            svrObj.spoolOut("usage: " + cmdargs[0] + " <item> [number]\n")
            return(True)

        if cmd == 'break' or cmd == 'smash':
            if not obj1.isSmashable():
                self.selfMsg(charObj, "This is not smashable!")
                return(False)

            if obj1.smash(charObj):
                self.othersMsg(svrObj,
                               charObj.getName() + " smashes the " +
                               obj1.getSingular() + " open.")
                self.selfMsg(charObj, "You smash it open!")
                otherRoom = self.getCorrespondingRoomObj(obj1)
                if otherRoom:
                    self.roomMsg(otherRoom, obj1.getSingular() +
                                 " smashes open")
                return(True)
            else:
                self.othersMsg(svrObj,
                               charObj.getName() + " fails to smash " +
                               obj1.describe() + " open.")
                self.selfMsg(charObj, "Bang! You fail to smash it open!")
                otherRoom = self.getCorrespondingRoomObj(obj1)
                if otherRoom:
                    self.roomMsg(otherRoom, "You hear a noise on " +
                                 "the other side of the " +
                                 obj1.getSingular())
            return(False)
        elif cmd == 'close':
            if not obj1.isClosable():
                self.selfMsg(charObj, "This is not closable!")
                return(False)

            if obj1.close(charObj):
                return(True)
            return(False)
        elif cmd == 'get' or cmd == "take":
            if not obj1.isCarryable():
                self.selfMsg(charObj, "That can not be carried.")
                return(False)

            if charObj.canCarryAdditionalWeight(obj1.getWeight()):
                roomObj.removeObject(obj1)
                charObj.addToInventory(obj1)
                self.selfMsg(charObj, "Ok\n")
            else:
                self.selfMsg(charObj, "You are not strong enough.")
        elif cmd == 'lock':
            if not obj2:
                self.selfMsg(charObj, "usage: lock <obj> <key>")
                return(False)
            if not obj1.isLockable():
                self.selfMsg(charObj, "This is not lockable!")
                return(False)
            self.selfMsg(charObj, "Not implemented yet.")
            return(False)
        elif cmd == 'open':
            if not obj1.isOpenable():
                self.selfMsg(charObj, "You can't open that.")
                return(False)

            if obj1.open(charObj):
                self.selfMsg(charObj, "It opens.")
                self.othersMsg(svrObj,
                               charObj.getName() + " opens the " +
                               obj1.getSingular(), charObj.isHidden())
                return(True)
            else:
                self.selfMsg(charObj, "You fail to open the door.")
            return(False)
        elif cmd == 'picklock':
            if not obj1.isPickable():
                self.selfMsg(charObj, "You can't pick that.")
                return(False)

            if obj1.pick(charObj):
                self.selfMsg(charObj, "You pick the lock.")
                self.othersMsg(svrObj,
                               charObj.getName() + " picks the " +
                               "lock on the " + obj1.getSingular(),
                               charObj.isHidden())
                return(True)
            else:
                self.selfMsg(charObj, "You fail to pick the lock.")
                self.othersMsg(svrObj,
                               charObj.getName() + " fails to pick " +
                               "the lock on the " +
                               obj1.getSingular(), charObj.isHidden())
                return(False)
            return(False)
        elif cmd == 'unlock':
            if not obj2:
                self.selfMsg(charObj, "usage: unlock <obj> <key>")
            if not obj1.isUnlockable():
                self.selfMsg(charObj, "You can't unlock that.")
                return(False)
            # need to get lock ID and see if the given key matches
            # if keys have charges, we need to modify key
            if obj1.unlock(charObj):
                self.selfMsg(charObj, "You unlock the lock.")
                self.othersMsg(svrObj,
                               charObj.getName() + " unlocks the " +
                               "lock on the " + obj1.getSingular(),
                               charObj.isHidden())
                return(True)
            else:
                self.selfMsg(charObj, "You fail to unlock the lock.")
                self.othersMsg(svrObj,
                               charObj.getName() + " fails to " +
                               "unlock the lock on the " +
                               obj1.getSingular(), charObj.isHidden())
                return(False)
            return(False)

        if (cmd == 'open' or cmd == 'close' or cmd == 'smash'):
            if obj1.gettype() == "Door":
                self.modifyCorrespondingDoor(obj1)

    def calculateObjectPrice(self, svrObj, obj):
        ''' return adjusted price for an object based on many factors '''
        if obj.isCursed():
            return(1)

        price = obj.getValue()
        price = obj.adjustPrice(price)   # object adjustment
        price = svrObj.charObj.getRoom().adjustPrice(price)  # room adjustment
        price = svrObj.charObj.adjustPrice(price)  # char adjust
        return(price)

    def shopTransaction(self, svrObj, cmdargs):    # noqa: C901
        ''' Process commands that are related to shop transactions '''
        cmd = cmdargs[0]
        charObj = svrObj.charObj
        roomObj = charObj.getRoom()

        if roomObj.getType() == 'Shop':
            if cmd == 'buy':
                if roomObj.isVendor():
                    if len(cmdargs) < 2 or not isIntStr(cmdargs[1]):
                        self.selfMsg(charObj, "usage: buy <item> [#]\n")
                        return(False)
                    catList = roomObj.getcatalog()
                    if ((int(cmdargs[1]) < 0 or
                         int(cmdargs[1]) > (len(catList)) - 1)):
                        self.selfMsg(charObj, "Bad item number.  Aborted\n")
                        return(False)
                    catItem = catList[int(cmdargs[1])]
                    oType, oNum = catItem.split('/')
                    obj1 = ObjectFactory(oType, oNum)
                    obj1.load()
                    price = self.calculateObjectPrice(svrObj, obj1)

                    # check if player has the funds
                    if not charObj.canAffordAmount(price):
                        self.selfMsg(charObj, roomObj.getCantAffordTxt())
                        return(False)
                    # check if player can carry the Weight
                    weight = obj1.getWeight()
                    if not charObj.canCarryAdditionalWeight(weight):
                        self.selfMsg(charObj, roomObj.getCantCarryTxt(weight))
                        return(False)

                    # prompt player for confirmation
                    prompt = ("You are about to spend " + str(price) +
                              " shillings for " + obj1.getArticle() + " " +
                              obj1.getName() + ".  Proceed?")
                    if svrObj.promptForYN(prompt):
                        charObj.subtractCoins(price)           # tax included
                        charObj.addToInventory(obj1)         # add item
                        roomObj.recordTransaction(obj1)      # update stats
                        roomObj.recordTransaction("sale/" + str(price))
                        charObj.recordTax(roomObj.getTaxAmount(price))
                        self.selfMsg(charObj, roomObj.getSuccessTxt())
                    else:
                        self.selfMsg(charObj, roomObj.getAbortedTxt())
                else:
                    self.selfMsg(charObj, "Find a shop!\n")
            elif cmd == 'catalog':
                ROW_FORMAT = "  ({0:2}) {1:<7} {2:<60}\n"

                itemBuf = ''
                if roomObj.isVendor():
                    # display # list by iterating, loading, & displaying objs
                    for num, oneitem in enumerate(roomObj.getcatalog()):
                        oType, oNum = oneitem.split('/')
                        obj1 = ObjectFactory(oType, oNum)
                        obj1.load()
                        # calculate price
                        price = self.calculateObjectPrice(svrObj, obj1)
                        itemBuf += ROW_FORMAT.format(num, price,
                                                     obj1.describe())
                    if itemBuf != '':
                        self.selfMsg(charObj, "Catalog of items for sale\n" +
                                     ROW_FORMAT.format('#', 'Price',
                                                       'Description') +
                                     itemBuf)
                else:
                    self.selfMsg(charObj, "There is nobody here to show you " +
                                 "the catalog.\n")
            elif cmd == 'repair':
                if roomObj.isRepairShop():
                    if len(cmdargs) < 2 or not isIntStr(cmdargs[1]):
                        self.selfMsg(charObj, "usage: repair <item> [#]\n")

                    playerInventory = charObj.getInventory()
                    objList = self.getObjFromCmd(playerInventory, cmdargs)

                    if len(objList) >= 1:
                        obj1 = objList[0]
                    else:
                        self.selfMsg(charObj, "Invalid item\n")
                        return(False)

                    if not obj1.canBeRepaired():
                        self.selfMsg(charObj, "This can't be repaired\n")
                        return(False)

                    price = self.calculateObjectPrice(svrObj, obj1) * 100
                    prompt = ("You are about to repair " +
                              obj1.getArticle() + " " + obj1.getName() +
                              " for " + str(price) + "shillings.  Proceed?")
                    if svrObj.promptForYN(prompt):
                        obj1.repair()
                        roomObj.recordTransaction(obj1)
                        roomObj.recordTransaction("repair/" + str(price))
                        charObj.recordTax(roomObj.getTaxAmount(price))
                        self.selfMsg(charObj, roomObj.getSuccessTxt())
                        return(True)
                    else:
                        self.selfMsg(charObj, roomObj.getAbortedTxt())
                        return(False)
                else:
                    self.selfMsg(charObj, "You need to find someone who can " +
                                 "repair your ragged items.\n")
            elif cmd == 'sell' or cmd == 'pawn':
                if roomObj.isPawnShop():
                    if len(cmdargs) < 2:
                        self.selfMsg(charObj, "usage: " + cmdargs[0] +
                                     "<item> [#]\n")
                        return(False)
                    playerInventory = charObj.getInventory()
                    objList = self.getObjFromCmd(playerInventory, cmdargs)
                    if len(objList) >= 1:
                        obj1 = objList[0]
                    else:
                        self.selfMsg(charObj, "Invalid item\n")
                        return(False)

                    price = int(self.calculateObjectPrice(svrObj, obj1) * .8)

                    # prompt player for confirmation
                    prompt = ("You are about to pawn " + obj1.getArticle() +
                              " " + obj1.getName() + " for " + str(price) +
                              " shillings.  Proceed?")
                    if svrObj.promptForYN(prompt):
                        charObj.removeFromInventory(obj1)     # remove item
                        charObj.addCoins(price)                 # tax included
                        roomObj.recordTransaction(obj1)       # update stats
                        roomObj.recordTransaction("purchase/" + str(price))
                        charObj.recordTax(roomObj.getTaxAmount(price))
                        self.selfMsg(charObj, roomObj.getSuccessTxt())
                        return(True)
                    else:
                        self.selfMsg(charObj, roomObj.getAbortedTxt())
                        return(False)
        else:
            self.selfMsg(charObj, "You can't do that here\n")
        return(False)

    def bankTransaction(self, svrObj, cmdargs):      # noqa: C901
        ''' Process commands that are related to shop transactions '''
        cmd = cmdargs[0]
        charObj = svrObj.charObj
        roomObj = charObj.getRoom()

        if roomObj.getType() == 'Shop':
            if cmd == 'balance':
                if roomObj.isBank():
                    amount = charObj.getBankBalance()
                    self.selfMsg(charObj, "Your account balance is " +
                                 str(amount) + " shillings.\n")
            elif cmd == 'deposit':
                if roomObj.isBank():
                    if len(cmdargs) < 2 or not isIntStr(cmdargs[1]):
                        self.selfMsg(charObj, "usage: deposit <amount>\n")
                        return(False)
                    # check if player has the funds
                    amount = int(cmdargs[1])
                    if not charObj.canAffordAmount(amount):
                        self.selfMsg(charObj, roomObj.getCantAffordTxt(amount))
                        return(False)

                    taxRate = roomObj.getTaxRate()
                    bankfee, dAmount = charObj.calculateBankFees(amount,
                                                                 taxRate)
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
                    if svrObj.promptForYN(prompt):
                        charObj.bankDeposit(amount, taxRate)
                        roomObj.recordTransaction("deposit/" + str(dAmount))
                        roomObj.recordTransaction("fees/" + str(bankfee))
                        self.selfMsg(charObj, roomObj.getSuccessTxt())
                        return(True)
                    else:
                        self.selfMsg(charObj, roomObj.getAbortedTxt())
                        return(False)
            elif cmd == 'withdraw':
                if roomObj.isBank():
                    if len(cmdargs) < 2 or not isIntStr(cmdargs[1]):
                        self.selfMsg(charObj, "usage: withdraw <amount>\n")
                        return(False)
                    amount = int(cmdargs[1])
                    if not charObj.canWithdraw(amount):
                        self.selfMsg(charObj, roomObj.getCantAffordTxt(amount))
                        return(False)
                    taxRate = roomObj.getTaxRate()
                    bankfee, wAmount = charObj.calculateBankFees(amount,
                                                                 taxRate)
                    prompt = ("You are about to withdraw " + str(amount) +
                              " shillings from the bank.\n")
                    if taxRate != 0:
                        prompt += ("The bank charges a " + str(taxRate) +
                                   "% withdrawl fee which comes to a " +
                                   str(bankfee) + " shilling charge.\n" +
                                   "As a result, you will receive " +
                                   str(wAmount) + " shillings.\n")
                    prompt += "Continue?"
                    if svrObj.promptForYN(prompt):
                        charObj.bankWithdraw(amount, taxRate)
                        roomObj.recordTransaction("withdrawl/" + str(wAmount))
                        roomObj.recordTransaction("fees/" + str(bankfee))
                        self.selfMsg(charObj, roomObj.getSuccessTxt())
                        return(True)
                    else:
                        self.selfMsg(charObj, roomObj.getAbortedTxt())
                        return(False)
        else:
            self.selfMsg(charObj, "You can't do that here\n")
        return(False)


# instanciate the _Game class
_game = _Game()


def Game():
    ''' return a reference to the single, existing _game instance
        Thus, when we try to instanciate Game, we are just returning
        a ref to the existing Game '''

    return(_game)
