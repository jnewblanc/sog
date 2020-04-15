''' creature Class '''     # noqa

from datetime import datetime
import logging
import pprint
import random

from common.storage import Storage
from common.attributes import AttributeHelper
from common.general import getNeverDate, getRandomItemFromList, secsSinceDate
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


class Creature(Storage, AttributeHelper):

    _instanceDebug = False

    creatureSpellList = ['poison', 'fireball', 'lightning', 'befuddle']

    attributesThatShouldntBeSaved = []

    _levelToExpDict = {
                       '1': 10,
                       '2': 20,
                       '3': 30,
                       '4': 40,
                       '5': 50,
                       '6': 90,
                       '7': 200,
                       '8': 300,
                       '9': 1000,
                       '10': 3000,
                       '11': 4000,
                       '12': 5000,
    }

    def __init__(self, id=0):
        self._name = ""
        self._creatureID = id

        self._name = ''
        self._ac = 0
        self._exp = 0               # gets generated after load
        self._level = 1             # determines experience - range 0..64
        self._longdesc = ''

        self._maxhp = 10            # Starting hit points - range 0..1023
        self._hp = 10               # Current hit points - autoset if 0
        self._regenerate = True     # Regenerates hit points during attack

        self._pluraldesc = ''
        self._singledesc = ''
        self._value = 0             # NOT NEEDED?
        self._weight = 5            # Not NEEDed?

        self._objDropList = []      # list of item nums that creature may drop
        self._numOfItemsDropped = []  # number of items dropped - random
        self._inventory = []        # list of items that creature is carrying

        self._defendCreature = ''   # Which creatures it will defend
        self._defendCreature = ''   # Which creatures it calls for help
        self._hostile = False
        self._permanent = True
        self._defend = False        # Wont attack back if attacked
        self._blockFromLeaving = True  # 50% stop atking player frm leving room
        self._follow = True         # chance to follow if player leaves room
        self._guardTreasure = True  # can't pick up treasure w/ creat in room
        self._sendToJail = True     # if attacked player loses weapon & jailed
        self._attackLastAttacker = True  # If false attack first attacker
        self._hidden = True         # Can't see monster until engaged
        self._invisible = True      # Can’t see + “to hit” has 20% penalty
        self._drain = True          # Chance to drain level (50% of the time)
        self._poison = True         # On hit may poison player
        self._antiMagic = True      # immune to spells
        self._undead = True         # can be turned by clerics and paladins
        self._attackIfPietyLessThan = 7  # 0=ignore
        self._attackIfPietyMoreThan = 7  # 0=ignore
        self._fleeIfAttacked = True      # chance to run away when attacked

        self._frequency = 0         # 0-100 with 100 being the most often
        self._TimeToFirstAttack = 10   # of seconds to wait before hostile atk
        self._attackSpeed = 0       # how fast a monter attacks
        self._creationTime = datetime.now()  # when creatureObj was created
        self._enterRoomTime = getNeverDate()  # when creture entered room
        self._attackPlayer = ''     # Who the creature is currently attacking

        self._kidnap = False         # Capture Instead of death
        self._callsForAssitance = True
        self._spellCaster = True     # can cast spells
        self._magic = True           # immune to attacks from non-magic weapons
        self._summonHelp = True
        self._cursed = False
        self._rust = False           # causes armor to rust and lose extra hits
        self._unique = False
        self._watch = True
        self._nice = True
        self._noKill = False          # players can't attack if set

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

        logging.debug("Creature __init__" + str(self._creatureID))

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

    def populateInventory(self):
        ''' create creature inventory
           * randomly pick the number of items from the numOfItemsDropped list
           * for each of those, randomly pick an objNum from the objDropList
           * for each of those, load the object and add it to the inventory
           * typically run at creature load time
        '''
        for itemNum in range(1,
                             getRandomItemFromList(self._numOfItemsDropped)):
            itemId = getRandomItemFromList(self._objDropList)
            if "/" not in itemId:
                continue

            oType, oNum = itemId.split('/')
            obj1 = ObjectFactory(oType, oNum)
            obj1.load()
            self._inventory.append(obj1)
        return(True)

    def postLoad(self):
        self.setExp()            # calculate exp and set it
        if not self.getHitPoints():
            self.setHitPoints()  # set hp to the maxHP for this creature
        self.populateInventory()

    def getAttributeCount(self, which='primary'):
        ''' Returns the number of attributes set to True.
            Distinguishes between primary and secondary attribute types '''
        count = 0
        primaryAtts = ['_block', '_follow', '_guard', '_fastreact',
                       '_moralreact', '_flee', 'undead', 'rust', 'steal']
        secondaryAtts = ['_magic', '_antimagic', '_spellcasting',
                         '_invisible', '_regenerate', '_level' '_drain',
                         '_poison', '_kidnap']
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

        exp += self.getMaxHitPoints() + self._levelToExpDict[self.getLevel()]

        # Monster level	Bonus
        monsterLevelBonus = (((self.getAttributeCount('primary') + 2) *
                             self.getAttributeCount('secondary')) *
                             (self.getMaxHitPoints() / 10))

        if self.getLevel() in range(6, 8):
            monsterLevelBonus *= 2
        elif self.getLevel() > 8:
            monsterLevelBonus *= 6

        self._exp = (exp + monsterLevelBonus)
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
        if not self.inventory:
            return(None)
        return(getRandomItemFromList(self._inventory))

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
