''' test_inventory '''   # noqa

# import loggerging
import unittest

from common.inventory import Inventory
from common.general import logger
from common.test import TestGameBase
import creature
import object


class TestPlayerInventory1(TestGameBase, Inventory):

    testInventory = ['Armor/1', 'Armor/1', 'Weapon/1', 'Treasure/1']

    def setUp(self):
        self.banner('start', testName=__class__.__name__)
        Inventory.__init__(self)

    def populateInventory(self, iList):
        for itemName in iList:
            iType, iNum = itemName.split('/')
            if object.isObjectFactoryType(iType.lower()):  # Objects
                logger.debug("In " + __class__.__name__ + ": creating obj " +
                             str(iType) + ":" + str(iNum))
                item = object.ObjectFactory(iType, iNum)
                item.load()
                self.addToInventory(item)
            elif iType == 'Creature':                    # Creatures
                item = creature.Creature(iNum)
                logger.debug("In " + __class__.__name__ + ": creating cre " +
                             str(iType) + ":" + str(iNum))
                item.load()
                self.addToInventory(item)
            else:
                logger.debug("In " + __class__.__name__ + ": unknown " +
                             str(iType) + " in " +
                             str(object.ObjFactoryTypes))
                print("Unknown Item type")
        return(None)

    def testPlayerInventoryCount(self):
        self.populateInventory(self.testInventory)
        logger.debug("In " + __class__.__name__ + ": inv = " +
                     str(self.getInventory()))
        inventoryCount = len(self.getInventory())
        self.assertEqual(inventoryCount != 0, True, "Empty Inventory")
        out = ("Inventory: " + str(self.getInventory) +
               " - InventoryCount: " + str(inventoryCount))
        status = bool(len(self.testInventory) == inventoryCount)
        self.assertEqual(status, True, out)

    def testPlayerInventoryRandomItem(self):
        self.populateInventory(self.testInventory)
        randomItem = self.getRandomInventoryItem()
        out = ("Inventory: " + str(self.testInventory) +
               " - RandomItemId: " + str(randomItem.getId()))
        status = bool(randomItem.getId() == 1)
        self.assertEqual(status, True, out)


class TestRoomInventory1(TestGameBase, Inventory):

    testInventory = ['Creature/1', 'Portal/1', 'Treasure/1']

    def setUp(self):
        self.banner('start', testName=__class__.__name__)
        Inventory.__init__(self)

    def populateInventory(self, iList):
        for itemName in iList:
            iType, iNum = itemName.split('/')
            if object.isObjectFactoryType(iType.lower()):  # Objects
                logger.debug("In " + __class__.__name__ + ": creating obj " +
                             str(iType) + ":" + str(iNum))
                item = object.ObjectFactory(iType, iNum)
                item.load()
                self.addToInventory(item)
            elif iType == 'Creature':                    # Creatures
                item = creature.Creature(iNum)
                logger.debug("In " + __class__.__name__ + ": creating cre " +
                             str(iType) + ":" + str(iNum))
                item.load()
                self.addToInventory(item)
            else:
                logger.debug("In " + __class__.__name__ + ": unknown " +
                             str(iType) + " in " +
                             str(object.ObjFactoryTypes))
                print("Unknown Item type")
        return(None)

    def testInventoryCount(self):
        self.populateInventory(self.testInventory)
        inventoryCount = len(self.getInventory())
        self.assertEqual(inventoryCount != 0, True, "Empty Inventory")
        out = ("Inventory: " + str(self.getInventory()) +
               " - InventoryCount: " + str(inventoryCount))
        status = bool(len(self.testInventory) == inventoryCount)
        self.assertEqual(status, True, out)


if __name__ == '__main__':
    unittest.main()
