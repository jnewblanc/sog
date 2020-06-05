""" Object Class """  # noqa

import bisect
from datetime import datetime
import pprint
import random
import re

from common.attributes import AttributeHelper
from common.general import logger
from common.inventory import Inventory
from common.item import Item
from magic import getSpellChant, Spell

# create obj staff in chest in 3001,ty=magdevice,magic=true,spell=3,
#    value=1000,charges=2


class Object(Item):
    """ object class """

    _instanceDebug = False

    _fileextension = ".json"

    # integer attributes
    intAttributes = ["_weight", "_value"]
    # boolean attributes
    boolAttributes = ["_carry", "_hidden", "_invisible", "_magic", "_permanent"]
    strAttributes = ["_name", "_article", "_singledesc", "_pluraldesc", "_longdesc"]
    listAttributes = ["_classesAllowed", "_alignmentsAllowed", "_gendersAllowed"]
    boolAttributes = [
        "_carry",
        "_hidden",
        "_invisible",
        "_magic",
        "_permanent",
    ]
    strAttributes = [
        "_name",
        "_article",
        "_singledesc",
        "_pluraldesc",
        "_longdesc",
    ]
    listAttributes = [
        "_classesAllowed",
        "_alignmentsAllowed",
        "_gendersAllowed",
    ]
    # obsolete attributes (to be removed)
    obsoleteAttributes = [
        "",
        "_correspondingRoomNum",
        "_classAllowed",
        "_AC",
        "_alignmentAllowed",
        "_genderAllowed",
        "_isMetal",
        "_equippable",
        "_equipable",
        "_usable",
        "equippedSlotName",
        "damageReduction",
        "_multiplier",
        "_depletable",
    ]

    attributesThatShouldntBeSaved = [
        "_instanceDebug",
        "self._persistThroughOneRoomLoad",
    ]

    wizardAttributes = [
        "_name",
        "_article",
        "_singledesc",
        "_pluraldesc",
        "_longdesc",
        "_weight",
        "_value",
    ]

    validSkills = ["_slash", "_bludgeon", "_pierce", "_magic", "_dodge"]

    attributeInfo = {
        "_ac": "the amount of damage this prevents - Range is 0 (none) to 10.",
        "_article": "the article of speech.  For example: a, an, some.",
        "_correspondingDoorId": "The id of the corresponding door i.e. Door/5",
        "_dodgeBonus": "increases chance that player is not hit when attacked",
        "_spell": "the spell that is cast when using this item.",
        "_hasMetal": "metal can't be used by some classes.",
        "_lockId": "The id of the lock used to connects a key with a lock",
        "_longdesc": "full description when item is examined.",
        "_maxCharges": "the number of times that item can be used when full.",
        "_maxAmount": "the maximum number of coins in this batch.",
        "_maximumDamage": "maximum amount of damage inflicted.  Range 0-80.",
        "_minimumDamage": "minimim amount of damage inflicted.  Range 0-50.",
        "_name": "single word that you use when interacting with item",
        "_pluraldesc": "the description for two or more of these.",
        "_singledesc": "the description for one of these, minus the article.",
        "_persistThroughOneRoomLoad": "don't remove during next room load.",
        "_spell": "the spell that is cast when using this item.",
        "_toHitBonus": "Increase the chance of hitting target.  0 = normal",
        "_toWhere": "The room that this item takes you to i.e. 35 or Shop/30",
        "_value": "the base amount used when calculating the sale value.",
        "_worksInRoomId": "The id of the room where this item works",
        "_weight": "how much the item weighs.  Range 0-80 lbs.",
    }

    def __init__(self, objId=0):
        self.objId = objId
        self._article = "a"
        self._longdesc = ""
        self._name = ""
        self._singledesc = ""
        self._pluraldesc = ""

        self._carry = True
        self._cursed = False
        self._enchanted = False  # typially, enchanting is done by players
        self._hidden = False
        self._invisible = False
        self._magic = False
        self._permanent = False

        self._value = 1
        self._weight = 1

        self._alignmentsAllowed = []
        self._classesAllowed = []
        self._gendersAllowed = []
        self._minLevelAllowed = 0
        self._maxLevelAllowed = 100

        self._instanceDebug = Object._instanceDebug
        self._isObject = True

        if self._instanceDebug:
            logger.debug("Object init called for " + str(self.getId()))
        return None

    def __del__(self):
        if self._instanceDebug:
            logger.debug("Object destructor called for " + str(self.getId()))

    def describe(self, count=1, article="none"):
        if count > 1:
            return count + " " + self._pluraldesc
        if article == "none":
            article = self._article + " "
        elif article != "":
            article += " "
        return article + self._singledesc

    def debug(self):
        return pprint.pformat(vars(self))

    def toggleInstanceDebug(self):
        self._instanceDebug = not self._instanceDebug

    def getInstanceDebug(self):
        return self._instanceDebug

    def setInstanceDebug(self, val):
        self._instanceDebug = bool(val)

    def isValid(self):
        for att in ["_name", "_article", "_singledesc", "_longdesc"]:
            if getattr(self, att) == "":
                return False
        return True

    def examine(self):
        msg = self._longdesc
        if hasattr(self, "_toll"):
            if self.hasToll:
                msg += "  It has a toll."
        return msg

    def identify(self):
        ROW_FORMAT = "{0:9}: {1:<30}\n"
        buf = ""
        for attName in vars(self):
            attValue = getattr(self, attName)
            buf += ROW_FORMAT.format(attName, str(attValue))
        return buf

    def fixAttributes(self):
        """ Sometimes we change attributes, and need to fix them in rooms
            that are saved.  This method lets us do that.  Typically this
            involves casting types or removing obsolete vars, but we could
            also use this for copying values from one attribute to another """

        try:
            self._hasMetal = self.isMetal
        except (AttributeError, TypeError):
            pass

        AttributeHelper.fixAttributes(self)
        return True

    def adjustPrice(self, price):
        """ adjust price based on object attributes """
        return price

    def getAc(self):
        """ This is meant to be overridden if needed """
        return 0

    def getArticle(self):
        return self._article

    def getDodgeBonus(self):
        """ This is meant to be overridden if needed """
        return 0

    def getId(self):
        return self.objId

    def getName(self):
        return self._name

    def getPlural(self):
        return self._pluraldesc

    def getSingular(self):
        return self._singledesc

    def getType(self):
        return self.__class__.__name__

    def getValue(self):
        value = self._value
        if self.isCursed():
            value = 6
        return max(0, value)

    def getWeight(self):
        return max(0, self._weight)

    def isCarryable(self):
        return self._carry

    def isCursed(self):
        return self._cursed

    def isHidden(self):
        return self._hidden

    def isInvisible(self):
        return self._invisible

    def isPermanent(self):
        return self._permanent

    def isMagic(self):
        return self._magic

    def limitationsAreSatisfied(self, charObj):
        """ Return True if an items limitations are met """
        if self._classesAllowed and charObj.getClassName() not in self._classesAllowed:
            charObj.client.spoolOut(
                charObj.getClassName().capitalize() + "s are not permitted.\n"
            )
            return False
        if (
            self._alignmentsAllowed
            and charObj.getAlignment() not in self._alignmentsAllowed
        ):
            charObj.client.spoolOut(
                "Folks regarded to be " + charObj.getAlignment() + " are not allowed.\n"
            )
            return False
        if self._gendersAllowed and charObj.getGender() not in self._gendersAllowed:
            charObj.client.spoolOut("You have the wrong parts.\n")
            return False
        if not charObj.getLevel() >= self._minLevelAllowed:
            charObj.client.spoolOut("You are not experienced enough.\n")
            return False
        if not charObj.getLevel() <= self._maxLevelAllowed:
            charObj.client.spoolOut("You are over experienced.\n")
            return False
        return True

    def persistsThroughOneRoomLoad(self):
        if hasattr(self, "_persistThroughOneRoomLoad"):
            return self._persistThroughOneRoomLoad
        return False

    def postLoad(self):
        # When a player dies, their inventory is dropped and made "temporarily
        # permanent", meaning that the permanancy is removed after the next
        # load of the object or room.
        if self.persistsThroughOneRoomLoad():
            self.setPersistThroughOneRoomLoad(False)

    def setName(self, name):
        self._name = str(name)

    def setPermanent(self, val=True):
        self._permanent = val

    def setPersistThroughOneRoomLoad(self, val=True):
        self._persistThroughOneRoomLoad = val


class Exhaustible(Object):
    """ superclass of objects that have a limited lifespan """

    wizardAttributes = [
        "_name",
        "_article",
        "_singledesc",
        "_pluraldesc",
        "_longdesc",
        "_maxCharges",
        "_weight",
        "_value",
    ]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._maxCharges = 100  # max number of charges (constant)
        self._charges = 100  # number of charges remaining (counter)
        self._timesRepaired = 0  # number of times repaired (counter)
        self._cooldown = 0  # Time between uses (in seconds)
        self._broken = False
        self._breakable = True
        self._depleatable = True
        self._lastUse = None

    def adjustPrice(self, price):
        """ adjust price based on percentage of charges remaining"""
        price *= self.percentOfChargesRemaining() / 100
        return int(price)

    def canBeRepaired(self):
        """ Return True if an item can be repaired """
        if self._broken or self._charges == 0:
            return False  # broken items can not be repaired
        if self._maxCharges > 10 and self.percentOfChargesRemaining() > 20:
            return False  # 20%+ charged items can be repaired
        elif self._maxCharges <= 10 and self._charges > 1:
            return False  # Small items need to be on last charge
        return True

    def decrementChargeCounter(self, num=1):
        if self._depleatable:
            self._charges -= num
        if self._charges <= 0:
            if self._breakable:
                self._broken = True

    def getCharges(self):
        return self._charges

    def getLastUse(self):
        return self._lastUse

    def getMaxCharges(self):
        return self._maxCharges

    def isBroken(self):
        return self._broken

    def isCool(self):
        """ Return True if object cooldown is complete """
        if self._cooldown == 0:
            return True  # No cooldown is required
        if (self._lastUse - datetime.now()).total_seconds() > self._cooldown:
            return True
        return False

    def isDepleated(self):
        if self._charges <= 0:
            return True
        return False

    def isUsable(self):
        if not self.isBroken() and not self.isDepleated():
            return True
        return False

    def percentOfChargesRemaining(self):
        return self._charges * 100 / self._maxCharges

    def repair(self):
        """ add charges back onto item
            The first time an item is repaired, it restores 80% of max charges.
            Each additional repair restores 10% fewer charges, meaning that.
            there are diminishing returns """
        if not self.canBeRepaired():
            return False
        newChargePercentage = 0.8  # 80% - amount of charges added back
        reduceBy = 0.1 * self._timesRepaired  # reduce % for each repair
        newChargePercentage -= reduceBy
        self._charges = int(self._maxCharges * newChargePercentage)
        self._timesRepaired += 1

    def setCharges(self, num):
        self._charges = int(num)

    def setLastUse(self):
        self._lastUse = datetime.now()

    def setMaxCharges(self, num):
        self._maxCharges = int(num)


class Equippable(Object):
    """ superClass for objects that are wearable or wieldable
        These objects have an _equippedSlotName that corresponds to the
        character slots """

    def __init__(self, objId=0):
        super().__init__(objId)
        self._equippedSlotName = ""

    def setEquippedSlotName(self, slotStr):
        self._equippedSlotName = str(slotStr)

    def getEquippedSlotName(self):
        return self._equippedSlotName

    def isEquippable(self):
        return True

    def isUsable(self):
        return True


class MagicalDevice(Exhaustible):
    """ SuperClass for magic staffs, potions, and similar spell-casting
        devices.  Unlike casting a spell from memory, there are no int
        requirements and no spell points required to activate spells from
        these items """

    wizardAttributes = [
        "_name",
        "_article",
        "_singledesc",
        "_pluraldesc",
        "_longdesc",
        "_spell",
        "_weight",
        "_value",
    ]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._spell = ""
        # Spell number, range 1..17. 1:vigor, 2:heal, 3:fireball, 4:lightning,
        # 5:hurt, 6:curepoison, 7:disintegrate, 8:befuddle, 9:teleport,
        # 10:wish, 11:passdoor, 12:enchant, 13:bless, 14:protection, 15:curse,
        # 16:poison, 17:intoxicate.
        self._magicLvlRequired = 0
        self._magic = True
        return None

    def isMagicItem(self):
        return True

    def getSpellName(self):
        return self._spell

    def cast(self, charObj, targetObj):
        """ cast a spell using a device """
        if self.getCharges() <= 0:
            charObj.client.spoolOut("This item has no charges left\n")
            return False
        if self.getCharges() == 1:
            if self.getType() == "Scroll":
                charObj.client.spoolOut(
                    self.describe(article="The") + " disintegrates\n"
                )
            else:
                charObj.client.spoolOut(self.describe(article="The") + " fizzles\n")

        spellName = self.getSpellName()
        # With devices, spellChant is not required, so we get it and pass it in
        spellChant = getSpellChant(spellName)

        # create the spell object, which determines if it succeeds
        spellObj = Spell(
            charObj,
            targetObj,
            spellName,
            chant=spellChant,
            requiresmana=False,
            useSelfCriteria=False,
        )

        # Apply effects of spell
        if spellObj.cast(charObj.getRoom()):
            pass
        else:
            charObj.client.spoolOut(spellObj.getFailedReason() + "\n")

        self.decrementChargeCounter()

        return None


class Closable(Object):
    """ superclass of objects that can be opened and closed """

    def __init__(self, objId=0):
        super().__init__(objId)
        self._closed = False
        self._locked = False
        self._poison = False  # when trapped, this flag inflicts poison
        self._spring = True  # automatically close if nobody is in the room
        self._locklevel = 0  # 0=no lock, -1=unpickable, 1=minor lock
        self._traplevel = 0  # 0=no trap, 1=minor trap
        self._lockId = 0  # keys matching this lockId will open it
        self._toll = 0  # 0=no toll, amount to deduct to open
        self._permanent = True
        return None

    def fixAttributes(self):
        attName = "_spring"
        try:
            newVal = bool(getattr(self, attName, False))
        except ValueError:
            newVal = False
        setattr(self, attName, newVal)

        try:
            self._depletable = self._depleatable
        except (AttributeError, TypeError):
            pass

        AttributeHelper.fixAttributes(self)
        return True

    def getLockId(self):
        return self._lockId

    def getLockLevel(self):
        return self._locklevel

    def getTrapLevel(self):
        return self._traplevel

    def isSmashable(self, charObj):
        if self.isClosed():
            # Time check - can only smash every 15 seconds
            if charObj.secsSinceLastAttack() < 15:
                return False
            return True
        return False

    def isPickable(self, charObj):
        if self.isClosed() and self.isLocked():
            # Time check - can only smash every 15 seconds
            if charObj.secsSinceLastAttack() < 15:
                return False
            return True
        return False

    def trapIsPoisoned(self):
        return self._poison

    def isOpenable(self, charObj):
        if self.isOpen():
            return False
        if self.isLocked():
            return False
        return True

    def isClosable(self, charObj):
        if self.isClosed():
            return False
        return True

    def isLockable(self):
        if self.isClosed() and self.isUnlocked() and self.getLockLevel() > 0:
            return True
        return False

    def isUnlockable(self):
        if self.isClosed() and self.isLocked() and self.getLockLevel() > 0:
            return True
        return False

    def isTrapped(self):
        if self._traplevel > 0:
            return True
        return False

    def hasToll(self):
        if self._toll > 0:
            return True
        return False

    def getToll(self):
        return self._toll

    def hasSpring(self):
        return self._spring

    def isClosed(self):
        return self._closed

    def isOpen(self):
        return not (self.isClosed())

    def isLocked(self):
        return self._locked

    def isUnlocked(self):
        return not (self.isLocked())

    def lock(self):
        self._locked = True
        return True

    def unlock(self, keyObj=None):
        if keyObj:
            keyObj.decrementChargeCounter()
        self._locked = False
        return True

    def smash(self, charObj, saveItem=True):
        """ Smash open object - return True if object is opened.
            Smash does not trigger traps, but does cause damage
        """

        if not self.isSmashable():
            return False

        if not charObj.checkCooldown(15):
            return False
        else:
            charObj.setLastAttackDate()

        charHp = charObj.getHitPoints()
        if self.smashSucceds(charObj):
            damage = self.smashDamage(charObj, self.getWeight(), True)
            charObj.client.spoolOut(self.smashTxt(damage, True, charHp))
            charObj.takeDamage(damage)
            self._closed = False
            if saveItem:
                charObj.getRoom().save()
            return True
        else:
            damage = self.smashDamage(charObj, self.getWeight(), False)
            charObj.client.spoolOut(self.smashTxt(damage, False, charHp))
            charObj.takeDamage(damage)
        return False

    def pick(self, charObj, saveItem=True):
        """ Pick lock on an object (also opens it)
           * return True if object is opened
           * Damage is delt only on failed attempts when there are traps
           * Dex and class used in pick calculation
        """
        if not self.isPickable():
            return False

        if self.getLockLevel() <= 0:  # Can't pick these doors
            return False

        if not charObj.checkCooldown(15):
            return False
        else:
            charObj.setLastAttackDate()

        if charObj.picksLock(charObj, self.getLockLevel()):
            self._locked = False
            self._closed = False
            if saveItem:
                charObj.getRoom().save()
            return True
        elif self.getTrapLevel() > 0:
            if not charObj.avoidsTrap(self.getTrapLevel()):
                damage = self.trapDamage(charObj, self.getTrapLevel())

                trapTxt = self.trapTxt(
                    damage, poison=self._poison, currenthealth=charObj.getHitPoints()
                )
                charObj.client.spoolOut(trapTxt)
                charObj.takeDamage(damage)

            if self._poison:
                if random.randint(1, 100) < charObj.getLuck():
                    charObj.setPoisoned()
            return False
        return False

    def open(self, charObj):
        """ Open an object - Returns true if opened """
        if not self.isOpenable(charObj):
            return False

        if self.getTrapLevel() > 0:
            if not charObj.avoidsTrap(self.getTrapLevel()):
                damage = self.trapDamage(charObj, self.getTrapLevel())
                dealPoison = False
                if self.trapIsPoisoned():
                    if not charObj.resistsPoison():
                        charObj.setPoisoned()
                        dealPoison = True
                trapTxt = self.trapTxt(
                    damage, poison=dealPoison, currenthealth=charObj.getHitPoints()
                )
                charObj.client.spoolOut(
                    "{}: Trap hits you for {} hit points.".format(trapTxt, damage)
                )
                charObj.client.spoolOut("\n")
                charObj.takeDamage(damage)
            else:
                pass
                # charObj.client.spoolOut("You avoid the trap!\n")

        self._closed = False

        return True

    def close(self, charObj):
        if not self.isClosable(charObj):
            return False

        self._closed = True
        return True

    def smashSucceds(self, charObj):
        """ Returns True if smash calculations succeed
            * Weight makes it harder to SMASH
            * Strength makes it easier to smash """

        if random.randint(1, 3) == 1:  # Always a 30% chance of success
            return True
        elif (charObj.getStrength() * 10) > self.getWeight():  # stat based
            return True
        return False

    def smashDamage(self, charObj, weight, succeeded):
        """ Returns damage from smash calculations
            * Dexterity and Luck are used to see if damage is reduced
            * Constitution determines how much damage is reduced """

        damage = random.randint(int(weight / 2), (weight * 2))  # 50% - 200%
        damage -= min(weight, charObj.calculateAC() * charObj.getLevel())

        # Random chance, based on luck/dex, to reduce damage
        # Reduction amount based on con
        randLuck = random.randint(1, (30 - charObj.getLuck()))
        if randLuck < charObj.getDexterity():
            damage = int(damage / charObj.getConstitution() * 3)

        if succeeded:
            damage = int(damage * 0.33)  # damage reduced on success

        return max(0, damage)

    def trapDamage(self, charObj, traplevel):
        """ Returns damage from trap calculations """
        damage = random.randint(traplevel, traplevel * 10)
        return max(0, damage)

    def smashTxt(self, damage=0, success=False, currenthealth=-1):
        """ returns the text for the smash """
        buf = ""
        if damage >= currenthealth:  # fatal blow
            buf += "Ouch.  That door was stronger than it looked"
        elif damage <= 30:
            buf += "Pieces of the door cut into you!"
        elif damage >= 30:
            buf += "Ouch!  That's one heavy door"
        return buf

    def trapTxt(self, damage=0, poison=False, currenthealth=-1):  # no
        """ returns the text for the trap """
        buf = ""

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

        if damage >= currenthealth:  # fatal blow
            pos = bisect.bisect_right(fatalDict, (damage,))
            buf += str(fatalDict[pos][1])
        elif poison:
            pos = bisect.bisect_left(poisonDict, (damage,))
            buf += str(poisonDict[pos][1])
        else:
            pos = bisect.bisect_left(normalDict, (damage,))
            buf += str(normalDict[pos][1])

        if buf == "":
            buf = "You are hit by a trap."
        return buf


class Armor(Equippable, Exhaustible):

    wizardAttributes = [
        "_name",
        "_article",
        "_singledesc",
        "_pluraldesc",
        "_longdesc",
        "_ac",
        "_dodgeBonus",
        "_maxCharges",
        "_weight",
        "_value",
        "_hasMetal",
    ]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._dodgeBonus = 0  # Percent - Extra chance of not being hit
        self._ac = 0  # Each point is 5% damage reduction
        self._hasMetal = True
        self._equippedSlotName = "_equippedArmor"  # see Character Class

        return None

    def getAc(self):
        return self._ac

    def getDodgeBonus(self):
        return self._dodgeBonus


class Weapon(Equippable, Exhaustible):
    """ Weapon Object -
        Players have skills in each of the four types of weapon.
        Weapons can be repaired (i.e., have strikesleft increase) at the
        repair shop (room 18) as long as “strikesleft” is more than 0.
        There’s a 50% chance that the repair will be botched if the weapon is
        magical or has MH more than 30.
    """

    wizardAttributes = [
        "_name",
        "_article",
        "_singledesc",
        "_pluraldesc",
        "_longdesc",
        "_minimumDamage",
        "_maximumDamage",
        "_maxCharges",
        "_weight",
        "_value",
    ]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._minimumDamage = 0
        self._maximumDamage = 10
        self._toHitBonus = 0  # Each 1 is a +5% chance to hit
        self._equippedSlotName = "_equippedWeapon"  # see Character Class
        self._damageType = "_bludgeon"

        return None

    def getMinimumDamage(self):
        return max(0, self._minimumDamage)

    def getMaximumDamage(self):
        return max(1, self._maximumDamage)

    def setMinimumDamage(self, num=0):
        self._minimumDamage = int(num)

    def setMaximumDamage(self, num=1):
        self._maximumDamage = int(num)

    def getToHitBonus(self):
        return self._toHitBonus

    def setToHitBonus(self, num=0):
        self._toHitBonus = int(num)

    def setDamageType(self, skill):
        if "_" not in skill:
            skill = "_" + skill
        if skill in self.validSkills:
            self._damageType = skill

    def getDamageType(self):
        skill = self._damageType
        if "_" not in skill:
            skill = "_" + skill
        if skill not in self.validSkills:
            return "_bludgeon"
        return skill


class Shield(Equippable, Exhaustible):

    wizardAttributes = [
        "_name",
        "_article",
        "_singledesc",
        "_pluraldesc",
        "_longdesc",
        "_ac",
        "_dodgeBonus",
        "_maxCharges",
        "_weight",
        "_value",
    ]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._dodgeBonus = 0  # Percent - Extra chance of not being hit
        self._ac = 0  # Each point is 5% damage reduction
        self._equippedSlotName = "_equippedShield"  # see Character Class
        return None

    def getAc(self):
        return self._ac

    def getDodgeBonus(self):
        return self._dodgeBonus


class Portal(Object):

    wizardAttributes = [
        "_name",
        "_article",
        "_singledesc",
        "_pluraldesc",
        "_longdesc",
        "_toWhere",
    ]

    """ Portals are similar to doors, but are one-way and not closable """

    def __init__(self, objId=0):
        super().__init__(objId)
        self._toWhere = ""
        self._toll = 0
        self._carry = False
        self._permanent = True
        return None

    def getToWhere(self):
        return self._toWhere

    def canBeEntered(self, charObj):
        if self.limitationsAreSatisfied(charObj):
            return True
        return False

    def hasToll(self):
        if self._toll > 0:
            return True
        return False

    def getToll(self):
        return self._toll


class Door(Portal, Closable):
    """ Doors are Closables which have a corresponding door who's open/closed
        state is kept in sync """

    wizardAttributes = [
        "_name",
        "_article",
        "_singledesc",
        "_pluraldesc",
        "_longdesc",
        "_toWhere",
        "_correspondingDoorId",
        "_weight",
    ]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._carry = False
        self._permanent = True
        self._spring = 0  # automatically close when room is loaded
        self._magic = 0  # can't be passed through by magic
        self._weight = 50  # weight impacts smashability
        self._correspondingDoorId = ""
        return None

    def canBeEntered(self, charObj):
        if self.isClosed():
            charObj.client.spoolOut(self.describe(article="The") + " is closed.\n")
            return False
        if self.limitationsAreSatisfied(charObj):
            return True
        return False

    def canPassThrough(self):
        if self.isMagic():
            return False
        return True

    def getCorresspondingDoorId(self):
        return self._correspondingDoorId

    def examine(self):
        buf = super().examine()
        if self.isClosed():
            buf += ".  It's closed."
        return buf

    def getSingular(self):
        return self.describe(article="")

    def describe(self, count=1, article="none"):
        if article == "none":
            article = self._article + " "
        elif article != "":
            article += " "

        if self.isClosed():
            return article + "closed " + self._singledesc
        else:
            if article == "a":
                return "an open " + self._singledesc
            else:
                return article + "open " + self._singledesc


class Container(Closable):

    wizardAttributes = ["_name", "_article", "_singledesc", "_pluraldesc", "_longdesc"]

    def __init__(self, objId=0):
        super().__init__(objId)
        Inventory.__init__(self)

        self._closed = False
        self._locklevel = 0  # 0=unpickable, 1=easy-to-pick

        self._trap = 0
        # When the container is opened or unlocked, this determines the trap
        # that might go off. Thieves are better at avoiding traps; the formula
        # to avoid the trap is DEX - random(6) > (CL mod 10), but for thieves
        # their DEX was multiplied by 2 in this equation.

        self._lockId = 0
        self._inventoryTruncSize = 6
        self._permanent = True
        self._containerWeight = 20
        self._closedTxt = "It's closed.  You must open it first"
        self._dontHaveTxt = "You don't have that"
        self._NotThereTxt = "That item isn't in there"
        self._notStrongEnoughTxt = "You aren't strong enough to take that."
        return None

    def postLoad(self):
        self.truncateInventory(self._inventoryTruncSize)

    def examine(self):
        buf = super().examine() + "\n"
        buf += self.describeInventory(
            markerAfter=self._inventoryTruncSize, headerTxt="Contents"
        )
        return buf

    def getContainerWeight(self):
        return self._containerWeight

    def getWeight(self):
        return self.getContainerWeight() + self.getInventoryWeight()

    def deposit(self, charObj, item, saveItem=True):
        """ add an item to the container's inventory """

        if item not in charObj.getInventory():
            charObj.client.spoolOut(self._dontHaveTxt + "\n")
            return False

        if self.isClosed():
            charObj.client.spoolOut(self._closedTxt + "\n")
            return False

        charObj.removeFromInventory(item)
        self.addToInventory(item)
        if len(self.getInventory()) >= self._inventoryTruncSize:
            msg = (
                "Warning - any items in excess of "
                + self._inventoryTruncSize
                + " will be truncated on when you leave the room."
            )
            charObj.client.spoolOut(msg + "\n")
        self._weight = self.getWeight()

        if saveItem:
            charObj.getRoom().save()
        return True

    def withdraw(self, charObj, item, saveItem=True):
        """ remove an item to the container's inventory """
        if item not in self.getInventory():
            charObj.client.spoolOut(self._NotThereTxt + "\n")
            return False

        if self.isClosed():
            charObj.client.spoolOut(self._closedTxt + "\n")
            return False

        if not charObj.canCarryAdditionalWeight(item.getWeight()):
            charObj.client.spoolOut(self._notStrongEnoughTxt + "\n")

        self.removeFromInventory(item)
        charObj.addToInventory(item)
        self._weight = self.getWeight()
        if saveItem:
            charObj.getRoom().save()
        return True


class Key(Exhaustible):

    wizardAttributes = [
        "_name",
        "_article",
        "_singledesc",
        "_pluraldesc",
        "_longdesc",
        "_lockId",
    ]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._lockId = 0  # id=1000 will open any door
        return None

    def getLockId(self):
        return self._lockId


class Scroll(MagicalDevice):
    """ Can study it to see the chant and learn the spell
        Scroll minimums for intelligence and level are -2
        if they are not met, nothing happens and scroll is not ruined """

    def __init__(self, objId=0):
        super().__init__(objId)
        self._maxCharges = 1
        self._charges = 1
        self._value = 10
        self._weight = 1
        return None

    def readScroll(self, charObj, targetObj):
        """ cast the spell
            * scroll disintegrates in calling function """
        # Get the spell object - no chant required for scrolls
        self.cast(charObj, targetObj)
        return None

    def study(self, charObj):
        """ Display the spell chant and add spell to Char's known spells
            * scroll disintegrates in calling function """

        msg = ""
        spellName = self.getSpellName()

        # Get the chant
        spellChant = getSpellChant(spellName)
        msg += self.describe(article="The") + ' reads, "' + spellChant + '"\n'

        # Learn the spell
        if charObj.learnSpell(spellName):
            msg += 'You learn the "' + spellName + '" spell\n'

        return msg


class Potion(MagicalDevice):
    """ Potion """

    def __init__(self, objId=0):
        super().__init__(objId)
        self._usesRemaining = 5
        return None


class Staff(MagicalDevice):
    """ Staff """

    def __init__(self, objId=0):
        super().__init__(objId)
        self._usesRemaining = 5
        return None


class Teleport(MagicalDevice):
    """ The teleport device sends the recipient to exactly one room, and
        perhaps from only room.  These are sometimes used like special keys
        to access special areas like the Thieves’ lair. Usually the departure
        room is set, so it will only work from one room; the player may need
        to work out clues to figure out where a teleportdevice works."""

    wizardAttributes = [
        "_name",
        "_article",
        "_singledesc",
        "_pluraldesc",
        "_longdesc",
        "_worksInRoomId",
        "_toWhere",
        "_weight",
        "_value",
    ]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._departureRoom = 0  # 0=any room
        self._toWhere = ""
        return None


class Coins(Object):
    """ Many kinds of coins with certain exchange rates.
        When picked up the disappear and value is converted to shillings"""

    wizardAttributes = [
        "_name",
        "_article",
        "_singledesc",
        "_pluraldesc",
        "_longdesc",
        "_value",
        "_minAmount",
        "_maxAmount",
    ]

    def __init__(self, objId=0):
        super().__init__(objId)
        self._minAmount = 1
        self._maxAmount = 5
        self._count = 1  # auto-generated number of coins in current batch
        return None

    def describe(self, article=""):
        if self._count > 1:
            return self._count + " " + self._pluraldesc
        return self._article + " " + self._singledesc

    def getTotalValue(self):
        return self._count * self._value


class Ring(Equippable):
    """ Rings can be equipped """

    def __init__(self, objId=0):
        super().__init__(objId)
        self._equippedSlotName = "_equippedRing"  # see Character Class
        return None


class Necklace(Equippable):
    """ Neclaces are rings for the neck """

    def __init__(self, objId=0):
        super().__init__(objId)
        self._slashPercent = 0
        self._bludgeonPercent = 0
        self._piercePercent = 0
        self._magicPercent = 0
        self._dodgePercent = 0
        self._equippedSlotName = "_equippedNecklace"  # see Character Class
        return None

    def getProtectionFromSkill(self, skill):
        """ return the amount of protection that a given skill provides """
        percent = 0
        skill = re.sub("^_", "", skill)  # get rid of leading underbars, if any
        if skill in ["slash", "bludgeon", "pierce", "magic", "dodge"]:
            percent = getattr(self, "_" + skill + "Percent")
        return percent


class Treasure(Object):
    """ Treasure has value, but is otherwise useless """

    def __init__(self, objId=0):
        super().__init__(objId)
        return None


ObjFactoryTypes = [
    "object",
    "portal",
    "door",
    "armor",
    "weapon",
    "shield",
    "container",
    "key",
    "scroll",
    "potion",
    "staff",
    "teleport",
    "coins",
    "ring",
    "necklace",
    "treasure",
]


def isObjectFactoryType(item):
    """ Return True if item is a valid object FacotryType """
    if isinstance(item, str):
        name = item.lower()
    else:
        name = item.getType().lower()
    return name in ObjFactoryTypes


def ObjectFactory(objType, id=0):  # noqa: C901
    """ Factory method to return the correct object, depending on the type """
    obj = None

    if objType.lower() == "object":
        obj = Portal(id)
    elif objType.lower() == "portal":
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
        logger.error(
            "ObjectFactory: Could not obtain id for newly"
            + "instanciated "
            + objType
            + " object"
        )
    return obj
