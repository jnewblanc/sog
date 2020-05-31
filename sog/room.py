""" room class """

from datetime import datetime, timedelta
import os
import pprint
import random

# import re
import textwrap

from common.storage import Storage
from common.attributes import AttributeHelper
from common.general import getNeverDate, differentDay, secsSinceDate, dateStr
from common.general import logger, dLog
from common.inventory import Inventory
from common.item import Item
from common.globals import DATADIR
from object import ObjectFactory, Door, isObjectFactoryType
from creature import Creature


class Room(Item):

    _instanceDebug = False

    _fileextension = ".json"

    _baseEncounterTime = 60

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
    intAttributes = list(directionNameDict.keys()) + ["_encounterRate", "_roomNum"]
    # boolean attributes
    boolAttributes = ["_notifyDM", "_safe", "_antiMagic", "_dark"]
    # string attributes
    strAttributes = ["_shortDesc", "_desc"]
    # list attributes
    listAttributes = ["_permanentList", "_inventory", "_characterList"]

    # obsolete attributes (to be removed)
    obsoleteAttributes = [
        "notifyDM",
        "safe",
        "antiMagic",
        "dark",
        "out",
        "priceBonus",
        "encounterTime",
        "encounterList",
        "_objectlist",
        "_creatureList",
        "gameObj",
        "_encounterTime",
        "_permanentCreatureList",
        "_permanentObjectList",
    ]

    attributesThatShouldntBeSaved = [
        "_creatureList",
        "_instanceDebug",
        "_characterList",
        "_objectList",
        "_timeOfLastAttack",
        "_creatureCache",
        "_timeOfLastEncounter",
        "_invWeight",
        "_maxweight",
        "_invValue",
    ]

    wizardAttributes = [
        "_shortDesc",
        "_desc",
        "n",
        "s",
        "e",
        "w",
        "_encounterRate",
    ]

    attributeInfo = {
        "_shortDesc": "short room description when brief prompt is used",
        "_desc": "full room description when normal prompt is used",
        "n": "the room in the north direction (0 for none)",
        "s": "the room in the south direction (0 for none)",
        "e": "the room in the east direction (0 for none)",
        "w": "the room in the west direction (0 for none)",
        "_encounterRate": "Percentage of typical encounter time ",
    }

    def __init__(self, roomNum=1):
        self._roomNum = int(roomNum)  # the room number, not seen by players

        super().__init__()
        Storage.__init__(self)
        Inventory.__init__(self)

        self._shortDesc = ""  # the brief description of a room
        self._desc = ""  # the full description of a room
        self._notifyDM = False  # notify DM if someone enters this room
        self._safe = False  # players/monsters can't attack here
        self._antiMagic = False  # can't use magic spells here
        self._dark = False  # players can't see here
        self._encounterRate = 100  # average seconds between encounters
        self._encounterList = []  # list of creature numbers for encounters
        self._permanentList = []  # perm object instances
        self._timeOfLastEncounter = getNeverDate()
        self._timeOfLastAttack = getNeverDate()
        self._instanceDebug = Room._instanceDebug

        # Override the inventory class  - Set the number of items allowed in
        self.setInventoryTruncSize(12)  # room before the items roll away

        # These are tmp properties that get reset everytime the room is empty
        self.initTmpAttributes()

        # Standard directions - 0=none
        self.n = 0
        self.s = 0
        self.e = 0
        self.w = 0
        self.u = 0
        self.d = 0
        self.o = 0

        if self._instanceDebug:
            logger.debug("Room init called for " + str(self.getId()))
        return None

    def __del__(self):
        if self._instanceDebug:
            logger.debug("Room destructor called for " + str(self.getId()))

    def debug(self):
        return pprint.pformat(vars(self))

    def toggleInstanceDebug(self):
        self._instanceDebug = not self._instanceDebug

    def getInstanceDebug(self):
        return self._instanceDebug

    def setInstanceDebug(self, val):
        self._instanceDebug = bool(val)

    def getType(self):
        return self.__class__.__name__

    def getInfo(self):
        buf = ""
        ROW_FORMAT = "{0:14}: {1:<30}\n"
        roomNumName = self.getType() + "Num"
        buf += (
            ROW_FORMAT.format(roomNumName, self.getRoomNum())
            + ROW_FORMAT.format("type", self.getType())
            + ROW_FORMAT.format("desc", self._desc)
            + ROW_FORMAT.format("shortDesc", self._shortDesc)
        )

        buf += (
            ROW_FORMAT.format("n", self.n)
            + ROW_FORMAT.format("s", self.s)
            + ROW_FORMAT.format("e", self.e)
            + ROW_FORMAT.format("w", self.w)
            + ROW_FORMAT.format("u", self.u)
            + ROW_FORMAT.format("d", self.d)
            + ROW_FORMAT.format("o", self.o)
        )

        buf += (
            ROW_FORMAT.format("encounterRate", self._encounterRate)
            + ROW_FORMAT.format("notifyDM", self._notifyDM)
            + ROW_FORMAT.format("safe", self._safe)
            + ROW_FORMAT.format("antiMagic", self._antiMagic)
            + ROW_FORMAT.format("dark", self._dark)
        )

        if self.getType() == "Shop":
            buf += self.shopGetInfo()

        if self.getType() == "Guild":
            buf += self.guildGetInfo()

        buf += "Encounter List:         " + ", ".join(self.getEncounterList()) + "\n"
        buf += "Permanent List:       " + ", ".join(self.getPermanentList()) + "\n"
        buf += (
            "Current Inventory:  "
            + ", ".join([x.describe() for x in self.getInventory()])
            + "\n"
        )
        buf += (
            "Current Character List: "
            + ", ".join([x.describe() for x in self.getCharacterList()])
            + "\n"
        )
        return buf

    def initTmpAttributes(self):
        """ Reset attributes that are not supposed to persist """
        self._characterList = []
        # self._inventory = []
        self._creatureCache = []
        # Accelerate first encounter by mucking with the last encounter time
        secsToReduceLastEncounter = random.randint(0, 60)
        self.setLastEncounter(secsToReduceLastEncounter)
        return True

    def fixAttributes(self):
        """ Sometimes we change attributes, and need to fix them in rooms
            that are saved.  This method lets us do that.  First we call
            the generic superClass fixAttributes to fix the types and remove
            obsolete vars.  Here, we can also add class specific logic for
            copying values from one attribute to another, etc """

        try:
            self.o = self.out  # stop using "out" and instead use "o"
        except (AttributeError, TypeError):
            pass
        try:
            self._encounterRate = self._encounterTime
        except (AttributeError, TypeError):
            pass
        try:
            self._permanentList = self._permanentObjectList
        except (AttributeError, TypeError):
            pass

        AttributeHelper.fixAttributes(self)

    def isBank(self):
        return False

    def isPawnShop(self):
        return False

    def isRepairShop(self):
        return False

    def isSafe(self):
        return self._safe

    def isTrainingGround(self):
        return False

    def isValid(self):
        if self.getRoomNum() > 0 and self._shortDesc != "" and self._desc != "":
            return True
        return False

    def isVendor(self):
        return False

    def creatureCachePush(self, creaObj):
        """ Populate the creature Cache """
        self._creatureCache.append(creaObj)

    def getCreatureCache(self):
        """ Return the creature cache """
        return self._creatureCache

    def deletePlayer(self, roomNum, charObj):
        """ remove player from a room - destroy room instance if needed """
        # clean up room if needed
        charObj.setRoom(roomNum)
        # stop creatures attack of the player
        return None

    def cleanRoom(self):
        self.loadPermanents()
        # Restore permanentCreatures health
        return None

    def displayDescription(self, charObj):
        buf = ""

        if charObj.isDm():  # DM can see room ID
            buf += "(" + str(self.getRoomNum()) + ") "

        if self.getRoomNum() == 0 or self._shortDesc == "":
            buf += "You are in a non descript room with no exits.\n"
            return buf

        if self._dark:
            if not charObj.canSeeInTheDark():
                buf += "It's too dark to see anything.\n"
                return buf

        if charObj.getPromptSize() == "brief":
            buf += "You are " + self._shortDesc
        else:
            buf += "You are " + self._desc
        return textwrap.fill(buf, width=80) + "\n"

    def displayExits(self, charObj):
        buf = ""

        # show adjoining rooms
        exitTxt = ""
        for direction in self.directionNameDict.keys():
            if getattr(self, direction) != 0:
                exitTxt += self.directionNameDict[direction]
                if charObj.isDm():  # DM can see exit Ids
                    exitTxt += "(" + str(self.getRoomNumForExit(direction)) + ")"
                exitTxt += ", "
        exitTxt = exitTxt.rstrip(", ")
        if exitTxt != "":
            buf += "Obvious exits are " + exitTxt + "." + "\n"
        return buf

    def displayExtra(self, charObj):
        """ Subclasses can override this, to get their messages inserted """
        msg = ""
        return msg

    def displayItems(self, charObj):  # noqa C901
        """ show items in current room """
        buf = self.describeInvAsList(
            showDm=charObj.isDm(),
            showHidden=charObj.canSeeHidden(),
            showInvisible=charObj.canSeeInvisible(),
            sortList=False,
        )
        dLog("displayItems:" + buf, False)
        if buf != "":
            buf = "You see " + buf
        return buf

    def displayPlayers(self, charObj):
        """ show players in current room """
        buf = ""
        # show players
        otherPlayerList = []
        for oneplayer in self.getCharacterList():
            if oneplayer == charObj:
                pass  # ignore yourself
            elif oneplayer.isInvisible():
                if charObj.isDM():
                    otherPlayerList.append(oneplayer.getName() + "(INV)")
            elif oneplayer.isHidden():
                if charObj.isDM():
                    otherPlayerList.append(oneplayer.getName() + "(HID)")
            else:
                otherPlayerList.append(oneplayer.getName())
        if len(otherPlayerList) == 1:  # one other player
            buf += otherPlayerList[0] + " is also here.\n"
        elif len(otherPlayerList) > 1:  # multiple other players
            all_but_last = ", ".join(otherPlayerList[:-1])
            last = otherPlayerList[-1]
            buf += " & ".join([all_but_last, last])
            buf += " are also here.\n"
        return buf

    def displayAttackers(self, charObj):
        """ show attackers in current room """

        buf = ""
        # show attackers
        for onecreature in self.getCreatureList():
            if onecreature.isAttacking():
                target = onecreature.getCurrentlyAttacking()
                buf += onecreature.describe() + " is attacking "
                if target == charObj:
                    buf += "you\n"
                else:
                    buf += target.getName() + "\n"

        # show who you are attacking
        for creature in charObj.getAttacking():
            buf += "You are attacking " + creature.describe()

        # todo: show other players who are attacking each other
        return buf

    def describe(self, count=1, article=""):
        """ show the room number """
        return self.getType() + " " + str(self._roomNum)

    def display(self, charObj):
        """ show all player visible info about current room """
        buf = ""

        buf += self.displayDescription(charObj)
        buf += self.displayExtra(charObj)
        buf += self.displayExits(charObj)
        buf += self.displayItems(charObj)
        buf += self.displayPlayers(charObj)
        buf += self.displayAttackers(charObj)

        return buf

    def setDataFilename(self):
        """ sets the filename of the room """
        filename = ""

        if hasattr(self, "_fileextension"):
            extension = self._fileextension
        else:
            extension = ".pickle"

        if isinstance(self.getRoomNum(), int):
            roomType = getRoomTypeFromFile(self.getRoomNum(), extension)
            filename = os.path.abspath(
                DATADIR
                + "/"
                + roomType.capitalize()
                + "/"
                + str(self.getRoomNum())
                + extension
            )

        if filename != "":
            self._datafile = filename

    def postLoad(self):
        """ Called by the loader - can be used for room initialization """

        self.initTmpAttributes()
        self.removeNonPermanents(removeTmpPermFlag=True)
        self.loadPermanents()
        self.closeSpringDoors()
        return True

    def getId(self):
        return self.getRoomNum()

    def getRoomNum(self):
        return self._roomNum

    def setRoomNum(self, num):
        self._roomNum = int(num)

    def getRoomNumForExit(self, exitStr):
        """ Return the room number for a given exit """
        return getattr(self, exitStr)

    def getExits(self):
        """ Returns a dict with direction as key and room numbers as val """
        exitDict = {}
        for direction in self.directionNameDict.keys():
            exitDict[direction] = getattr(self, direction)
        return exitDict

    def getExit(self, dirIn):
        """ Given a direction, return a room number, or 0 if none """
        if self.IsDirection():
            return getattr(self, dirIn)
        return 0

    def isDirection(self, inStr):
        """ Return true if string is any of the possible directions """
        if inStr in self.directionNameDict.keys():
            return True
        return False

    def getDoorsAndPortals(self):
        """ returns a list of door and portal objects """
        dpList = []
        for oneobj in self.getInventory():
            if oneobj.type == "portal" or oneobj.type == "door":
                dpList.append(oneobj)
        return dpList

    def getCharsAndInventory(self):
        """ returns mixed list of items, creatures, and chars in room """
        return self.getInventory() + self.getCharacterList()

    def getCharacterList(self):
        """ return list of characters in room """
        return self._characterList

    def addCharacter(self, charObj):
        """ add character to list of characters in room """
        self._characterList.append(charObj)

    def removeCharacter(self, charObj):
        """ remove character to list of characters in room """
        if charObj in self._characterList:
            self._characterList.remove(charObj)

    def getCreatureList(self):
        """ return list of creatures in room """
        creatureList = []
        for obj in self.getInventory():
            if obj.getType() == "Creature":
                creatureList.append(obj)
        return creatureList

    def addCreature(self, creatureObj):
        """ add creature to list of creatures in room """
        self.addToInventory(creatureObj)

    def removeCreature(self, creatureObj):
        """ remove creature to list of creatures in room """
        self.removeFromInventory(creatureObj)

    def addObject(self, itemObj):
        """ add object to list of objects in room """
        self.addToInventory(itemObj)

    def removeObject(self, itemObj):
        """ remove object to list of objects in room """
        self.removeFromInventory(itemObj)

    def getPermanentList(self):
        """ return list of permanent in room """
        return self._permanentList

    def addPermanent(self, itemObj):
        """ add object to list of permanents in room """
        self._permanentList.append(itemObj)

    def removePermanent(self, itemObj):
        """ remove object from list of permanents in room """
        if itemObj in self._permanentList:
            self._permanentList.remove(itemObj)

    def getEncounterList(self):
        """ return list of creature numbers for room """
        return self._encounterList

    def addEncounterList(self, num):
        """ add num to list of encounters for room - used for room editing """
        self._encounterList.append(num)

    def removeEncounterList(self, num):
        """ remove num from list of encounters for room - used for editing """
        if num in self._encounterList:
            self._encounterList.remove(num)

    def resetEncounterList(self):
        """ remove all nums from encounters list - used for editing """
        self._encounterList = []

    def loadPermanents(self):
        """ Load/instanciate permanents, and add them to the tmp lists """
        idsOfPermsInRoom = [x.getItemId() for x in self.getInventory()]
        permList = self.getPermanentList()
        for perm in self.getPermanents(permList):
            permId = perm.getItemId()
            if permId not in idsOfPermsInRoom:
                dLog(
                    "loadPermanents: loading perm =" + str(permId), self._instanceDebug,
                )
                self.addToInventory(perm)
            else:
                dLog(
                    "loadPermanents: perm " + str(permId) + " already exists in room",
                    self._instanceDebug,
                )
        return True

    def getPermanents(self, idList=[]):
        """ Returns a list of objects for the corresponding object IDs """
        objList = []
        for permId in idList:
            oneObj = self.getPermanent(permId)
            if oneObj:
                objList.append(oneObj)
            else:
                logger.error("Could not add permanent " + permId + " to list")
        return objList

    def getPermanent(self, permId):
        """ Returns an object, given the objectID """
        itemObj = None
        (objType, objId) = permId.split("/")

        if objType.lower() == "creature":
            itemObj = Creature(objId)
        elif isObjectFactoryType(objType.lower()):
            itemObj = ObjectFactory(objType, objId)
        else:
            logger.error("Can not determine object type.")
            return None

        if itemObj:
            if itemObj.load():
                return itemObj
            else:
                logger.error(
                    "Could not load object "
                    + permId
                    + " with type "
                    + itemObj.getType()
                )
        else:
            logger.error(
                "Could not instanciate object "
                + permId
                + " with type="
                + objType
                + "and id="
                + str(objId)
            )

        return None

    def reloadPermanent(self, objId):
        """ reload a permanent from disk, replacing the original
            * if a door changes state, we'll need to reload it """
        for oneObj in self.getInventory():
            if oneObj.getId() == objId:
                oneObj.load()
        return True

    def removeNonPermanents(self, removeTmpPermFlag=False):
        """ remove any non permanents from inventory """
        logPrefix = "removeNonPermanents: " + str(self) + str(self.getItemId()) + ": "
        itemsInRoom = self.getInventory().copy()

        if removeTmpPermFlag:
            dLog(
                logPrefix
                + "inv= "
                + " ,".join(
                    [
                        x.getItemId() + "(" + str(x.persistsThroughOneRoomLoad()) + ")"
                        for x in itemsInRoom
                    ]
                ),
                self._instanceDebug,
            )

        for obj in itemsInRoom:
            if obj.persistsThroughOneRoomLoad():
                if removeTmpPermFlag:
                    # Do not remove object - let it be for one room load, but
                    # remove the property that permits this.
                    obj.setPersistThroughOneRoomLoad(False)
                    dLog(
                        logPrefix
                        + "Preserving tmpPermanent "
                        + str(obj.getItemId())
                        + " but removing persist flag",
                        self._instanceDebug,
                    )
            elif obj.isPermanent():
                # Object is permanent.  Don't remove it.
                dLog(
                    logPrefix + "Preserving permanent " + obj.getItemId(),
                    self._instanceDebug,
                )
            else:
                dLog(
                    logPrefix + "Removing non-permanent " + obj.getItemId(),
                    self._instanceDebug,
                )
                self.removeFromInventory(obj)
                self.save()
        return True

    def closeSpringDoors(self):
        for obj in self.getInventory():
            if isinstance(obj, Door):
                if obj.hasSpring():
                    obj.close()

    def readyForEncounter(self):
        """ returns true if the room is ready for an encounter """
        debugPrefix = "Room readyForEncounter (" + str(self.getId()) + "): "

        # Room has no encounter time.  Will never be ready
        if not self._encounterRate:
            dLog(debugPrefix + "Room has no encounter rate", self._instanceDebug)
            return False

        # Room has no encounter list.  Will never be ready
        if not self._encounterList:
            dLog(debugPrefix + "Room has no creatureList", self._instanceDebug)
            return False

        # Check if the appropriate amount of time has pased
        if self._timeOfLastEncounter != getNeverDate():
            secsSinceLastEncounter = secsSinceDate(self._timeOfLastEncounter)
            pctRateAdj = (self._encounterRate - 100) / 100
            secsAdj = self._baseEncounterTime * pctRateAdj + random.randint(-5, 5)
            secsBetweenEncounters = self._baseEncounterTime - secsAdj
            timeLeft = int(secsBetweenEncounters - secsSinceLastEncounter)
            if timeLeft > 0:
                dLog(
                    debugPrefix
                    + "Encounter discarded due to time - "
                    + str(timeLeft)
                    + " secs left",
                    self._instanceDebug,
                )
                return False

        # % chance that room will have no encounter this time
        if random.randint(1, 5) == 5:
            self.setLastEncounter()
            dLog(
                debugPrefix + "Encounter randomly discarded", self._instanceDebug,
            )
            return False

        dLog(debugPrefix + "Room is ready for encounter", self._instanceDebug)
        return True

    def setLastEncounter(self, secs=0):
        self._timeOfLastEncounter = datetime.now() - timedelta(seconds=secs)

    def setLastAttackDate(self):
        self._timeOfLastAttack = datetime.now()

    def getBlockingCreatures(self, charObj):
        """ Returns a blocking creature in the room, if any
            * blocking is an attacking creature with blocking attribute set """
        creatureList = []
        for creatureObj in self.getInventoryByType("Creature"):
            if creatureObj.getCurrentlyAttacking() == charObj:
                if creatureObj.blocksFromLeaving():
                    if random.randint(0, 1):  # 50% chance per creature
                        creatureList.append(creatureObj)
        return creatureList

    def getGuardingCreature(self):
        """ Returns a guarding creature in the room, if any
            * guarding is any creature with guarding attribute set """
        for creatureObj in self.getInventoryByType("Creature"):
            if creatureObj.guardsTreasure():
                return creatureObj
        return None

    def canBeJoined(self, charObj, blockPercent=50):
        """ returns true if a given room can be joined """
        blockingCreatureObjs = self.getBlockingCreatures(charObj)
        blockPercent = 50
        for blockingCreatureObj in blockingCreatureObjs:
            if random.randint(0, 100) <= blockPercent:
                charObj.client.spoolOut(
                    blockingCreatureObj.describe() + " blocks your way.\n"
                )
            return False
        return True

    def getAllAdjacentRooms(self):
        """ Returns a list of room numbers that are accessible from room """
        roomNumList = []

        # Add directional Exits
        roomNumList += list(self.getExits().values())

        # Get rooms connected by a portal or door
        for obj in self.getInventory():
            type = obj.getType()
            if type == "Door" or type == "Portal":
                roomNum = obj.getToWhere()
                if roomNum:
                    roomNumList.append(roomNum)

        # remove dups
        set(roomNumList)

        # remove current room from list
        if self.getId() in roomNumList:
            roomNumList.remove(self.getId())

        # filter out any non-room room numbers (i.e. roomNum = 0)
        roomNumList = list(filter(lambda x: x != 0, set(roomNumList)))

        return roomNumList

    # End of Room class


class Shop(Room):

    wizardAttributes = Room.wizardAttributes + [
        "_pawnshop",
        "_bank",
        "_repair",
        "_priceBonus",
    ]

    S_ROW_FORMAT = "{0:14}: {1:<30}\n"

    def __init__(self, roomNum=1):
        super().__init__(roomNum)
        self._pawnshop = False  # can sell items here
        self._bank = False  # can bank here
        self._repair = False  # can repair items here
        self._priceBonus = 100  # percent to raise/lower prices
        self._catalog = []  # items that are sold here, if any
        self._isShop = True

        # Set some defaults
        self._safe = True  # Shops are safe, by default.  Can be changed
        self._encounterRate = 20  # Super slow encounter rate by default

        # Canned responses can be overwritten, depending on flavor of shopkeep
        self._successfulTransactionTxt = "Thank you.  Please come again"
        self._abortedTransactionTxt = "Maybe next time"
        self._cantAffordTxt = "You have insufficient funds for that"
        self._cantCarryTxt = "You would not be able to carry this " + "additional item"

        # auto generated attributes
        self._lastTransactionDate = getNeverDate()
        self._totalTransactionCount = {}
        self._dailyTransactionCount = {}

        for itemStr in self._catalog:
            self._totalTransactionCount[itemStr] = 0
            self._dailytransactionCount[itemStr] = 0

        self._totalCoinLedger = {
            "deposit": 0,
            "withdraw": 0,
            "purchase": 0,
            "sale": 0,
            "repair": 0,
        }
        self._dailyCoinLedger = {
            "deposit": 0,
            "withdraw": 0,
            "purchase": 0,
            "sale": 0,
            "repair": 0,
        }

    def isVendor(self):
        if len(self.getCatalog()) > 0:
            return True
        return False

    def isRepairShop(self):
        return self._repair

    def isPawnShop(self):
        return self._pawnshop

    def isBank(self):
        return self._bank

    def getAttributesThatShouldntBeSaved(self):
        atts = []
        if hasattr(self, "attributesThatShouldntBeSaved"):
            atts += self.attributesThatShouldntBeSaved

        # Dont save empty inventories for rooms
        if self.getType() != "Room":
            return atts

        # everything below is for rooms only
        if hasattr(self, "_inventory"):
            if len(self.getInventory()) == 0:
                dLog(
                    "getAttributesThatShouldntBeSaved: adding _inventory "
                    + "to unsaved attributes",
                    self._instanceDebug,
                )
                atts.append("_inventory")
            else:
                dLog(
                    "getAttributesThatShouldntBeSaved: preserving room "
                    + "inventory (count="
                    + str(len(self.getInventory()))
                    + ")",
                    self._instanceDebug,
                )
        return atts

    def getCatalog(self):
        return self._catalog

    def getPriceBonus(self):
        return self._priceBonus

    def getCantAffordTxt(self, cost=0):
        return self._cantAffordTxt + "\n"

    def getCantCarryTxt(self, weight=0):
        return self._cantCarryTxt + "\n"

    def getSuccessTxt(self):
        return self._successfulTransactionTxt + "\n"

    def getAbortedTxt(self):
        return self._abortedTransactionTxt + "\n"

    def getTransactions(self):
        return (
            self._dailyTransactionCount,
            self._totalTransactionCount,
            self._dailyCoinLedger,
            self._totalCoinLedger,
        )

    def shopGetInfo(self):
        buf = ""
        shopTypeList = []
        if len(self.getCatalog()):
            shopTypeList.append("Shop")
        if self.isPawnShop():
            shopTypeList.append("PawnShop")
        if self.isRepairShop():
            shopTypeList.append("RepairShop")
        if self.isBank():
            shopTypeList.append("Bank")

        buf += (
            self.S_ROW_FORMAT.format("ShopType", ", ".join(shopTypeList))
            + self.S_ROW_FORMAT.format("priceBonus", str(self.getPriceBonus()))
            + self.S_ROW_FORMAT.format("LastTrans", dateStr(self._lastTransactionDate))
            + self.S_ROW_FORMAT.format("TotalTrans", str(self._totalTransactionCount))
            + self.S_ROW_FORMAT.format("DailyTrans", str(self._dailyTransactionCount))
        )

        buf += self.displayLedger()
        buf += self.displayTransactions()
        return buf

    def displayTransactions(self):
        buf = ""

        if len(self.getCatalog()):
            buf += "Catalog:\n"
            for itemStr in self._catalog:
                buf += "  " + self.S_ROW_FORMAT.format(
                    itemStr,
                    " sold today: "
                    + str(self._dailyTransactionCount.get(itemStr, 0))
                    + " - total sold: "
                    + str(self._totalTransactionCount.get(itemStr, 0)),
                )
        return buf

    def displayLedger(self):
        buf = ""
        if not self.isBank():
            return ""
        buf += "Bank Ledger:\n"
        for onekey in self._totalCoinLedger.keys():
            buf += "  " + self.S_ROW_FORMAT.format(
                onekey,
                "today: "
                + str(self._dailyCoinLedger.get(onekey, 0))
                + " - total: "
                + str(self._totalCoinLedger.get(onekey, 0)),
            )
        return buf

    def getTaxRate(self):
        taxrate = max(0, (100 - self.getPriceBonus()))
        return taxrate

    def getTaxAmount(self, amount):
        taxes = int(int(amount) * self.getTaxRate())
        return taxes

    def recordTransaction(self, item, saveRoomFlag=True):
        """ Everytime a buy/sell/repair is done, use this to update stats """
        if differentDay(datetime.now(), self._lastTransactionDate):
            self._dailyTransactionCount = {}  # reset daily counts
            self._dailyCoinLedger = {}

        if isinstance(item, str):
            """ This keeps track of totals funds """
            itemStr, itemAmount = item.split("/")  # i.e. deposit/345560

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
            """ This keeps track of item totals """
            itemStr = item.__class__.__name__ + "/" + str(item.getId())

            if itemStr in self._totalTransactionCount.keys():  # incr totals
                self._totalTransactionCount[itemStr] += 1
            else:
                self._totalTransactionCount[itemStr] = 1

            if itemStr in self._dailyTransactionCount.keys():  # incr daily
                self._totalTransactionCount[itemStr] += 1
            else:
                self._dailyTransactionCount[itemStr] = 1

        self._lastTransactionDate = datetime.now()  # store date of transaction

        if saveRoomFlag:
            self.save()  # save the room

    def adjustPrice(self, price):
        """ Adjust the price of goods depending on room attributes
            * non-room price changes occur elsewhere """
        price *= self._priceBonus / 100
        return int(price)

    def setDataFilename(self):
        """ sets the filename of the room """
        if isinstance(self.getRoomNum(), int):
            self._datafile = os.path.abspath(
                DATADIR
                + "/"
                + "Shop"
                + "/"
                + str(self.getRoomNum())
                + self._fileextension
            )

    # End of Shop class


class Guild(Shop):
    """ Room where players of the proper class can level up by training """

    wizardAttributes = Room.wizardAttributes + ["_order"]

    def __init__(self, roomNum=1):
        super().__init__(roomNum)
        self._order = "fighter"  # What class can train here - must match
        self._guildDues = 100

        # These are auto-generated
        self._lastTrainDate = getNeverDate()
        self._lastTrainees = []
        self._masterLevel = 1  # Highest level players in this guild
        self._masters = []  # Leaderboard of players at highest level

        self._successfulTransactionTxt = "Congratulations!"
        self._cantAffordTxt = "You can't afford the training fee!"
        self._notHereTxt = "You can't train here!"
        self._notEnoughExpTxt = "You don't have enough experience to train."

    def guildGetInfo(self):
        ROW_FORMAT = "{0:14}: {1:<30}\n"
        buf = ""
        buf += ROW_FORMAT.format("Order", self._order)
        return buf

    def getNotHereTxt(self):
        return self._notHereTxt + "\n"

    def getNotEnoughExpTxt(self):
        return self._notEnoughExpTxt + "\n"

    def getOrder(self):
        return self._order

    def getLastTrainees(self):
        return self._lastTrainees

    def getLastTrainDate(self):
        return self._lastTrainDate

    def getMasterLevel(self):
        return self._masterLevel

    def getMasters(self):
        return self._masters

    def isTrainingGround(self):
        return True

    def isTrainingGroundForChar(self, charObj):
        if not self.isTrainingGround():
            return False
        if charObj.getClassName() == self.getOrder():
            return True
        return False

    def getCostToTrain(self, level):
        """ amount required to train for next level """
        return 2 ** (7 + level)

    def payToTrain(self, charObj):
        costToTrain = self.getCostToTrain(charObj.getLevel())

        if charObj.canAffordAmount(costToTrain):
            charObj.subtractCoins(costToTrain)
            return True

        coinsMissing = costToTrain - charObj.getCoins()
        charObj.client.spoolOut(
            self.getCantAffordTxt()
            + "You need "
            + str(coinsMissing)
            + " more shillings."
        )
        return False

    def train(self, charObj):
        if not self.isTrainingGroundForChar(charObj):
            charObj.client.spoolOut(self.getNotHereTxt())

        if not charObj.hasExpToTrain():
            charObj.client.spoolOut(
                self.getNotEnoughExpTxt()
                + "You need "
                + str(charObj.getExp())
                + " more experience"
            )
            return False

        if not self.payToTrain(charObj):
            return False

        charObj.levelUp()
        newLevel = charObj.getLevel()
        charObj.client.spoolOut(
            self.getSuccessTxt() + "You are now level " + str(newLevel) + "."
        )
        logger.info(
            "room.train: "
            + charObj.getId()
            + "has trained to "
            + "become level "
            + str(newLevel)
            + "."
        )

        self.recordTrainStats(charObj)
        return True

    def calculateMasterCoinBonus(self, level):
        return int(1000 * (level ** 2))

    def recordTrainStats(self, charObj):
        charLevel = charObj.getLevel()
        self._lastTrainDate = datetime.now()
        self._lastTrainees.append(charObj.getId())
        if len(self._lastTrainees) > 5:
            self._lastTrainees.pop(0)
        if charLevel == self._masterLevel:
            self._masters.append(charObj.getId())
        if charLevel > self._masterLevel:
            self._masterLevel = charLevel
            self._masters = [charObj.getId()]
            coinBonus = self.calculateMasterCoinBonus(charLevel)
            charObj.addCoins(coinBonus)
            charObj.client.spoolOut(
                "As the first "
                + self._order
                + " to reach level "
                + str(charLevel)
                + ", the guild honors your new rank with a "
                + "bonus of "
                + str(coinBonus)
                + " shillings and adds your "
                + "name to a plaque on the wall.\n"
            )

    def getPlaqueMsg(self):
        msg = (
            "Our guild honors the following level "
            + str(self.getMasterLevel())
            + " masters:\n"
        )
        if len(self.getMasters()) == 0:
            msg += "  None\n"
        for name in self.getMasters()[:10]:  # Show the first 10 names
            msg += "  " + name + "\n"

        msg += "The following students have trained recently:\n"
        if len(self.getLastTrainees()) == 0:
            msg += "  None.\n"
        for name in self.getLastTrainees():
            msg += "  " + name + "\n"
        return msg

    def setDataFilename(self):
        """ sets the filename of the room """
        if isinstance(self.getRoomNum(), int):
            self._datafile = os.path.abspath(
                DATADIR
                + "/"
                + "Guild"
                + "/"
                + str(self.getRoomNum())
                + self._fileextension
            )

    def displayExtra(self, charObj):
        buf = self.getPlaqueMsg()
        return buf

    # End of Guild class


RoomFactoryTypes = ["room", "shop", "guild"]


def getRoomTypeFromFile(num, extension=".json"):
    returnType = "room"
    for roomType in RoomFactoryTypes:
        filename = os.path.abspath(
            DATADIR + "/" + roomType.capitalize() + "/" + str(num) + extension
        )
        if os.path.isfile(filename):
            returnType = roomType
            break
    return returnType


def isRoomFactoryType(item):
    """ Return True if item is a valid object FacotryType """
    if isinstance(item, str):
        name = item.lower()
    else:
        name = item.getType().lower()
    return name in RoomFactoryTypes


def RoomFactory(objType="room", id=0):
    """ Factory method to return the correct object, depending on the type """
    obj = None

    if objType.lower() == "room":
        obj = Room(id)
    elif objType.lower() == "shop":
        obj = Shop(id)
    elif objType.lower() == "guild":
        obj = Guild(id)

    if not obj.getId():
        logger.error(
            "RoomFactory: Could not obtain id for newly"
            + "instanciated "
            + objType
            + " object"
        )

    return obj
    # End of RoomFactory
