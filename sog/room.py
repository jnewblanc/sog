''' room class '''

from datetime import datetime
import logging
import os
import pprint
# import re

from common.storage import Storage
from common.attributes import AttributeHelper
from common.general import rreplace, getNeverDate, differentDay
from common.paths import DATADIR
from object import ObjectFactory, Door


class Room(Storage, AttributeHelper):

    attributesThatShouldntBeSaved = ['gameObj', "_creatureList",   # Storage
                                     '_characterList', '_objectList']
    _instanceDebug = False

    directionNameDict = {
        "n": "north",
        "s": "south",
        "e": "east",
        "w": "west",
        "u": "up",
        "d": "down",
        "o": "out",
    }

    # int attributes
    intAttributes = ['n', 's', 'e', 'w', 'u', 'd', 'o',
                     '_encounterTime', '_roomNum']
    # boolean attributes
    boolAttributes = ['_notifyDM', '_safe', '_antiMagic', '_dark']
    # string attributes
    strAttributes = ['_shortDesc', '_desc']
    # list attributes
    listAttributes = ['_permanentCreatureList', '_permanentObjectList',
                      '_creatureList', '_characterList', '_objectList']

    # obsolete attributes (to be removed)
    obsoleteAttributes = ['notifyDM', 'safe', 'antiMagic', 'dark', 'out',
                          'priceBonus', 'encounterTime' 'encounterList']

    def __init__(self, roomNum=1):
        self._roomNum = int(roomNum)  # the room number, not seen by players
        self._shortDesc = ''     # the brief description of a room
        self._desc = ''          # the full description of a room
        self._notifyDM = False    # notify DM if someone enters this room
        self._safe = False        # players/monsters can't attack here
        self._antiMagic = False   # can't use magic spells here
        self._dark = False        # players can't see here
        self._encounterTime = 0   # average seconds between encounters
        self._encounterList = []  # list of creature numbers for encounters
        self._permanentCreatureList = []  # perm creature instances
        self._permanentObjectList = []    # perm object instances

        # These are tmp properties that get reset everytime the room is empty
        self.initTmpAttributes()

        # Standard directions - 0=none
        self.n = 0
        self.s = 0
        self.e = 0
        self.w = 0
        self.u = 0
        self.d = 0
        self.o = 1

        if self._instanceDebug:
            logging.debug("Room init called for " + str(self.getId()))
        return(None)

    def __del__(self):
        if self._instanceDebug:
            logging.debug("Room destructor called for " + str(self.getId()))

    def debug(self):
        return(pprint.pformat(vars(self)))

    def getType(self):
        return(self.__class__.__name__)

    def getWizFields(self):
        ''' Editor uses to determine which fields to prompt for '''
        return(["_shortDesc", "_desc", "n", "s", "e", "w"])

    def getInfo(self):
        buf = ''
        ROW_FORMAT = "{0:14}: {1:<30}\n"
        buf += (ROW_FORMAT.format("RoomNum", self.getRoomNum()) +
                ROW_FORMAT.format("desc", self._desc) +
                ROW_FORMAT.format("shortDesc", self._shortDesc) +
                ROW_FORMAT.format("encounterTime", self._encounterTime) +
                ROW_FORMAT.format("notifyDM", self._notifyDM) +
                ROW_FORMAT.format("safe", self._safe) +
                ROW_FORMAT.format("antiMagic", self._antiMagic) +
                ROW_FORMAT.format("dark", self._dark) +
                ROW_FORMAT.format("priceBonus", self._priceBonus) +
                ROW_FORMAT.format("n", self.n) +
                ROW_FORMAT.format("s", self.s) +
                ROW_FORMAT.format("e", self.e) +
                ROW_FORMAT.format("w", self.w) +
                ROW_FORMAT.format("u", self.u) +
                ROW_FORMAT.format("d", self.d) +
                ROW_FORMAT.format("o", self.o))

        buf += ("Encounter List:         " +
                " ".join(self.getEncounterList()) + '\n')
        buf += ("Perm Creature List:     " +
                " ".join(self.getPermanentCreatureList()) + '\n')
        buf += ("Perm Object List:       " +
                " ".join(self.getPermanentObjectList()) + '\n')
        buf += ("Current Creature List:  " +
                " ".join(self.getCreatureList()) + '\n')
        buf += ("Current Object List:    " +
                " ".join(self.getObjectList()) + '\n')
        buf += ("Current Character List: " +
                " ".join(self.getCharacterList()) + '\n')
        return(buf)

    def initTmpAttributes(self):
        ''' Reset attributes that are not supposed to persist '''
        self._creatureList = []
        self._characterList = []
        self._objectList = []
        return(True)

    def fixAttributes(self):
        ''' Sometimes we change attributes, and need to fix them in rooms
            that are saved.  This method lets us do that.  First we call
            the generic superClass fixAttributes to fix the types and remove
            obsolete vars.  Here, we can also add class specific logic for
            copying values from one attribute to another, etc '''

        try:
            self.o = self.out  # stop using "out" and instead use "o"
            logging.debug("Room - translating 'out' to 'o' self.o=" + self.o)
        except (AttributeError, TypeError):
            pass

        AttributeHelper.fixAttributes(self)

    def isValid(self):
        if ((self.getRoomNum() > 0 and self._shortDesc != '' and
             self._desc != '')):
            return(True)
        return(False)

    def deletePlayer(self, roomNum, charObj):
        ''' remove player from a room - destroy room instance if needed '''
        # clean up room if needed
        charObj.setRoom(roomNum)
        # stop creatures attack of the player
        return(None)

    def insertCreature(self, creature, svrObj):
        self._creatureList.append(creature)
        svrObj.spoolOut(creature + 'has entered the room')
        return(None)

    def cleanRoom(self):
        self.loadPermanents()
        # Restore permanentCreatures health
        return(None)

    def displayDescription(self, charObj):
        buf = ''

        if charObj.isDm():  # DM can see room ID
            buf += "(" + str(self.getRoomNum()) + ") "

        if self.getRoomNum() == 0 or self._shortDesc == "":
            buf += "You are in a non descript room with no exits."
            return(buf)

        if self._dark:
            if not charObj.canSeeInTheDark():
                buf += "It's too dark to see anything."
                return(buf)

        if charObj.getPromptSize() == 'brief':
            buf += "You are " + self._shortDesc + '\n'
        else:
            buf += "You are " + self._desc + '\n'
        return(buf)

    def displayExits(self, charObj):
        buf = ''

        # show adjoining rooms
        exitTxt = ''
        for direction in self.directionNameDict.keys():
            if getattr(self, direction) != 0:
                exitTxt += self.directionNameDict[direction]
                if charObj.isDm():     # DM can see exit Ids
                    exitTxt += ("(" + str(self.getRoomNumForExit(direction)) +
                                ")")
                exitTxt += ', '
        exitTxt = exitTxt.rstrip(', ')
        if exitTxt != '':
            buf += "Obvious exits are " + exitTxt + ".\n"
        return(buf)

    def dmTxt(self, charObj, msg):
        ''' return the given msg only if the character is a DM '''
        if charObj.isDm():
            return(msg)
        return('')

    def displayItems(self, charObj):     # noqa C901
        ''' show items in current room '''
        buf = ''

        sightList = ''

        # show creatures, objects, and players
        for onecreature in self.getCreatureList():
            dmInfo = '(' + str(onecreature.getId()) + ')'
            if onecreature.isInvisible():
                dmInfo += "[INV]"
            if onecreature.isHidden():
                dmInfo += "[HID]"
            if (((onecreature.isInvisible() and not charObj.canSeeInvisible())
                 or (onecreature.isHidden() and not charObj.canSeeHidden()))):
                pass
            else:
                sightList += (onecreature.getName() +
                              self.dmTxt(charObj, dmInfo) + ", ")

        for obj in self.getObjectList():
            dmInfo = '(' + str(obj.getId()) + ')'
            if obj.isInvisible():
                dmInfo += "[INV]"
            if obj.isHidden():
                dmInfo += "[HID]"
            if (((obj.isInvisible() and not charObj.canSeeInvisible())
                 or (obj.isHidden() and not charObj.canSeeHidden()))):
                pass
            else:
                sightList += (obj.describe() + self.dmTxt(charObj, dmInfo) +
                              ", ")

        # toDo: compact lists by grouping duplicates as plurals

        if sightList != '':
            # Pretty up the list of objects/creatures to make it more readable
            sightList = sightList.rstrip(', ')
            if sightList.count(', ') > 2:
                andTxt = ', and '
            else:
                andTxt = ' and '
            sightList = rreplace(sightList, ', ', andTxt)
            buf += "  You see " + sightList + ".\n"

        return(buf)

    def displayPlayers(self, charObj):
        ''' show players in current room '''
        buf = ''
        # show players
        otherPlayerList = []
        for oneplayer in self.getCharacterList():
            if oneplayer == charObj:
                pass                       # ignore yourself
            elif oneplayer.isInvisible():
                if charObj.isDM():
                    otherPlayerList.append(oneplayer.getName() + "(INV)")
            elif oneplayer.isHidden():
                if charObj.isDM():
                    otherPlayerList.append(oneplayer.getName() + "(HID)")
            else:
                otherPlayerList.append(oneplayer.getName())
        if len(otherPlayerList) == 1:     # one other player
            buf += otherPlayerList[0] + " is also here.\n"
        elif len(otherPlayerList) > 1:  # multiple other players
            all_but_last = ', '.join(otherPlayerList[:-1])
            last = otherPlayerList[-1]
            buf += ' & '.join([all_but_last, last])
            buf += " are also here.\n"
        return(buf)

    def displayAttackers(self, charObj):
        ''' show attackers in current room '''

        buf = ''
        # show attackers
        for onecreature in self.getCreatureList():
            if onecreature.attacking != '':
                buf = (buf + onecreature.name + ' is attacking ' +
                       onecreature.attacking)

        # show who you are attacking
        for creature in charObj.getAttacking():
            buf += 'You\'re attacking ' + creature.getName()

        # todo: show other players who are attacking each other
        return(buf)

    def describe(self, charObj):
        ''' alias for display '''
        return(self.display(charObj))

    def display(self, charObj):
        ''' show all player visible info about current room '''
        buf = ''

        buf += self.displayDescription(charObj)
        buf += self.displayExits(charObj)
        buf += self.displayItems(charObj)
        buf += self.displayPlayers(charObj)
        buf += self.displayAttackers(charObj)

        return(buf)

    def getDataFilename(self):
        ''' returns the filename of self.roomNum '''
        filename = ''

        if isinstance(self.getRoomNum(), int):
            filename = os.path.abspath(DATADIR + "/room/" +
                                       str(self.getRoomNum()) +
                                       '.pickle')
        return(filename)

    def postLoad(self):
        ''' Called by the loader - can be used for room initialization '''

        self.initTmpAttributes()
        self.loadPermanents()
        self.closeSpringDoors()
        return(True)

    def getId(self):
        return(self.getRoomNum())

    def getRoomNum(self):
        return(self._roomNum)

    def setRoomNum(self, num):
        self._roomNum = int(num)

    def getRoomNumForExit(self, exitStr):
        ''' Return the room number for a given exit '''
        return(getattr(self, exitStr))

    def getExits(self):
        ''' Returns a dict with direction as key and room numbers as val '''
        exitDict = {}
        for direction in self.directionNameDict.keys():
            exitDict[direction] = getattr(self, direction)
        return(exitDict)

    def getExit(self, dirIn):
        ''' Given a direction, return a room number, or 0 if none '''
        if self.IsDirection():
            return(getattr(self, dirIn))
        return(0)

    def isDirection(self, inStr):
        ''' Return true if string is any of the possible directions '''
        if inStr in self.directionNameDict.keys():
            return(True)
        return(False)

    def getAllObjects(self):
        ''' Returns a list of all objects '''
        return(list(self.getObjectList()))

    def getDoorsAndPortals(self):
        ''' returns a list of door and portal objects '''
        dpList = []
        for oneobj in self.getAllObjects():
            if oneobj.type == 'portal' or oneobj.type == 'door':
                dpList.append(oneobj)
        return(dpList)

    def getCharacterList(self):
        ''' return list of characters in room '''
        return self._characterList

    def addCharacter(self, charObj):
        ''' add character to list of characters in room '''
        self._characterList.append(charObj)

    def removeCharacter(self, charObj):
        ''' remove character to list of characters in room '''
        if charObj in self._characterList:
            self._characterList.remove(charObj)

    def getCreatureList(self):
        ''' return list of creatures in room '''
        return self._creatureList

    def addCreature(self, creatureObj):
        ''' add creature to list of creatures in room '''
        self._creatureList.append(creatureObj)

    def removeCreature(self, creatureObj):
        ''' remove creature to list of creatures in room '''
        if creatureObj in self._creatureList:
            self._creatureList.remove(creatureObj)

    def getObjectList(self):
        ''' return list of objects in room '''
        return self._objectList

    def addObject(self, itemObj):
        ''' add object to list of objects in room '''
        self._objectList.append(itemObj)

    def removeObject(self, itemObj):
        ''' remove object to list of objects in room '''
        if itemObj in self._objectList:
            self._objectList.remove(itemObj)

    def getPermanentCreatureList(self):
        ''' return list of permanentCreature IDs for room '''
        return self._permanentCreatureList

    def addPermanentCreature(self, creatureId):
        ''' add creature to list of permanentCreature Ids for room '''
        self._permanentCreatureList.append(creatureId)

    def removePermanentCreature(self, creatureId):
        ''' remove creature from list of permanentCreature IDs for room '''
        if creatureId in self._permanentCreatureList:
            self._permanentCreatureList.remove(creatureId)

    def getPermanentObjectList(self):
        ''' return list of permanentObjects in room '''
        return self._permanentObjectList

    def addPermanentObject(self, itemObj):
        ''' add object to list of permanentObjects in room '''
        self._permanentObjectList.append(itemObj)

    def removePermanentObject(self, itemObj):
        ''' remove object from list of permanentObjects in room '''
        if itemObj in self._permanentObjectList:
            self._permanentObjectList.remove(itemObj)

    def getEncounterList(self):
        ''' return list of creature numbers for room '''
        return self._encounterList

    def addEncounterList(self, num):
        ''' add num to list of encounters for room - used for room editing '''
        self._encounterList.append(num)

    def removeEncounterList(self, num):
        ''' remove num from list of encounters for room - used for editing '''
        if num in self._encounterList:
            self._encounterList.remove(num)

    def resetEncounterList(self):
        ''' remove all nums from encounters list - used for editing '''
        self._encounterList = []

    def loadPermanents(self):
        ''' Load/instanciate permanents, and add them to the tmp lists '''
        pcl = self.getPermanentCreatureList()
        pol = self.getPermanentObjectList()
        if len(pcl):
            self._creatureList = self.getPermanents(pcl)
        if len(pol):
            self._objectList = self.getPermanents(pol)
        return(True)

    def getPermanents(self, idList=[]):
        ''' Returns a list of objects for the corresponding object IDs '''
        objList = []
        for permId in idList:
            oneObj = self.getPermanent(permId)
            if oneObj:
                objList.append(oneObj)
            else:
                logging.debug("Could not add permanent " + permId + ' to list')
        return(objList)

    def getPermanent(self, permId):
        ''' Returns an object, given the objectID '''
        oneObj = None
        (objType, objId) = permId.split('/')
        oneObj = ObjectFactory(objType, objId)

        if oneObj:
            if oneObj.load():
                return(oneObj)
        return(None)

    def savePermanents(self):
        ''' save permanents to disk '''
        for obj in self.getObjectList():
            if obj.isPermanent():
                obj.save()
        return(True)

    def reloadPermanentObject(self, objId):
        ''' reload a permanent from disk, replacing the original
            * if a door changes state, we'll need to reload it '''
        for oneObj in self._objectList:
            if oneObj.getId() == objId:
                oneObj.load()
        return(True)

    def closeSpringDoors(self):
        for obj in self.getObjectList():
            if isinstance(obj, Door):
                if obj.hasSpring():
                    obj.close()


class Shop(Room):
    def __init__(self, roomNum=1):
        super().__init__(roomNum)
        self._pawnshop = False    # can sell items here
        self._bank = False        # can bank here
        self._repair = False      # can repair items here
        self._priceBonus = 100    # percent to raise/lower prices
        self._catalog = []        # items that are sold here, if any

        self._lastTransactionDate = getNeverDate()
        self._totalTransactionCount = {}
        self._dailyTransactionCount = {}

        for itemStr in self._catalog:
            self._totalTransactionCount[itemStr] = 0
            self._dailytransactionCount[itemStr] = 0

        self._totalCoinLedger = {'deposit': 0, 'withdraw': 0,
                                 'purchase': 0, 'sale': 0, 'repair': 0}
        self._dailyCoinLedger = {'deposit': 0, 'withdraw': 0,
                                 'purchase': 0, 'sale': 0, 'repair': 0}

        # Responses can be overwritten, depending on the flavor of shopkeep
        self._successfulTransactionTxt = "Thank you.  Please come again"
        self._abortedTransactionTxt = "Maybe next time"
        self._cantAffordTxt = "You have insufficient funds for that"
        self._cantCarryTxt = ("You would not be able to carry this " +
                              "additional item")

    def isVendor(self):
        if len(self.getcatalog()) > 0:
            return(True)
        return(False)

    def isRepairShop(self):
        return(self._repairhere)

    def isPawnShop(self):
        return(self._pawnshop)

    def isBank(self):
        return(self._bank)

    def getcatalog(self):
        return(self._catalog)

    def getPriceBonus(self):
        return(self._priceBonus)

    def getCantAffordTxt(self, cost=0):
        return(self._cantAffordTxt + "\n")

    def getCantCarryTxt(self, weight=0):
        return(self._cantCarryTxt + "\n")

    def getSuccessTxt(self):
        return(self._successfulTransactionTxt + "\n")

    def getAbortedTxt(self):
        return(self._abortedTransactionTxt + "\n")

    def getTransactions(self):
        return(self._dailyTransactionCount, self._totalTransactionCount,
               self._dailyCoinLedger, self._totalCoinLedger)

    def getTaxRate(self):
        taxrate = max(0, (100 - self.getPriceBonus()))
        return(taxrate)

    def getTaxAmount(self, amount):
        taxes = int(int(amount) * self.getTaxRate())
        return(taxes)

    def recordTransaction(self, item):
        ''' Everytime a buy/sell/repair is done, use this to update stats '''
        if differentDay(datetime.now(), self._lastTransactionDate):
            self._dailyTransactionCount = {}         # reset daily counts
            self._dailyCoinLedger = {}

        if isinstance(item, str):
            ''' This keeps track of totals funds '''
            itemStr, itemAmount = item.split('/')  # i.e. deposit/345560

            if itemStr and itemAmount:
                if itemStr in self._totalCoinLedger.keys():  # incr totals
                    self._totalCoinLedger[itemStr] += int(itemAmount)
                else:
                    self._totalCoinLedger[itemStr] = int(itemAmount)

                if itemStr in self._dailyCoinLedger.keys():  # incr daily
                    self._dailyCoinLedger[itemStr] += int(itemAmount)
                else:
                    self._dailyCoinLedger[itemStr] = int(itemAmount)
        else:
            ''' This keeps track of item totals '''
            itemStr = item.__class__.__name__ + '/' + str(item.getId())

            if itemStr in self._totalTransactionCount.keys():  # incr totals
                self._totalTransactionCount[itemStr] += 1
            else:
                self._totalTransactionCount[itemStr] = 1

            if itemStr in self._dailyTransactionCount.keys():  # incr daily
                self._totalTransactionCount[itemStr] += 1
            else:
                self._dailyTransactionCount[itemStr] = 1

        self._lastTransactionDate = datetime.now()  # store date of transaction
        self.save()                                 # save the room

    def adjustPrice(self, price):
        ''' Adjust the price of goods depending on room attributes
            * non-room price changes occur elsewhere '''
        price *= (self._priceBonus / 100)
        return(int(price))


def RoomFactory(objType="room", id=0):
    ''' Factory method to return the correct object, depending on the type '''
    obj = None

    if objType.lower() == "room":
        obj = Room(id)
    elif objType.lower() == "shop":
        obj = Shop(id)

    if not obj.getId():
        logging.error("RoomFactory: Could not obtain id for newly" +
                      "instanciated " + objType + " object")

    return(obj)
