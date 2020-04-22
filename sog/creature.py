''' creature Class '''     # noqa

from datetime import datetime
import logging
# import os
import pprint
import random

from common.storage import Storage
from common.attributes import AttributeHelper
from common.editwizard import EditWizard
from common.general import getNeverDate, getRandomItemFromList, secsSinceDate
from common.inventory import Inventory
# from common.paths import DATADIR
from object import ObjectFactory


'''

4.5.1 Basic

    4.5.3 Secondary
        SP= : Spell casting, true/false, default false. Can cast these
            spells: poison, fireball, lightning, or befuddle.
        UN= : Undead, true/false, default false. Vulnerable to TURN command
            (clerics can use this).
        RU= : Rust, true/false, default false. Weakens player armor or primary
            weapon (deducts strikes or hits)


'''


class Creature(Storage, AttributeHelper, Inventory, EditWizard):

    _instanceDebug = False

    creatureSpellList = ['poison', 'fireball', 'lightning', 'befuddle']

    # obsolete attributes (to be removed)
    obsoleteAttributes = ['_parleyNone', '_spellCaster', '_parleyNone',
                          '_parleyPositive', '_parleyNegative',
                          '_parleyCustom', '_parleyTeleport' '_parleySell',
                          '_spellCaster', '_objDropList', '_numOfItemsDropped',
                          '_parleySellItems']

    attributesThatShouldntBeSaved = ['_creationDate', '_currentlyAttacking',
                                     '_enterRoomTime', '_instanceDebug',
                                     '_invWeight', '_invValue',
                                     '_attackPlayer']

    _levelDefaultsDict = {
        1: {
            '_exp': 10,
            '_ac': 0,
            '_maxhp': 30,
            '_damage': 5,
            '_tohit': 0
        },
        2: {
            '_exp': 20,
            '_ac': 0,
            '_maxhp': 50,
            '_damage': 5,
            '_tohit': 0
        },
        3: {
            '_exp': 30,
            '_ac': 1,
            '_maxhp': 70,
            '_damage': 5,
            '_tohit': 1
        },
        4: {
            '_exp': 40,
            '_ac': 1,
            '_maxhp': 100,
            '_damage': 5,
            '_tohit': 1
        },
        5: {
            '_exp': 50,
            '_ac': 2,
            '_maxhp': 150,
            '_damage': 5,
            '_tohit': 1
        },
        6: {
            '_exp': 90,
            '_ac': 2,
            '_maxhp': 200,
            '_damage': 5,
            '_tohit': 1
        },
        7: {
            '_exp': 200,
            '_ac': 3,
            '_maxhp': 500,
            '_damage': 5,
            '_tohit': 1
        },
        8: {
            '_exp': 300,
            '_ac': 3,
            '_maxhp': 700,
            '_damage': 5,
            '_tohit': 2
        },
        9: {
            '_exp': 1000,
            '_ac': 4,
            '_maxhp': 1000,
            '_damage': 5,
            '_tohit': 2
        },
        10: {
            '_exp': 3000,
            '_ac': 5,
            '_maxhp': 3000,
            '_damage': 5,
            '_tohit': 3
        },
        11: {
            '_exp': 4000,
            '_ac': 6,
            '_maxhp': 4000,
            '_damage': 5,
            '_tohit': 4
        },
        12: {
            '_exp': 5000,
            '_ac': 7,
            '_maxhp': 5000,
            '_damage': 5,
            '_tohit': 5
        },
        99: {
            '_exp': 8000,
            '_ac': 8,
            '_maxhp': 10000,
            '_damage': 5,
            '_tohit': 6
        }
    }

    _parleyDefaultsDict = {
        'None': ['does not respond', 'says nothing', 'has no reaction'],
        'Positive': ["Hello there, friend.", "Well, hello!"],
        'Negative': ["Buzz off, scumbag!", 'Leave me alone.'],
        'Custom': ["Have you heard about the burried treasure?"],
        'Teleport': ["recites some exotic words and you are whisked away.",
                     "whispers something incomprehendible before you vanish " +
                     "into thin air"],
        'Sell': ["Hey buddy.  Check this out"]
        }

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc",
                        "_longdesc", "_level", "_maxhp", "_hostile",
                        "_parleyAction"]

    attributeInfo = {
        "_name": "the single work noun you use when interacting with this",
        "_article": "the article of speech.  For example: a, an, some",
        "_singledesc": "the description for one of these",
        "_pluraldesc": "the description for two or more of these",
        "_longdesc": "the detailed description that is shown when you examine",
        "_level": "the level of the creature",
        "_maxhp": "the health of the creature",
        "_regenerate": "if True, monster regenerates hitpoints",
        "_damage": "additional damage that a creature inflicts on hit",
        "_tohit": "additional chance to hit target",
        "_hostile": "whether the creature attacks on sight or not",
        "_parleyAction": ("What the creature does when it's talked to.\n" +
                          "  Active values: Sell, Teleport, Attack\n" +
                          "  Canned Responses: None, Positive, Negative"),
        "_itemCatalog": "Which items the creature can be carrying",
        "_numOfItemsCarried": "Possible number of objects carried",
        "_frequency": "How often its encountered.  Range 1 (rare) to 100",
        "_frequency": "How often its encountered.  Range 1 (rare) to 100",
        "_TimeToFirstAttack": "# of seconds to wait before hostile atk",
        "_attackSpeed": "how fast a monter attacks  100=normal"}

    def __init__(self, id=0):
        super().__init__()
        self._creatureId = id
        self._name = ''

        self._article = ''
        self._pluraldesc = ''
        self._singledesc = ''
        self._longdesc = ''
        self._weight = 20           # unloaded creature weight
        self._value = 0             # unloaded creature value

        self._level = 1             # range 1..64
        self._exp = 0               # auto-generated after load
        self._ac = 0                # inital value auto-filled based on lvl
        self._damage = 0            # inital value auto-filled based on lvl
        self._tohit = 0             # inital value auto-filled based on lvl

        self._maxhp = 100           # Starting hit points - range 0..1023
        self._hp = self._maxhp      # Current hit points - autoset if 0
        self._regenerate = False    # Regenerates hit points during attack

        self._frequency = 50        # 0-100 with 100 being the most often
        self._TimeToFirstAttack = 10   # of seconds to wait before hostile atk
        self._attackSpeed = 100     # how fast a monter attacks  100=normal

        self._hostile = False        # attack player on sight
        self._defend = True          # attack back if attacked?
        self._follow = False         # chance to follow if player leaves room
        self._blockFromLeaving = False  # 50% stop atking player frm lving room
        self._guardTreasure = False  # can't pick up treasure w/ creat in room
        self._sendToJail = False     # if attacked player loses weapon & jailed
        self._noKill = False         # players can't attack if set
        self._kidnap = False         # Capture Instead of death
        self._hidden = False         # Can't see monster until engaged
        self._invisible = False      # Can’t see + “to hit” has 20% penalty
        self._drain = False          # Chance to drain level (50% of the time)
        self._poison = False         # On hit may poison player
        self._undead = False         # can be turned by clerics and paladins
        self._rust = False           # causes armor to rust and lose extra hits
        self._steal = False          # chance to steal from player
        self._carry = False          # creature is carryable (ultra-rare)
        self._antiMagic = False      # immune to spells
        self._magicImmunity = False  # immune to attacks from non-magic weapons
        self._fleeIfAttacked = False     # chance to run away when attacked
        self._attackLastAttacker = True  # If false attack first attacker
        self._attackIfPietyLessThan = 3  # 0=ignore
        self._attackIfPietyMoreThan = 0  # 0=ignore
        self._assistCreature = []        # Which creatures it calls for help
        self._defendCreature = []        # Which creatures it will defend
        self._offensiveSpells = []       # Which spells it can cast
        self._itemCatalog = []      # list of item nums that creature may drop
        self._numOfItemsCarried = [0, 1, 2]  # number of items dropped - random

        self._creationDate = datetime.now()   # ag - when creatObj was created
        self._enterRoomTime = getNeverDate()  # ag - when creture entered room
        self._currentlyAttacking = None       # ag - Who creature is attacking

        self._permanent = False      # stays in room when room is not active
        self._unique = False         # only one allowed in room at a time
        self._watch = False          # notify dm if attacked

        self._parleyAction = 'None'    # Which of the parley actions to take
        self._parleyTxt = self._parleyDefaultsDict['None']
        self._parleyTeleportRooms = []  # room to transport to.  empty=1-300

        self._alignment = 'neutral'  # Values: neutral, good, evil

        self._instanceDebug = Creature._instanceDebug

        logging.debug("Creature __init__" + str(self._creatureId))

        if self._instanceDebug:
            logging.debug("Creature init called for " + str(self.getId()))
        return(None)

    def __del__(self):
        if self._instanceDebug:
            logging.debug("Creature destructor called for " +
                          str(self.getId()))

    def debug(self):
        return(pprint.pformat(vars(self)))

    def toggleInstanceDebug(self):
        self._instanceDebug = not self._instanceDebug

    def describe(self, count=1):
        if count > 1:
            return(count + " " + self._pluraldesc)
        return(self._article + " " + self._singledesc)

    def examine(self):
        return(self._longdesc)

    def delete(self):
        return(None)

    def getId(self):
        return(self._creatureId)

    def getType(self):
        return(self.__class__.__name__)

    def getArticle(self):
        return(self._article)

    def getSingular(self):
        return(self._singledesc)

    def getPlural(self):
        return(self._pluraldesc)

    def getLevel(self):
        return(self._level)

    def getExp(self):
        return(self._exp)

    def getHitPoints(self):
        return(self._hp)

    def setHitPoints(self, num=0):
        if num:
            self._hp = int(num)
        else:
            self._hp = self.getMaxHitPoints()

    def takeDamage(self, num=0):
        self._hp -= num

    def diesFromDamage(self, num=0):
        if num > self.getHitPoints():
            return(True)
        return(False)

    def setEnterRoomTime(self):
        self._enterRoomTime = datetime.now()

    def getMaxHitPoints(self):
        return(self._maxhp)

    def getName(self):
        return(self._name)

    def getFrequency(self):
        return(self._frequency)

    def getAlignment(self):
        return(self._alignment)

    def fleesIfAttacked(self):
        return(self._fleeIfAttacked)

    def isInvisible(self):
        return(self._invisible)

    def isHidden(self):
        return(self._hidden)

    def isHostile(self):
        return(self._hostile)

    def isCarryable(self):
        return(self._carry)

    def isPermanent(self):
        return(self._permanent)

    def isUsable(self):
        return(False)

    def isMagic(self):
        return(self._magicImmunity)

    def isAntiMagic(self):
        return(self._antiMagic)

    def isUndead(self):
        return(self._undead)

    def getWeight(self):
        return(self._weight)

    def getValue(self):
        return(self._value)

    def isAttacking(self):
        if self._currentlyAttacking is not None:
            return(True)
        return(False)

    def getCurrentlyAttacking(self):
        if self.isAttacking():
            return(self._currentlyAttacking)
        return(None)

    def setCurrentlyAttacking(self, player):
        self._currentlyAttacking = player

    def initiateAttack(self, charObj=None):
        ''' Returns true if creature initiates attack on player '''
        if not charObj:
            charObj = self.getCurrentlyAttacking()

        if not charObj:
            return(False)

        if not self.notices(charObj):
            return(False)

        if charObj != self.getCurrentlyAttacking():
            self.setCurrentlyAttacking(charObj)        # initiate attack
            return(True)

        return(False)

    def attack(self, charObj=None):
        if not charObj:
            charObj = self.getCurrentlyAttacking()

        if not charObj:
            return(False)

        if charObj != self.getCurrentlyAttacking():
            self.setCurrentlyAttacking(charObj)        # initiate attack

        # determine if creature actually attacks
        # self._attackSpeed

        if not self.hitsCharacter(charObj):  # determine if creature hits
            charObj.svrObj.spoolOut(self.describe() + " misses you!")
            # notify other players in the room

        # calculate attack damage
        damage = 0

        # notify
        if damage:
            charObj.svrObj.spoolOut(self.describe() + " hits you for " +
                                    damage + " damage.")
            charObj.takeDamage(damage)
        return(None)

    def hitsCharacter(self, charObj):
        ''' return true if creature hits the character '''
        # todo: figure out formula
        return(True)

    def autoPopulateInventory(self):
        ''' create creature inventory
           * randomly pick the number of items from the numOfItemsDropped list
           * for each of those, randomly pick an objNum from the itemCatalog
           * for each of those, load the object and add it to the inventory
           * typically run at creature load time
        '''
        if not self._permanent:
            self.clearInventory()

        # Randomly select the itemCount
        itemCount = getRandomItemFromList(self._numOfItemsCarried)

        if not itemCount:   # 0 items carried
            return(True)

        for itemNum in range(1, itemCount + 1):  # +1 due to exclusive ranges
            itemId = getRandomItemFromList(self._itemCatalog)
            if not itemId:
                continue
            if "/" not in itemId:
                continue

            logging.debug("api: obj = " + itemId)
            oType, oNum = itemId.split('/')
            obj1 = ObjectFactory(oType, oNum)
            obj1.load()
            self.addToInventory(obj1)
        return(True)

    def postLoad(self):
        self.setExp()            # calculate exp and set it
        if not self.getHitPoints():
            self.setHitPoints()  # set hp to the maxHP for this creature
        self.autoPopulateInventory()

    def getAttributeCount(self, which='primary'):
        ''' Returns the number of attributes set to True.
            Distinguishes between primary and secondary attribute types '''
        count = 0
        primaryAtts = ['_blockFromLeaving', '_follow', '_guardTreasure',
                       '_hostile', '_attackLastAttacker', '_fleeIfAttacked',
                       '_undead', '_rust', '_steal']
        secondaryAtts = ['_magicImmunity', '_antiMagic',
                         '_hidden', '_regenerate', '_steal', '_drain',
                         '_poison', '_kidnap', '_invisible', '_sendToJail']
        if which == 'primary':
            mylist = primaryAtts
        else:
            mylist = secondaryAtts
            if len(self._offensiveSpells) > 0:
                count += 1

        for att in mylist:
            if getattr(self, att):
                count += 1

        return(count)

    def setExp(self):
        ''' Set the exp of a creature depending on it's stats
            EXP = HP + Table(level) + monsterLevelBonus

            Todo: When there are multiple attackers, this exp should be
            split amoung them and the player with the kill receives a bonus.
        '''
        exp = 0

        level = min(1, self.getLevel())
        exp += self.getMaxHitPoints() + self._levelDefaultsDict[level]['_exp']

        # Monster level	Bonus
        monsterLevelBonus = (((self.getAttributeCount('primary') + 2) *
                             self.getAttributeCount('secondary')) *
                             (self.getMaxHitPoints() / 10))

        if self.getLevel() in range(6, 8 + 1):
            monsterLevelBonus *= 2
        elif self.getLevel() > 8:
            monsterLevelBonus *= 6

        self._exp = int(exp + monsterLevelBonus)
        return(None)

    def getHitPointPercent(self):
        ''' returns the int percentage of health remaining '''
        percent = self.getHitPoints() * 100 / self.getMaxHitPoints()
        return(int(percent))

    def flees(self, percentChanceOfFleeing=20):
        if not self.fleesIfAttacked():
            return(False)

        if (self.getHitPointPercent() < 40):
            if random.randint(1, 100) <= percentChanceOfFleeing:
                return(True)

        return(False)

    def getParleyAction(self):
        return(self._parleyAction)

    def getParleyTeleportRoomNum(self):
        if len(self._parleyTeleportRooms) == 0:
            return(random.randint(1, 300))
        return(getRandomItemFromList(self._parleyTeleportRooms))

    def getParleySaleItem(self):
        return(self.getRandomInventoryItem())

    def getParleyTxt(self):
        buf = ''

        if self._parleyAction.lower() == 'none':
            buf += "The " + self._name + " " + self._parleyNone
        else:
            buf += ("The " + self._name + " says, " +
                    getRandomItemFromList(self._parleyTxt))
        return(buf)

    def notices(self, charObj):
        ''' returns true if the creature notices the character '''
        if charObj.isHidden() or charObj.isInvisible():
            return(False)

        # todo: add rand/luck?

        if self._enterRoomTime == getNeverDate():
            self.setEnterRoomTime()
            return(False)

        if secsSinceDate(self._enterRoomTime) > self._TimeToFirstAttack:
            return(True)
        else:
            return(False)

        return(True)

    def fixAttributes(self):
        ''' Sometimes we change attributes, and need to fix them in rooms
            that are saved.  This method lets us do that.  Typically this
            involves casting types or removing obsolete vars, but we could
            also use this for copying values from one attribute to another '''

        try:
            self._objDropList = self.itemCatalog
        except (AttributeError, TypeError):
            pass
        try:
            self._numOfItemsDropped = self._numOfItemsCarried
        except (AttributeError, TypeError):
            pass
        try:
            self._parleyTeleportRooms = []
        except (AttributeError, TypeError):
            pass

        AttributeHelper.fixAttributes(self)
