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

    attributesThatShouldntBeSaved = ['_creationDate', '_attackPlayer',
                                     '_enterRoomTime']

    _levelDefaultsDict = {
        1: {
            '_exp': 10,
            '_ac': 1,
            '_maxhp': 30
        },
        2: {
            '_exp': 20,
            '_ac': 1,
            '_maxhp': 50
        },
        3: {
            '_exp': 30,
            '_ac': 1,
            '_maxhp': 70
        },
        4: {
            '_exp': 40,
            '_ac': 1,
            '_maxhp': 100
        },
        5: {
            '_exp': 50,
            '_ac': 1,
            '_maxhp': 150
        },
        6: {
            '_exp': 90,
            '_ac': 1,
            '_maxhp': 200
        },
        7: {
            '_exp': 200,
            '_ac': 1,
            '_maxhp': 500
        },
        8: {
            '_exp': 300,
            '_ac': 1,
            '_maxhp': 700
        },
        9: {
            '_exp': 1000,
            '_ac': 1,
            '_maxhp': 1000
        },
        10: {
            '_exp': 3000,
            '_ac': 1,
            '_maxhp': 3000
        },
        11: {
            '_exp': 4000,
            '_ac': 1,
            '_maxhp': 4000
        },
        12: {
            '_exp': 5000,
            '_ac': 1,
            '_maxhp': 5000
        },
        99: {
            '_exp': 8000,
            '_ac': 10,
            '_maxhp': 10000
        }
    }

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc",
                        "_longdesc", "_level", "_maxhp", "_hostile"]

    attributeInfo = {
        "_name": "the single work noun you use when interacting with this",
        "_article": "the article of speech.  For example: a, an, some",
        "_singledesc": "the description for one of these",
        "_pluraldesc": "the description for two or more of these",
        "_longdesc": "the detailed description that is shown when you examine",
        "_level": "the level of the creature",
        "_maxhp": "the health of the creature",
        "_hostile": "whether the creature attacks on sight or not",
        "_frequency": "How often its encountered.  Range 1 (rare) to 100"}

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
        self._ac = 0                # auto-generated based on level
        self._exp = 0               # auto-generated after load

        self._maxhp = 100           # Starting hit points - range 0..1023
        self._hp = self._maxhp      # Current hit points - autoset if 0
        self._regenerate = False    # Regenerates hit points during attack

        self._frequency = 50        # 0-100 with 100 being the most often
        self._TimeToFirstAttack = 10   # of seconds to wait before hostile atk
        self._attackSpeed = 10      # how fast a monter attacks

        self._objDropList = []      # list of item nums that creature may drop
        self._numOfItemsDropped = [1, 2, 3]  # number of items dropped - random

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
        self._spellCaster = False    # can cast spells
        self._antiMagic = False      # immune to spells
        self._magicImmunity = False  # immune to attacks from non-magic weapons
        self._fleeIfAttacked = False     # chance to run away when attacked
        self._assistCreature = []        # Which creatures it calls for help
        self._defendCreature = []        # Which creatures it will defend
        self._attackLastAttacker = True  # If false attack first attacker
        self._attackIfPietyLessThan = 3  # 0=ignore
        self._attackIfPietyMoreThan = 0  # 0=ignore

        self._creationDate = datetime.now()  # ag - when creatObj was created
        self._enterRoomTime = getNeverDate()  # ag - when creture entered room
        self._attackPlayer = ''     # auto-generated - Who creature is atking

        self._permanent = False
        self._unique = False         # only one allowed in room at a time
        self._watch = False

        self._parleyAction = 'None'    # Which of the parley actions to take
        self._parleyNone = ['does not respond', 'says nothing',
                            'has no reaction']
        self._parleyPositive = ["Hello there, friend.", "Well, hello!"]
        self._parleyNegative = ["Buzz off, scumbag!", 'Leave me alone.']
        self._parleyCustom = ["Have you heard about the burried treasure " +
                              " below town hall?"]
        self._parleyTeleport = ["recites some exotic words and you are " +
                                "whisked away.", "whispers something " +
                                "incomprehendible before you vanish into " +
                                "thin air"]
        self._parleySell = ["Hey buddy.  Check this out"]
        self._parleySellItems = self._objDropList
        self._parleyTeleportRooms = range(2, 300)

        self._instanceDebug = Creature._instanceDebug

        logging.debug("Creature __init__" + str(self._creatureId))

        return(None)

    def debug(self):
        return(pprint.pformat(vars(self)))

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

    def getLevel(self):
        return(self._level)

    def getHitPoints(self):
        return(self._hp)

    def setHitPoints(self, num=0):
        if num:
            self._hp = int(num)
        else:
            self._hp = self.getMaxHitPoints()

    def setEnterRoomTime(self):
        self._enterRoomTime = datetime.now()

    def getMaxHitPoints(self):
        return(self._maxhp)

    def getName(self):
        return(self._name)

    def getFrequency(self):
        return(self._frequency)

    def fleesIfAttacked(self):
        return(self._fleeIfAttacked)

    def isAttacking(self):
        if self._attackPlayer is not None:
            return(True)
        return(False)

    def isInvisible(self):
        return(self._invisible)

    def isHidden(self):
        return(self._hidden)

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

    def getAttackPlayer(self):
        if self.isAttacking():
            return(self._attackPlayer)
        return(None)

    def setAttackPlayer(self, player):
        self._attackPlayer = player

    def initiateAttack(self, charObj=None):
        ''' Returns true if creature initiates attack on player '''
        if not charObj:
            charObj = self.getAttackPlayer()

        if not charObj:
            return(False)

        if not self.notices(charObj):
            return(False)

        if charObj != self.getAttackPlayer():
            self.setAttackPlayer(charObj)        # initiate attack
            return(True)

        return(False)

    def attack(self, charObj=None):
        if not charObj:
            charObj = self.getAttackPlayer()

        if not charObj:
            return(False)

        if charObj != self.getAttackPlayer():
            self.setAttackPlayer(charObj)        # initiate attack

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
           * for each of those, randomly pick an objNum from the objDropList
           * for each of those, load the object and add it to the inventory
           * typically run at creature load time
        '''
        if not self._permanent:
            self.clearInventory()

        for itemNum in range(1,
                             getRandomItemFromList(self._numOfItemsDropped)):
            itemId = getRandomItemFromList(self._objDropList)
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
        secondaryAtts = ['_magicImmunity', '_antiMagic', '_spellCaster',
                         '_hidden', '_regenerate', '_steal', '_drain',
                         '_poison', '_kidnap', '_invisible', '_sendToJail']
        if which == 'primary':
            mylist = primaryAtts
        else:
            mylist = secondaryAtts

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

        if self.getLevel() in range(6, 8):
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
        return(getRandomItemFromList(self._parleyTeleportRooms))

    def getParleySaleItem(self):
        return(self.getRandomInventoryItem())

    def getParleyTxt(self):
        buf = ''

        if self._parleyLevel.lower() == 'positive':
            buf += getRandomItemFromList(self._parleyPositive)
        elif self._parleyLevel.lower() == 'negative':
            buf += getRandomItemFromList(self._parleyNegative)
        elif self._parleyLevel.lower() == 'custom':
            buf += getRandomItemFromList(self._parleyCustom)
        elif self._parleyLevel.lower() == 'sell':
            buf += getRandomItemFromList(self._parleySell)
        elif self._parleyLevel.lower() == 'teleport':
            buf += getRandomItemFromList(self._parleyTeleport)
        else:
            buf += "The " + self._name + " " + self._parleyNone

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
        # integer attributes
        intAtt = []
        # boolean attributes
        boolAtt = []
        # obsolete attributes (to be removed)
        obsoleteAtt = []

        for attName in intAtt:
            try:
                newVal = int(getattr(self, attName, 0))
            except ValueError:
                newVal = 0
            setattr(self, attName, newVal)
        for attName in boolAtt:
            try:
                newVal = bool(getattr(self, attName, False))
            except ValueError:
                newVal = False
            setattr(self, attName, newVal)
        for attName in obsoleteAtt:
            try:
                delattr(self, attName)
            except AttributeError:
                pass
