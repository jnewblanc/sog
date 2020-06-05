''' Item superClass, from which character, creatures, rooms, and object are
    derived.
'''

import glob
import os
import re

from common.attributes import AttributeHelper
from common.editwizard import EditWizard
from common.globals import DATADIR
from common.inventory import Inventory
from common.storage import Storage


class Item(Storage, AttributeHelper, Inventory, EditWizard):
    ''' Item SuperClass - A bunch of common methods that are meant to
        be overridden if needed '''

    def canBeEntered(self, charObj=None):
        return(False)

    def canBeRepaired(self):
        return(False)

    def dmTxt(self, msg):
        ''' inventory wants this to be defined. '''
        return('')

    def getId(self):
        return(0)

    def getValue(self):
        return(0)

    def getWeight(self):
        return(0)

    def getAttributesThatShouldntBeSaved(self):
        atts = []
        if hasattr(self, 'attributesThatShouldntBeSaved'):
            atts += self.attributesThatShouldntBeSaved
        return(atts)

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

    def hasToll(self):
        return(False)

    def payToll(self, charObj):
        return(True)

    def isVulnerable(self):
        return(False)

    def getItemId(self):
        return(self.getType() + "/" + str(self.getId()))

    def getNextUnusedFileNumber(self, type):
        ''' return the next unused item number, by looking through the
            corresponding files for the last one used.  This is typically
            used when creating new objects or creatures '''
        # It's a little sucky to have to list these here, but we have no access
        # to the object, where _fileextension is defined.
        returnNum = 0
        dir = DATADIR
        if type != '':
            dir += '/' + type.capitalize()

        if hasattr(self, '_fileextension'):
            extension = self._fileextension
        else:
            extension = '.pickle'

        numberlist = []
        if os.path.exists(dir):
            filelist = glob.glob(dir + '/*' + extension)
            for fqfn in filelist:
                filenumber = re.sub('[^0-9]', '', os.path.basename(fqfn))
                if filenumber != '':
                    numberlist.append(int(filenumber))
        if len(numberlist) > 0:
            sortedlist = sorted(numberlist)
            returnNum = sortedlist[-1] + 1
        return(returnNum)

    def persistsThroughOneRoomLoad(self):
        return(False)
