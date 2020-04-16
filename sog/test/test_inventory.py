''' inventory unit tests '''   # noqa

import logging
import unittest

import object
import creature
from common.inventory import Inventory
from common.inittestlog import InitTestLog


class TestPlayerInventory1(unittest.TestCase, Inventory, InitTestLog):

    testInventory = ['Armor/1', 'Armor/1', 'Weapon/1', 'Treasure/1']

    def populateInventory(self, iList):
        for itemName in iList:
            iType, iNum = itemName.split('/')
            if iType.lower() in object.getObjectFactoryTypes():  # Objects
                logging.debug("In " + __class__.__name__ + ": creating obj " +
                              str(iType) + ":" + str(iNum))
                item = object.ObjectFactory(iType, iNum)
                item.load()
                self.addToInventory(item)
            elif iType == 'Creature':                    # Creatures
                item = creature.Creature(iNum)
                logging.debug("In " + __class__.__name__ + ": creating cre " +
                              str(iType) + ":" + str(iNum))
                item.load()
                self.addToInventory(item)
            else:
                logging.debug("In " + __class__.__name__ + ": unknown " +
                              str(iType) + " in " +
                              str(object.getObjectFactoryTypes()))
                print("Unknown Item type")
        return(None)

    def testPlayerInventoryCount(self):
        InitTestLog.__init__(self)
        Inventory.__init__(self)

        self.populateInventory(self.testInventory)
        logging.debug("In " + __class__.__name__ + ": inv = " +
                      str(self.getInventory()))
        inventoryCount = len(self.getInventory())
        self.assertEqual(inventoryCount != 0, True, "Empty Inventory")
        out = ("Inventory: " + str(self.getInventory) +
               " - InventoryCount: " + str(inventoryCount))
        status = bool(len(self.testInventory) == inventoryCount)
        self.assertEqual(status, True, out)

    def testPlayerInventoryRandomItem(self):
        InitTestLog.__init__(self)
        Inventory.__init__(self)

        self.populateInventory(self.testInventory)
        randomItem = self.getRandomInventoryItem()
        out = ("Inventory: " + str(self.testInventory) +
               " - RandomItemId: " + str(randomItem.getId()))
        status = bool(randomItem.getId() == 1)
        self.assertEqual(status, True, out)


class TestRoomInventory1(unittest.TestCase, Inventory):

    testInventory = ['Creature/1', 'Portal/1', 'Treasure/1']

    def populateInventory(self, iList):
        for itemName in iList:
            iType, iNum = itemName.split('/')
            if iType.lower() in object.getObjectFactoryTypes():  # Objects
                logging.debug("In " + __class__.__name__ + ": creating obj " +
                              str(iType) + ":" + str(iNum))
                item = object.ObjectFactory(iType, iNum)
                item.load()
                self.addToInventory(item)
            elif iType == 'Creature':                    # Creatures
                item = creature.Creature(iNum)
                logging.debug("In " + __class__.__name__ + ": creating cre " +
                              str(iType) + ":" + str(iNum))
                item.load()
                self.addToInventory(item)
            else:
                logging.debug("In " + __class__.__name__ + ": unknown " +
                              str(iType) + " in " +
                              str(object.getObjectFactoryTypes()))
                print("Unknown Item type")
        return(None)

    def testInventoryCount(self):
        InitTestLog.__init__(self)
        Inventory.__init__(self)

        self.populateInventory(self.testInventory)
        inventoryCount = len(self.getInventory())
        self.assertEqual(inventoryCount != 0, True, "Empty Inventory")
        out = ("Inventory: " + str(self.getInventory()) +
               " - InventoryCount: " + str(inventoryCount))
        status = bool(len(self.testInventory) == inventoryCount)
        self.assertEqual(status, True, out)


if __name__ == '__main__':
    unittest.main()
