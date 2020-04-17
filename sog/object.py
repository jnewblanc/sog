''' Object Class '''   # noqa

import bisect
import datetime
import logging
import pprint
import random
# import re

from common.attributes import AttributeHelper
from common.editwizard import EditWizard
from common.storage import Storage

# create obj staff in chest in 3001,ty=magdevice,magic=true,spell=3,
#    value=1000,charges=2


class Object(Storage, EditWizard):
    ''' object class '''

    _instanceDebug = False

    # integer attributes
    intAttributes = ['_weight', '_value']
    # boolean attributes
    boolAttributes = ['_carry', '_equipable', '_hidden', '_invisible',
                      '_magic', '_permanent', '_usable']
    strAttributes = ['_name', '_article', '_singledesc', '_pluraldesc',
                     '_longdesc']
    listAttributes = ['_classesAllowed', '_alignmentsAllowed',
                      '_gendersAllowed']
    # obsolete attributes (to be removed)
    obsoleteAttributes = ['_correspondingRoomNum', "_classeAllowed",
                          '_alignmentAllowed', '_genderAllowed']

    attributesThatShouldntBeSaved = ['']

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc",
                        "_longdesc", "_weight", "_value"]

    attributeInfo = {
        "_name": "single word that you use when interacting with item",
        "_article": "the article of speech.  For example: a, an, some.",
        "_singledesc": "the description for one of these, minus the article.",
        "_pluraldesc": "the description for two or more of these.",
        "_longdesc": "full description when item is examined.",
        "_weight": "how much the item weighs.  Range 0-80 lbs.",
        "_value": "the base amount used when calculating the sale value.",
        "_spell": "the spell that is cast when using this item.",
        "_maxCharges": "the number of times that item can be used when full.",
        "_ac": "the amount of damage this prevents - Range is 0 (none) to 10.",
        "_dodgeBonus": "increases chance that player is not hit when attacked",
        "_isMetal": "metal can't be used by some classes.",
        "_minimumDamage": "minimim amount of damage inflicted.  Range 0-50.",
        "_maximumDamage": "maximum amount of damage inflicted.  Range 0-80.",
        "_toWhere": "The room that this item takes you to i.e. 35 or Shop/30",
        "_correspondingDoorId": "The id of the corresponding door i.e. Door/5",
        "_lockId": "The id of the lock used to connects a key with a lock",
        "_worksInRoomId": "The id of the room where this item works"}

    def __init__(self, objId=0):
        self.objId = objId
        self._name = ''
        self._article = 'a'
        self._singledesc = ''
        self._pluraldesc = ''
        self._longdesc = ''

        self._carry = True
        self._equippable = False
        self._hidden = False
        self._invisible = False
        self._magic = False
        self._permanent = False
        self._usable = False
        self._cursed = False

        self._weight = 1
        self._value = 1

        self._classesAllowed = []
        self._alignmentsAllowed = []
        self._gendersAllowed = []
        self._minLevelAllowed = 0
        self._maxLevelAllowed = 100

        return(None)

    def describe(self, count=1):
        if count > 1:
            return(count + " " + self._pluraldesc)
        return(self._article + " " + self._singledesc)

    def debug(self):
        return(pprint.pformat(vars(self)))

    def examine(self):
        return(self._longdesc)

    def isUseable(self):
        return(self._usable)

    def setName(self, name):
        self._name = str(name)

    def setUseable(self):
        self._usable = True

    def use(self):
        return(False)

    def identify(self):
        ROW_FORMAT = "{0:9}: {1:<30}\n"
        buf = ''
        for attName in vars(self):
            attValue = getattr(self, attName)
            buf += ROW_FORMAT.format(attName, attValue)
        return(buf)

    def getId(self):
        return(self.objId)

    def fixAttributes(self):
        ''' Sometimes we change attributes, and need to fix them in rooms
            that are saved.  This method lets us do that.  Typically this
            involves casting types or removing obsolete vars, but we could
            also use this for copying values from one attribute to another '''

        AttributeHelper.fixAttributes(self)
        return(True)

    def isEquippable(self):
        return(self._equipable)

    def isInvisible(self):
        return(self._invisible)

    def isHidden(self):
        return(self._invisible)

    def isCarryable(self):
        return(self._carry)

    def isPermanent(self):
        return(self._permanent)

    def isUsable(self):
        return(self._usable)

    def isMagic(self):
        return(self._magic)

    def isCursed(self):
        return(self._cursed)

    def getValue(self):
        return(max(0, self._value))

    def getWeight(self):
        return(max(0, self._weight))

    def getName(self):
        return(self._name)

    def getType(self):
        return(self.__class__.__name__)

    def getArticle(self):
        return(self._article)

    def getSingular(self):
        return(self._singledesc)

    def getPlural(self):
        return(self._pluraldesc)

    def limitationsAreSatisfied(self, charObj):
        ''' Return True if an items limitations are met '''
        if ((self._classesAllowed and
             charObj.getClass() not in self._classesAllowed)):
            charObj.svrObj.spoolOut(charObj.getClass().capitalize() +
                                    "s are not permitted.\n")
            return(False)
        if ((self._alignmentsAllowed and
             charObj.getAlignment() not in self._alignmentsAllowed)):
            charObj.svrObj.spoolOut("Folks regarded to be " +
                                    charObj.getAlignment() +
                                    " are not allowed.\n")
            return(False)
        if ((self._gendersAllowed and
             charObj.getGender() not in self._gendersAllowed)):
            charObj.svrObj.spoolOut("You have the wrong parts.\n")
            return(False)
        if not charObj.getLevel() >= self._minLevelAllowed:
            charObj.svrObj.spoolOut("You are not experienced enough.\n")
            return(False)
        if not charObj.getLevel() <= self._maxLevelAllowed:
            charObj.svrObj.spoolOut("You are over experienced.\n")
            return(False)
        return(True)

    def adjustPrice(price):
        ''' adjust price based on object attributes '''
        return(price)

    def isMagicItem(self):
        ''' This is meant to be overridden if needed '''
        return(False)

    def isSmashable(self, obj):
        ''' This is meant to be overridden if needed '''
        return(False)

    def isPickable(self, obj):
        ''' This is meant to be overridden if needed '''
        return(False)

    def isOpenable(self, obj):
        ''' This is meant to be overridden if needed '''
        return(False)

    def isClosable(self, obj):
        ''' This is meant to be overridden if needed '''
        return(False)

    def canBeRepaired(self):
        ''' This is meant to be overridden if needed '''
        return(False)

    def getAc(self):
        ''' This is meant to be overridden if needed '''
        return(0)

    def getDodgeBonus(self):
        ''' This is meant to be overridden if needed '''
        return(0)

    def canBeEntered(self, charObj):
        ''' This is meant to be overridden if needed '''
        return(False)


class Exhaustible(Object):
    ''' superclass of objects that have a limited lifespan '''

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc",
                        "_longdesc", "_maxCharges", "_weight", "_value"]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._maxCharges = 100    # max number of charges (constant)
        self._charges = 100       # number of charges remaining (counter)
        self._timesRepaired = 0   # number of times repaired (counter)
        self._cooldown = 0        # Time between uses (in seconds)
        self._broken = False
        self._breakable = True
        self._depletable = True
        self._lastUse = None

    def setLastUse(self):
        self._lastUse = datetime.now()

    def getLastUse(self):
        return(self._lastUse)

    def isCool(self):
        ''' Return True if object cooldown is complete '''
        if self._cooldown == 0:
            return(True)    # No cooldown is required
        if (self._lastUse - datetime.now()).total_seconds() > self._cooldown:
            return(True)
        return(False)

    def percentOfChargesRemaining(self):
        return (self._charges * 100 / self._maxCharges)

    def canBeRepaired(self):
        ''' Return True if an item can be repaired '''
        if self._broken or self.charges == 0:
            return(False)                 # broken items can not be repaired
        if self._maxCharges > 10 and self.percentOfChargesRemaining() > 20:
            return(False)                 # 20%+ charged items can be repaired
        elif self._maxCharges <= 10 and self._charges > 1:
            return(False)              # Small items need to be on last charge
        return(True)

    def repair(self):
        ''' add charges back onto item
            The first time an item is repaired, it restores 80% of max charges.
            Each additional repair restores 10% fewer charges, meaning that.
            there are diminishing returns '''
        if not self.canBeRepaired():
            return(False)
        newChargePercentage = .8           # 80% - amount of charges added back
        reduceBy = (.1 * self._timesRepaired)  # reduce % for each repair
        newChargePercentage -= reduceBy
        self._charges = int(self._maxCharges * newChargePercentage)
        self._timesRepaired += 1

    def setMaxCharges(self, num):
        self._maxCharges = int(num)

    def getMaxCharges(self):
        return(self._maxCharges)

    def setCharges(self, num):
        self._charges = int(num)

    def getCharges(self):
        return(self._charges)

    def decrementChargeCounter(self, num=1):
        if self._depletable:
            self._charges -= num
        if self._charges <= 0:
            if self._breakable:
                self._broken = True

    def isBroken(self):
        return(self._broken)

    def isDepleated(self):
        if self._charges > 0:
            return(True)
        return(False)

    def isUsable(self):
        if not self.isBroken() and not self.isDepleated():
            return(True)
        return(False)

    def adjustPrice(self, price):
        ''' adjust price based on percentage of charges remaining'''
        price *= (self.percentOfChargesRemaining() / 100)
        return(int(price))


class Equippable(Object):
    ''' superClass for objects that are wearable or wieldable
        These objects have an _equippedSlotName that corresponds to the
        character slots '''

    def __init__(self, objId=0):
        super().__init__(objId)
        self._equippedSlotName = ''
        self._equipable = "True"
        self._usable = "True"

    def setEquippedSlotName(self, slotStr):
        self._equippedSlotName = str(slotStr)

    def getEquippedSlotName(self):
        return(self._equippedSlotName)


class MagicalDevice(Exhaustible):
    ''' SuperClass for magic staffs, potions, and similar spell-casting
        devices.  Unlike casting a spell from memory, there are no int
        requirements and no spell points required to activate spells from
        these items '''

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc",
                        "_longdesc", "_spell", "_weight", "_value"]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._spell = ''
        # Spell number, range 1..17. 1:vigor, 2:heal, 3:fireball, 4:lightning,
        # 5:hurt, 6:curepoison, 7:disintegrate, 8:befuddle, 9:teleport,
        # 10:wish, 11:passdoor, 12:enchant, 13:bless, 14:protection, 15:curse,
        # 16:poison, 17:intoxicate.
        self._magicLvlRequired = 0
        self._usable = True
        self._magic = True
        return(None)

    def isMagicItem(self):
        return(True)

    def getSpell(self):
        return(self._spell)


class Closable(Object):
    ''' superclass of objects that can be opened and closed '''
    def __init__(self, objId=0):
        super().__init__(objId)
        self._closed = False
        self._locked = False
        self._poison = False  # when trapped, this flag inflicts poison
        self._spring = True   # automatically close if nobody is in the room
        self._locklevel = 0  # 0=no lock, -1=unpickable, 1=minor lock
        self._traplevel = 0  # 0=no trap, 1=minor trap
        self._lockId = 0     # keys matching this lockId will open it
        self._toll = 0       # 0=no toll, amount to deduct to open
        self._permanent = True
        return(None)

    def fixAttributes(self):
        attName = "_spring"
        try:
            newVal = bool(getattr(self, attName, False))
        except ValueError:
            newVal = False
        setattr(self, attName, newVal)

        AttributeHelper.fixAttributes(self)
        return(True)

    def getLockLevel(self):
        return self._locklevel

    def getTrapLevel(self):
        return self._traplevel

    def isSmashable(self, charObj):
        if self.isClosed():
            # Time check - can only smash every 15 seconds
            if charObj.secsSinceLastAttack() < 15:
                return(False)
            return(True)
        return(False)

    def isPickable(self, charObj):
        if self.isClosed() and self.isLocked():
            # Time check - can only smash every 15 seconds
            if charObj.secsSinceLastAttack() < 15:
                return(False)
            return(True)
        return(False)

    def isOpenable(self, charObj):
        if self.isClosed() and not self.isLocked():
            return(True)
        return(False)

    def isClosable(self):
        if self.isClosed():
            return(False)
        return(True)

    def isLockable(self):
        if self.isClosed() and self.isUnlocked() and self.getLockLevel() > 0:
            return(True)
        return(False)

    def isUnlockable(self):
        if self.isClosed() and self._isLocked() and self.getLockLevel() > 0:
            return(False)
        return(True)

    def isTrapped(self):
        if self._traplevel > 0:
            return(True)
        return(False)

    def hasToll(self):
        if self._toll > 0:
            return(True)
        return(False)

    def hasSpring(self):
        return(self._spring)

    def isClosed(self):
        if self._closed:
            return(True)
        return(False)

    def isLocked(self):
        if self._locked:
            return(True)
        return(False)

    def isUnlocked(self):
        if self._locked:
            return(False)
        return(True)

    def smash(self, charObj):
        ''' Smash open object - return True if object is opened.
            Smash does not trigger traps, but does cause damage
        '''

        if not self.isSmashable():
            return(False)

        if not charObj.checkCooldown(15):
            return(False)
        else:
            charObj.setLastAttack()

        charHp = charObj.getHitPoints()
        if self.smashSucceds(charObj):
            damage = self.smashDamage(charObj, self.getWeight(), True)
            charObj.svrObj.spoolOut(self.smashTxt(damage, True, charHp))
            charObj.takeDamage(damage)
            self._closed = 'False'
            self.save()
            return(True)
        else:
            damage = self.smashDamage(charObj, self.getWeight(), False)
            charObj.svrObj.spoolOut(self.smashTxt(damage, False, charHp))
            charObj.takeDamage(damage)
        return(False)

    def pick(self, charObj):
        ''' Pick lock on an object (also opens it)
           * return True if object is opened
           * Damage is delt only on failed attempts when there are traps
           * Dex and class used in pick calculation
        '''
        if not self.isPickable():
            return(False)

        if self.getLockLevel() <= 0:                   # Can't pick these doors
            return(False)

        if not charObj.checkCooldown(15):
            return(False)
        else:
            charObj.setLastAttack()

        if self.pickSuccess(charObj):
            self._locked = 'False'
            self._closed = 'False'
            self.save()
            return(True)
        elif self.traplevel > 0:
            if not self.avoidTrap(charObj):
                damage = self.trapDamage(charObj, self.getTrapLevel())

                trapTxt = self.trapTxt(damage, poison=self._poison,
                                       currenthealth=charObj.getHitPoints())
                charObj.svrObj.spoolOut(trapTxt)
                charObj.takeDamage(damage)

            if self._poison:
                if random.randint(1, 100) < charObj.getLuck():
                    charObj.setPoisoned()
            return(False)
        return(False)

    def open(self, charObj):
        ''' Open an object - Returns true if opened '''
        if not self.isOpenable():
            return(False)

        self._closed = 'False'
        self.save()

        if self._traplevel > 0:
            if not self.avoidTrap(charObj):
                damage = self.trapDamage(charObj, self.getTrapLevel())
                trapTxt = self.trapTxt(damage, poison=self._poison,
                                       currenthealth=charObj.getHitPoints())
                charObj.svrObj.spoolOut(trapTxt)
                charObj.takeDamage(damage)
        return(True)

    def close(self):
        self._closed = 'True'
        self.save()

    def smashSucceds(self, charObj):
        ''' Returns True if smash calculations succeed
            * Weight makes it harder to SMASH
            * Strength makes it easier to smash '''

        if random.randint(1, 3) == 1:        # Always a 30% chance of success
            return(True)
        elif (charObj.getStrength() * 10) > self.getWeight():  # stat based
            return(True)
        return(False)

    def smashDamage(self, charObj, weight, succeeded):
        ''' Returns damage from smash calculations
            * Dexterity and Luck are used to see if damage is reduced
            * Constitution determines how much damage is reduced '''

        damage = random.randint(int(weight/2), (weight * 2))  # 50% - 200%
        damage -= min(weight, charObj.calculateAC() * charObj.getLevel())

        # Random chance, based on luck/dex, to reduce damage
        # Reduction amount based on con
        randLuck = random.randint(1, (30 - charObj.getLuck()))
        if randLuck < charObj.getDexterity():
            damage = int(damage / charObj.getConstitution() * 3)

        if succeeded:
            damage = int(damage * .33)         # damage reduced on success

        return(max(0, damage))

    def pickSuccess(self, charObj):
        ''' Returns True if pick calculations succeed
            * Lock level makes it harder to pick
            * Dex makes it easier to pick
            * Rogues get a big pick advantage '''
        if (((charObj.getClass().lower() == 'rogue') and
             (charObj.getDexterity() - 5 > self.getLockLevel()))):
            return(True)
        elif (charObj.getDexterity() - 12) > self.getLockLevel():  # stat based
            return(True)
        return(False)

    def trapDamage(self, charObj, traplevel):
        ''' Returns damage from trap calculations '''
        damage = random.randint(traplevel, traplevel * 10)
        return(max(0, damage))

    def avoidTrap(self, charObj):
        ''' Return true if trap is avoided
            dex, class, and traplevel are used to calulate '''
        trapPercent = 100 + self._traplevel * 10
        if charObj.getClass().lower() == "rogue":
            # Thieves are twice as good at avoiding traps
            trapPercent /= 2
        return(charObj.dodge(trapPercent))

    def smashTxt(self, damage=0, success=False, currenthealth=-1):
        ''' returns the text for the smash '''
        buf = ''
        if (damage >= currenthealth):  # fatal blow
            buf += "Ouch.  That door was stronger than it looked"
        elif damage <= 30:
            buf += "Pieces of the door cut into you!"
        elif damage >= 30:
            buf += "Ouch!  That's one heavy door"
        return(buf)

    def trapTxt(self, damage=0, poison=False, currenthealth=-1):  # no
        ''' returns the text for the trap '''
        buf = ''

        fatalDict = [
                     (0, "You hear a click"),  # only occurs if damage is 0
                     (10, "Spear impales your stomach!"),
                     (50, "A rack of knives falls and crushes you!"),
                     (99999, "Tons of rocks tumble down upon you!"),
                     ]

        poisonDict = [
                     (0, "You hear a click"),  # only occurs if damage is 0
                     (10, "Poison dart!"),
                     (20, "Poison needles!"),
                     (50, "Cobra lunges at you!"),
                     (99999, "Gas spores explode!"),
                     ]

        normalDict = [
                      (0, "You hear a click"),  # only occurs if damage is 0
                      (5, "Splinters on your hand!"),
                      (10, "Spring dart!"),
                      (15, "Small knife flies at you!"),
                      (20, "Spear shoots out of the ground at you!"),
                      (30, "Putrid dust sprays in your eyes!"),
                      (40, "Grubs bite you!"),
                      (50, "Steel wire cuts your hand!"),
                      (60, "Needles stab your toes!"),
                      (70, "Blam!  Explosion in your face!"),
                      (80, "Acid splashes in your face!"),
                      (90, "Flames shoot out at you!"),
                      (99999, "Boooooom!"),
                      ]

        if (damage >= currenthealth):  # fatal blow
            pos = bisect.bisect_right(fatalDict, (damage,))
            buf += str(fatalDict[pos][1])
        elif poison:
            pos = bisect.bisect_left(poisonDict, (damage,))
            buf += str(poisonDict[pos][1])
        else:
            pos = bisect.bisect_left(normalDict, (damage,))
            buf += str(normalDict[pos][1])

        if buf == '':
            buf = "You are hit by a trap."
        return(buf)

    def poison(self, charObj, chanceToAvoid=20):
        ''' Returns true/false depending on whether the player is poisoned '''
        randX = random.randint(1, 100)
        if charObj.getClass() == "ranger":
            # Rangers are much less likely to be poisoned
            chanceToAvoid = (chanceToAvoid * 3) + charObj.getLevel
        if (randX > chanceToAvoid):
            return(True)
        return(False)


class Armor(Equippable, Exhaustible):

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc",
                        "_longdesc", "_ac", "_dodgeBonus", "_maxCharges",
                        "_weight", "_value", "_isMetal"]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._dodgeBonus = 0       # Percent - Extra chance of not being hit
        self._ac = 0               # Each point is 5% damage reduction
        self._isMetal = True
        self.setUseable()
        self.equippedSlotName = '_equippedArmor'  # see Character Class

        return(None)

    def getAc(self):
        return(self._ac)

    def getDodgeBonus(self):
        return(self._dodgeBonus)

    def use(self):
        if self.wear():
            return(True)
        return(False)


class Weapon(Equippable, Exhaustible):
    ''' Weapon Object -
        Players have skills in each of the four types of weapon.
        Weapons can be repaired (i.e., have strikesleft increase) at the
        repair shop (room 18) as long as “strikesleft” is more than 0.
        There’s a 50% chance that the repair will be botched if the weapon is
        magical or has MH more than 30.'''

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc",
                        "_longdesc", "_minimumDamage", "_maximumDamage",
                        "_maxCharges", "_weight", "_value"]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._minimumDamage = 0
        self._maximumDamage = 10
        self._toHitBonus = 0  # Each 1 is a +5% chance to hit
        self.equippedSlotName = '_equippedWeapon'  # see Character Class

        return(None)


class Shield(Equippable, Exhaustible):

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc",
                        "_longdesc", "_ac", "_dodgeBonus", "_maxCharges",
                        "_weight", "_value"]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._dodgeBonus = 0       # Percent - Extra chance of not being hit
        self._ac = 0               # Each point is 5% damage reduction
        self.equippedSlotName = '_equippedShield'  # see Character Class
        return(None)

    def getAc(self):
        return(self._ac)

    def getDodgeBonus(self):
        return(self._dodgeBonus)


class Portal(Object):

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc",
                        "_longdesc", "_toWhere"]

    ''' Portals are similar to doors, but are one-way and not closable '''
    def __init__(self, objId=0):
        super().__init__(objId)
        self._toWhere = ""
        self._toll = 0
        self._carry = False
        self._permanent = True
        return(None)

    def getToWhere(self):
        return(self._toWhere)

    def canBeEntered(self, charObj):
        if self.limitationsAreSatisfied(charObj):
            return(True)
        return(False)


class Door(Portal, Closable):
    ''' Doors are Closables which have a corresponding door who's open/closed
        state is kept in sync '''

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc",
                        "_longdesc", "_toWhere", "_correspondingDoorId",
                        '_weight']

    def __init__(self, objId=0):
        super().__init__(objId)
        self._carry = False
        self._permanent = True
        self._spring = 0           # automatically close when room is loaded
        self._magic = 0            # can't be passed through by magic
        self._weight = 50          # weight impacts smashability
        self._correspondingDoorId = ""
        return(None)

    def canBeEntered(self, charObj):
        if self.isClosed():
            charObj.svrObj.spoolOut(self.name + " is closed")
            return(False)
        if self.limitationsAreSatisfied(charObj):
            return(True)
        return(False)

    def canPassThrough(self):
        if self.isMagic():
            return(False)
        return(True)

    def getCorresspondingDoorId(self):
        return(self._correspondingDoorId)

    def describe(self, count=1):
        if self.isClosed():
            return(self._article + " closed " + self._singledesc)
        else:
            if self._article == "a":
                return("an open " + self._singledesc)
            else:
                return(self._article + " open " + self._singledesc)


class Container(Closable):

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc",
                        "_longdesc"]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._closed = False
        self._locklevel = 0  # 0=unpickable, 1=easy-to-pick

        self._trap = 0
        # When the container is opened or unlocked, this determines the trap
        # that might go off. Thieves are better at avoiding traps; the formula
        # to avoid the trap is DEX - random(6) > (CL mod 10), but for thieves
        # their DEX was multiplied by 2 in this equation.

        self._lockId = 0
        self._maxitems = 5
        self._permanent = True
        self._inventory = []
        return(None)


class Key(Exhaustible):

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc",
                        "_longdesc", "_lockId"]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._lockId = 0   # id=1000 will open any door
        return(None)


class Card(Object):
    ''' special magical device used by DMs that allows the user to teleport
        to any place in the game. It’s not intended for use by players.
          It is activated using:
            use card on PLAYER'''
    def __init__(self, objId=0):
        super().__init__(objId)
        return(None)


class Scroll(MagicalDevice):
    ''' Can study it to see the chant and learn the spell
        Scroll minimums for intelligence and level are -2
        if they are not met, nothing happens and scroll is not ruined '''

    def __init__(self, objId=0):
        super().__init__(objId)
        self._usesRemaining = 1
        return(None)

    def read(self):
        ''' cast the spell - scroll disintegrates '''
        return(None)

    def study(self):
        ''' study the spell to learn it - scroll disintrgrates '''
        return(None)


class Potion(MagicalDevice):
    ''' Potion '''
    def __init__(self, objId=0):
        super().__init__(objId)
        self._usesRemaining = 5
        return(None)


class Staff(MagicalDevice):
    ''' Staff '''
    def __init__(self, objId=0):
        super().__init__(objId)
        self._usesRemaining = 5
        return(None)


class Teleport(MagicalDevice):
    ''' The teleport device sends the recipient to exactly one room, and
        perhaps from only room.  These are sometimes used like special keys
        to access special areas like the Thieves’ lair. Usually the departure
        room is set, so it will only work from one room; the player may need
        to work out clues to figure out where a teleportdevice works.'''

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc",
                        "_longdesc", "_worksInRoomId", "_toWhere", "_weight",
                        "_value"]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._departureRoom = 0  # 0=any room
        self._toWhere = ""
        return(None)


class Coins(Object):
    ''' Many kinds of coins with certain exchange rates.
        When picked up the disappear and value is converted to shillings'''

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc",
                        "_longdesc", "_value"]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._multiplier = 1  # currency exchange regenerate
        # Copper=1, silver=20, electrum=50, gold=100, platinum=127.

        return(None)


class Ring(Equippable):
    ''' Rings can be equipped '''
    def __init__(self, objId=0):
        super().__init__(objId)
        self.equippedSlotName = '_equippedRing'  # see Character Class
        return(None)


class Necklace(Equippable):
    ''' Neclaces are rings for the neck '''
    def __init__(self, objId=0):
        super().__init__(objId)
        self._dodgeBonus = 0       # Percent - Extra chance of not being hit
        self._ac = 0               # Each point is 5% damage reduction
        self.equippedSlotName = '_equippedNecklace'  # see Character Class
        return(None)

    def getAc(self):
        return(self._ac)

    def getDodgeBonus(self):
        return(self._dodgeBonus)


class Treasure(Object):
    ''' Treasure has value, but is otherwise useless '''
    def __init__(self, objId=0):
        super().__init__(objId)
        return(None)


def getObjectFactoryTypes():
    objTypeList = ['object', 'portal', 'door', 'armor', 'weapon', 'shield',
                   'container', 'key', 'card', 'scroll', 'potion', 'staff',
                   'teleport', 'coins', 'ring', 'necklace', 'treasure']
    return(objTypeList)


def ObjectFactory(objType, id=0):       # noqa: C901
    ''' Factory method to return the correct object, depending on the type '''
    obj = None

    if objType.lower() == "portal":
        obj = Portal(id)
    elif objType.lower() == "door":
        obj = Door(id)
    elif objType.lower() == "armor":
        obj = Armor(id)
    elif objType.lower() == "weapon":
        obj = Weapon(id)
    elif objType.lower() == "shield":
        obj = Shield(id)
    elif objType.lower() == "container":
        obj = Container(id)
    elif objType.lower() == "key":
        obj = Key(id)
    elif objType.lower() == "card":
        obj = Card(id)
    elif objType.lower() == "scroll":
        obj = Scroll(id)
    elif objType.lower() == "potion":
        obj = Potion(id)
    elif objType.lower() == "staff":
        obj = Staff(id)
    elif objType.lower() == "teleport":
        obj = Teleport(id)
    elif objType.lower() == "coins":
        obj = Coins(id)
    elif objType.lower() == "ring":
        obj = Ring(id)
    elif objType.lower() == "necklace":
        obj = Necklace(id)
    elif objType.lower() == "treasure":
        obj = Treasure(id)

    try:
        obj.getId()
    except AttributeError:
        logging.error("ObjectFactory: Could not obtain id for newly" +
                      "instanciated " + objType + " object")
    return(obj)
