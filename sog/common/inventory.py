''' inventory class '''   # noqa

import textwrap


from common.general import rreplace, getRandomItemFromList, dLog


class Inventory():
    ''' A generic inventory SuperClass
        * used by characters, creatures, and rooms
        * a char/creature inventory contains objects
        * a room inventory may contain objects and/or creatures'''

    _instanceDebug = False

    def __init__(self, id=0):
        # id is unused in this case, but super often passes id anyway
        self._inventory = []
        self._invWeight = 0
        self._maxweight = 0
        self._invValue = 0
        self._inventoryTruncSize = 12
        self._instanceDebug = Inventory._instanceDebug

        return(None)

    def getInventory(self):
        dLog("inv getInventory: " + str(self._inventory),
             Inventory._instanceDebug)
        return(self._inventory)

    def getInventoryByType(self, type):
        matchList = []
        for item in self._inventory:
            if item.getType() == type:
                matchList.append(item)
        return(matchList)

    def getInventoryWeight(self):
        self._setInventoryWeight()
        return(self._invWeight)

    def getInventoryValue(self):
        self._setInventoryValue()
        return(self._invValue)

    def setInventoryMaxWeight(self, num=0):
        self._maxweight = int(num)

    def getInventoryMaxWeight(self):
        return(self._maxweight)

    def setInventoryTruncSize(self, num=12):
        self._inventoryTruncSize = int(num)

    def getInventoryTruncSize(self):
        return(self._inventoryTruncSize)

    def addToInventory(self, item, maxSize=99999):
        if len(self.getInventory()) >= maxSize:
            return(False)
        self._inventory.append(item)
        self._setInventoryWeight()
        self._setInventoryValue()
        return(True)

    def removeFromInventory(self, item):
        if item in self._inventory:
            self._inventory.remove(item)
            self._setInventoryWeight()
            self._setInventoryValue()
        return(True)

    def describeInventory(self):
        ''' Display inventory '''
        buf = "Inventory:\n"
        ROW_FORMAT = "  ({0:2}) {1:<60}\n"
        itemlist = ''
        for num, oneObj in enumerate(self._inventory):
            dmInfo = '(' + str(oneObj.getId()) + ')'
            itemlist += (ROW_FORMAT.format(num, oneObj.describe() +
                         self.dmTxt(dmInfo)))

        if itemlist:
            buf += itemlist
        else:
            buf += "  Nothing\n"
        return(buf)

    def describeInvAsList(self, showDm, showHidden, showInvisible):
        ''' show inventory items as compact list
            typically used by room object, as player sees it '''
        buf = ''
        sightList = ''

        # show creatures and objects in inventory
        for oneitem in self.getInventory():
            dmInfo = '(' + str(oneitem.getId()) + ')'
            if oneitem.isInvisible():
                dmInfo += "[INV]"
            if oneitem.isHidden():
                dmInfo += "[HID]"
            if (((oneitem.isInvisible() and not showInvisible)
                 or (oneitem.isHidden() and not showHidden))):
                pass
            else:
                sightList += oneitem.describe()
                if showDm:
                    sightList += dmInfo
                sightList += ", "
        # toDo: compact lists by grouping duplicates as plurals

        if sightList != '':
            # Pretty up the list of objects/creatures to make it more readable
            sightList = sightList.rstrip(', ')
            if sightList.count(', ') > 2:
                andTxt = ', and '
            else:
                andTxt = ' and '
            sightList = rreplace(sightList, ', ', andTxt)
            buf = textwrap.fill(sightList, width=80) + '\n'

        dLog("inv descAsList: " + buf, Inventory._instanceDebug)

        return(buf)

    def clearInventory(self):
        ''' remove everything from inventory '''
        self._inventory = []

    def truncateInventory(self, num):
        ''' remove everything from inventory that exceeds <num> items '''
        if not num:
            num = self._inventoryTruncSize
        del self._inventory[num:]

    def _setInventoryWeight(self):
        ''' Calculate the weight of inventory '''
        self._invWeight = 0
        for oneObj in list(self._inventory):
            self._invWeight += oneObj.getWeight()

    def _setInventoryValue(self):
        ''' Calculate the value of inventory '''
        self._invValue = 0
        for oneObj in list(self._inventory):
            self._invValue += oneObj.getValue()

    def inventoryWeightAvailable(self):
        weight = self.getInventoryMaxWeight() - self.getInventoryWeight()
        return(int(weight))

    def canCarryAdditionalWeight(self, num):
        if self.inventoryWeightAvailable() >= int(num):
            return(True)
        return(False)

    def getRandomInventoryItem(self):
        if not self.getInventory():
            return(None)
        return(getRandomItemFromList(self.getInventory()))

    def autoPopulateInventory(self):
        ''' should be overridden if needed '''
