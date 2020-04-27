''' inventory class '''   # noqa

import inflect
import re
import textwrap


from common.general import getRandomItemFromList, dLog


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

    def describeInventory(self, showIndex=False, markerAfter=0, markerTxt=''):
        ''' Display inventory
            * showIndex - show the enumerated number in front of each item
            * markerAfter - add a separator after this many items
            * markerTxt - txt for the marker '''
        buf = "Inventory:\n"

        ROW_FORMAT = "  "
        if showIndex:
            ROW_FORMAT += "({0:2}) "
        ROW_FORMAT += "{1:<60}\n"

        itemlist = ''
        for num, oneObj in enumerate(self._inventory):
            dmInfo = '(' + str(oneObj.getId()) + ')'
            itemlist += (ROW_FORMAT.format(num, oneObj.describe() +
                         self.dmTxt(dmInfo)))
            if markerAfter and num == (markerAfter - 1):
                if markerTxt == '':
                    markerTxt = 'items below will be truncated on exit'
                itemlist += "--- " + markerTxt + " ---\n"

        if itemlist:
            buf += itemlist
        else:
            buf += "  Nothing\n"
        return(buf)

    def getDmMarkers(self, obj):
        buf = '(' + str(obj.getId()) + ')'
        if obj.isInvisible():
            buf += "[INV]"
        if obj.isHidden():
            buf += "[HID]"
        return(buf)

    def describeInvAsList(self, showDm, showHidden, showInvisible):
        ''' show inventory items as compact list
            typically used by room object, as player sees it '''
        buf = ''

        dLog("describeInvAsList: showDm=" + str(showDm) +
             " showHidden=" + str(showHidden) + " showInvisible=" +
             str(showInvisible), Inventory._instanceDebug)

        # create a list of items in inventory and a dict of related DM info
        dmDict = {}
        itemList = []
        for oneitem in self.getInventory():
            itemStr = ''
            if (((oneitem.isInvisible() and not showInvisible)
                 or (oneitem.isHidden() and not showHidden) and
                 not showDm)):
                dLog("describeInvAsList HID/INV: " + str(oneitem),
                     Inventory._instanceDebug)
                pass
            else:
                itemStr += oneitem.getSingular()
                itemList.append(itemStr)
                dmInfo = self.getDmMarkers(oneitem)
                try:
                    if re.match(dmInfo, dmDict[itemStr]):
                        dmDict[itemStr] += dmInfo
                except KeyError:
                    dmDict[itemStr] = dmInfo

        # instanciate inflect to help with grammar and punctuation
        inf = inflect.engine()

        # create a list of unique items
        uniqueItemNames = set(itemList)

        # create a list of items with their counts
        countedList = []
        for name in uniqueItemNames:
            itemStr = ''
            itemCnt = itemList.count(name)
            if itemCnt == 1:
                # we just want the article, but inf.a returns the noun
                words = inf.a(name).split(' ', 1)
                itemStr += words[0]
            else:
                itemStr += inf.number_to_words(inf.num(itemCnt))
            itemStr += ' ' + inf.plural_noun(name, itemCnt)
            if showDm:
                itemStr += dmDict[name]
            countedList.append(itemStr)

        # join our list with commas and 'and'
        sightList = inf.join(countedList)

        # intelligently wrap the resulting string
        if sightList != '':
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
