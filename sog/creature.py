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
from common.general import dLog
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
                          '_parleySellItems', '_attackSpeed',
                          '_TimeToFirstAttack', '_damage']

    attributesThatShouldntBeSaved = ['_creationDate', '_currentlyAttacking',
                                     '_enterRoomTime', '_instanceDebug',
                                     '_invWeight', '_invValue',
                                     '_attackPlayer', '_lastAttackDate',
                                     '_secondsUntilNextAttack']

    intAttributes = ['_weight', '_value', '_level', '_exp', '_ac',
                     '_damagePct', '_tohit', '_dodge', '_frequency',
                     '_timeToFirstAttack', '_attackRate',
                     '_attackIfPietyLessThan', '_attackIfPietyMoreThan']

    boolAttributes = ['_regenerate', '_hostile', '_defend', '_follow',
                      '_blockFromLeaving', '_guardTreasure', '_sendToJail',
                      '_noKill', '_kidnap', '_hidden', '_invisible', '_drain',
                      '_poison', '_undead', '_rust', '_steal', '_carry',
                      '_antiMagic', '_magicImmunity', '_fleeIfAttacked',
                      '_attackLastAttacker', '_permanent', '_unique', '_watch']

    strAttributes = ['_name', '_article', '_pluraldesc', '_longdesc',
                     '_alignment', '_parleyAction']

    listAttributes = ['_assistCreature', '_defendCreature', '_offensiveSpells',
                      '_itemCatalog', '_numOfItemsCarried', '_parleyTxt',
                      '_parleyTeleportRooms']

    _levelDefaultsDict = {
        1: {
            '_exp': 10,
            '_ac': 0,
            '_maxhp': 30,
            '_tohit': 0,
            '_dodge': 0
        },
        2: {
            '_exp': 20,
            '_ac': 0,
            '_maxhp': 50,
            '_tohit': 0,
            '_dodge': 0
        },
        3: {
            '_exp': 30,
            '_ac': 1,
            '_maxhp': 70,
            '_tohit': 10,
            '_dodge': 0
        },
        4: {
            '_exp': 40,
            '_ac': 1,
            '_maxhp': 100,
            '_tohit': 10,
            '_dodge': 0
        },
        5: {
            '_exp': 50,
            '_ac': 2,
            '_maxhp': 150,
            '_tohit': 10,
            '_dodge': 0
        },
        6: {
            '_exp': 90,
            '_ac': 2,
            '_maxhp': 200,
            '_tohit': 10,
            '_dodge': 0
        },
        7: {
            '_exp': 200,
            '_ac': 3,
            '_maxhp': 500,
            '_tohit': 10,
            '_dodge': 0
        },
        8: {
            '_exp': 300,
            '_ac': 3,
            '_maxhp': 700,
            '_tohit': 20,
            '_dodge': 0
        },
        9: {
            '_exp': 1000,
            '_ac': 4,
            '_maxhp': 1000,
            '_tohit': 20,
            '_dodge': 10
        },
        10: {
            '_exp': 3000,
            '_ac': 5,
            '_maxhp': 3000,
            '_tohit': 30,
            '_dodge': 10

        },
        11: {
            '_exp': 4000,
            '_ac': 6,
            '_maxhp': 4000,
            '_tohit': 40,
            '_dodge': 20
        },
        12: {
            '_exp': 5000,
            '_ac': 7,
            '_maxhp': 5000,
            '_tohit': 50,
            '_dodge': 20
        },
        99: {
            '_exp': 8000,
            '_ac': 8,
            '_maxhp': 10000,
            '_tohit': 60,
            '_dodge': 30
        }
    }

    _baseStatDict = {
        1: {'_damage': 3},
        2: {'_damage': 6},
        3: {'_damage': 9},
        4: {'_damage': 12},
        5: {'_damage': 15},
        6: {'_damage': 20},
        7: {'_damage': 25},
        8: {'_damage': 35},
        9: {'_damage': 50},
        10: {'_damage': 75},
        11: {'_damage': 100},
        12: {'_damage': 150},
        99: {'_damage': 200}
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
        "_damagePct": "multiplier for default damage - 100% = normal, +/-10%",
        "_tohit": "additional chance to hit/miss target - 10% increments",
        "_hostile": "whether the creature attacks on sight or not",
        "_parleyAction": ("What the creature does when it's talked to.\n" +
                          "  Active values: Sell, Teleport, Attack\n" +
                          "  Canned Responses: None, Positive, Negative"),
        "_itemCatalog": "Which items the creature can be carrying",
        "_numOfItemsCarried": "Possible number of objects carried",
        "_frequency": "How often its encountered.  Range 1 (rare) to 100",
        "_frequency": "How often its encountered.  Range 1 (rare) to 100",
        "_timeToFirstAttack": "# of seconds to wait before hostile atk",
        "_attackRate": "speed of creature attacks.  100%=normal - 50%=slow"}

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
        self._tohit = 0             # inital value auto-filled based on lvl
        self._damagePct = 100       # inital value
        self._dodge = 0             # inital value auto-filled based on lvl

        self._maxhp = 100           # Starting hit points - range 0..1023
        self._hp = 100              # Current hit points - autoset if 0
        self._regenerate = False    # Regenerates hit points during attack

        self._frequency = 50        # 0-100 with 100 being the most often
        self._timeToFirstAttack = 10   # of seconds to wait before hostile atk
        self._attackRate = 100     # how fast a monter attacks  100=normal

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
        self._lastAttackDate = getNeverDate()  # ag
        self._secondsUntilNextAttack = 0

        self._permanent = False      # stays in room when room is not active
        self._unique = False         # only one allowed in room at a time
        self._watch = False          # notify dm if attacked

        self._parleyAction = 'None'    # Which of the parley actions to take
        self._parleyTxt = self._parleyDefaultsDict['None']
        self._parleyTeleportRooms = []  # room to transport to.  empty=1-300

        self._alignment = 'neutral'  # Values: neutral, good, evil

        self._instanceDebug = Creature._instanceDebug

        logging.debug("Creature __init__" + str(self._creatureId))

        dLog("Creature init called for " + str(self.getId()),
             self._instanceDebug)
        return(None)

    def __del__(self):
        dLog("Creature destructor called for " + str(self.getId()),
             self._instanceDebug)

    def debug(self):
        return(pprint.pformat(vars(self)))

    def toggleInstanceDebug(self):
        self._instanceDebug = not self._instanceDebug

    def getInstanceDebug(self):
        return(self._instanceDebug)

    def setInstanceDebug(self, val):
        self._instanceDebug = bool(val)

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

    def kidnaps(self):
        return(self._kidnap)

    def sendsToJail(self):
        return(self._sendToJail)

    def blocksFromLeaving(self):
        return(self._blockFromLeaving)

    def guardsTreasure(self):
        return(self._guardTreasure)

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

    def flees(self, percentChanceOfFleeing=20):
        ''' Returns true if creature flees
            * creature must have _fleeIfAttacked attribute set
            * creature must be at 10% health or less
            * after that, 20% (by default) chance of flee '''
        if not self.fleesIfAttacked():
            return(False)

        if self.getHitPoints() <= (self.getMaxHitPoints() * .10):
            if random.randint(1, 100) <= percentChanceOfFleeing:
                return(True)
        return(False)

    def getEquippedWeaponToHit(self):
        ''' creatures don't have weapons, so we just use their _tohit att '''
        return(self._tohit)

    def attacksBack(self):
        return(self._defend)

    def damageIsLethal(self, num=0):
        if num >= self.getHitPoints():
            return(True)
        return(False)

    def setEnterRoomTime(self):
        self._enterRoomTime = datetime.now()

    def getMaxHitPoints(self):
        return(self._maxhp)

    def getName(self):
        return(self._name)

    def getAc(self):
        return(self._ac)

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

    def getDamage(self):
        damage = int(self._baseStatDict[self.getLevel()]['_damage'] *
                     self._damagePct / 100)
        return(damage)

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

    def getEquippedWeaponDamage(self, percentSwing=15):
        ''' calculate creature 'weapon' damage
            * creatures don't have weapons equipped.  Instead, we treat their
              damage attribute as a weapon with some random fluctuation '''
        damage = self.getDamage()
        damageAdj = int(damage * percentSwing / 100)
        damage += random.randInt(-(damageAdj), damageAdj)
        return(damage)

    def acDamageReduction(self, damage):
        ''' reduce damage based on AC '''
        acReduction = int(damage * (.05 * self.getAc()))
        damage -= acReduction
        return(max(0, damage))

    def getCumulativeDodge(self):
        ''' return percentage to avoid a hit '''
        return(self._dodge)

    def hitsCharacter(self, charObj):
        ''' return true if creature hits the character '''
        # todo: figure out formula
        # fumble
        return(True)

    def fumbles(self, basePercent=20, secsToWait=20):
        ''' Return true if creature fumbles.
            * creature must wait 20 seconds before attacking
        '''
        fumbles = False

        fumbleRoll = random.randint(1, 100)
        if fumbleRoll == 1:  # always a 1% change of fumbling
            fumbles = True
        elif fumbleRoll < basePercent - (self.getLevel() * 2):
            fumbles = True
            self.setSecondsUntilNextAttack(secsToWait)
        return(fumbles)

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
        itemCount = int(getRandomItemFromList(self._numOfItemsCarried))

        if not itemCount:   # 0 items carried
            return(True)

        for itemNum in range(1, itemCount + 1):  # +1 due to exclusive ranges
            itemId = getRandomItemFromList(self._itemCatalog)
            if not itemId:
                continue
            if "/" not in itemId:
                continue

            dLog("creature.autoPopulateInventory: obj = " + itemId)
            oType, oNum = itemId.split('/')
            obj1 = ObjectFactory(oType, oNum)
            obj1.load()
            self.addToInventory(obj1)
        return(True)

    def postLoad(self):
        ''' hook that runs after creature is loaded '''
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

        msg = getRandomItemFromList(self._parleyTxt)
        if not msg:
            buf += "The " + self._name + " does not respond."
        elif self._parleyAction.lower() == 'none':
            buf += "The " + self._name + " " + msg + '.'
        else:
            buf += "The " + self._name + " says, " + msg + '.'

        return(buf)

    def notices(self, charObj):
        ''' returns true if the creature notices the character '''
        if charObj.isHidden() or charObj.isInvisible():
            return(False)

        # todo: add rand/luck?

        if self._enterRoomTime == getNeverDate():
            self.setEnterRoomTime()
            return(False)

        if secsSinceDate(self._enterRoomTime) > self._timeToFirstAttack:
            return(True)
        else:
            return(False)

        return(True)

    def getAttackRate(self):
        return(self._attackRate)

    def setLastAttack(self):
        self._lastAttackDate = datetime.now()

    def getLastAttack(self):
        return(self._lastAttackDate)

    def setSecondsUntilNextAttack(self, secs=10):
        self._secondsUntilNextAttack = int(secs)

    def getSecondsUntilNextAttack(self):
        return(self._secondsUntilNextAttack)

    def canAttack(self):
        ''' returns true if the creature is ready for an attack '''
        debugPrefix = "Creature.canAttack (" + str(self.getId()) + "): "

        # Creature has no attack speed.  Will never be ready
        if not self.getAttackRate():
            dLog(debugPrefix + "Creature has no attack rate",
                 self._instanceDebug)
            return(False)

        # Check if the appropriate amount of time has pased
        timeLeft = int((self.getSecondsUntilNextAttack() /
                       (self.getAttackRate() / 100)) -
                       secsSinceDate(self.getLastAttack()))
        if timeLeft > 0:
            dLog(debugPrefix + "Attack discarded due to time - " +
                 str(timeLeft) + " secs left", self._instanceDebug)
            return(False)

        # % chance that creature does not attack
        randX = random.randint(1, 10)
        if randX == 1:
            self.setLastAttack()
            dLog(debugPrefix + "Creature randomly chose not to attack (" +
                 str(randX) + ' = 1)', self._instanceDebug)
            return(False)

        dLog(debugPrefix + "Creature is ready for attack", self._instanceDebug)
        return(True)

    def fixAttributes(self):
        ''' Sometimes we change attributes, and need to fix them in rooms
            that are saved.  This method lets us do that.  Typically this
            involves casting types or removing obsolete vars, but we could
            also use this for copying values from one attribute to another '''

        try:
            self._attackRate = self._attackSpeed
        except (AttributeError, TypeError):
            pass
        try:
            self._timeToFirstAttack = self._TimeToFirstAttack
        except (AttributeError, TypeError):
            pass

        AttributeHelper.fixAttributes(self)
