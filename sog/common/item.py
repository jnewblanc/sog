''' Item superClass, from which character, creatures, rooms, and object are
    derived.
'''
from common.storage import Storage
from common.attributes import AttributeHelper
from common.editwizard import EditWizard
from common.inventory import Inventory


class Item(Storage, AttributeHelper, Inventory, EditWizard):
    ''' Item SuperClass - A bunch of common methods that are meant to
        be overridden if needed '''

    def canBeEntered(self, charObj=None):
        return(False)

    def canBeRepaired(self):
        return(False)

    def getId(self):
        return(0)

    def getValue(self):
        return(0)

    def getWeight(self):
        return(0)

    def isBlessed(self):
        return(False)

    def isBroken(self):
        return(False)

    def isCarryable(self):
        return(False)

    def isClosable(self, obj=None):
        return(False)

    def isCursed(self):
        return(False)

    def isDepleated(self):
        return(False)

    def isEquippable(self):
        return(False)

    def isEvil(self):
        return(False)

    def isGood(self):
        return(False)

    def isHidden(self):
        return(False)

    def isInvisible(self):
        return(False)

    def isLockable(self):
        return(False)

    def isMagic(self):
        return(False)

    def isMagicItem(self):
        return(False)

    def isOpenable(self, obj=None):
        return(False)

    def isPermanent(self):
        return(False)

    def isPickable(self, obj=None):
        return(False)

    def isSmashable(self, obj=None):
        return(False)

    def isUnlockable(self):
        return(False)

    def isUsable(self):
        return(False)

    def isValid(self):
        return(False)

    def isVulnerable(self):
        return(False)
