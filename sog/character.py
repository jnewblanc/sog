''' Character class '''

from datetime import datetime
import inflect
import os
import pprint
import random
import re

from common.attributes import AttributeHelper
from common.editwizard import EditWizard
from common.ioLib import TestIo
from common.inventory import Inventory
from common.general import getNeverDate, differentDay, dLog, secsSinceDate
from common.general import getRandomItemFromList, truncateWithInt
from common.general import logger
from common.paths import DATADIR
from common.storage import Storage
from object import Weapon
from magic import SpellList


class Character(Storage, AttributeHelper, Inventory, EditWizard):
    """ Character class """

    _instanceDebug = False

    attributesThatShouldntBeSaved = \
        ['client', '_instanceDebug', '_currentlyAttacking', '_vulnerable',
         '_secondsUntilNextAttack', '_lastInputDate', '_lastAttackDate',
         '_lastRegenDate', '_spoolOut', '_roomObj']

    # int attributes
    intAttributes = ['_expToNextLevel', '_level', '_maxhp', '_hp',
                     '_maxmana', '_mana',
                     '_statsearnedlastlevel', '_limitedSpellsLeft',
                     '_broadcastLimit', '_slash', '_bludgeon', '_pierce',
                     '_magic', '_dodge', '_coins', '_ac',
                     '_weenykills', '_matchedkills', '_valiantkills',
                     '_epickills', '_playerkills', '_bankBalance',
                     '_taxesPaid', '_bankFeesPaid', '_dodgeBonus']
    # boolean attributes
    boolAttributes = ['_achievedSkillForLevel', '_poisoned', '_plagued',
                      '_evil', '_invisible', '_nonexistent', '_playtester',
                      '_hidden']
    # string attributes
    strAttributes = ['_name']
    # list attributes
    listAttributes = ['_knownSpells', '_doubleUpStatLevels']

    # obsolete attributes (to be removed)
    obsoleteAtt = ['_money', '_heal', '_maxspellpoints', '_spellpoints',
                   '_hitpoints', '_maxhitpoints', 'roomObj']

    attributeInfo = {
    }

    genderDict = {
        0: {
            'name': 'male',
            'pronoun': 'him',
            'possisivepronoun': 'his',
            'bonusStats': ['strength', 'constitution']},
        1: {
            'name': 'female',
            'pronoun': 'her',
            'possisivepronoun': 'her',
            'bonusStats': ['charisma', 'intelligence']},
        2: {
            'name': 'fluid',
            'pronoun': 'them',
            'possisivepronoun': 'their',
            'bonusStats': ['piety', 'dexterity']}
        }

    classDict = {
        0: {
            'name': 'fighter',
            'desc': 'Master of combat, skilled in weapondry',
            'pros': 'Attack/Defense Bonuses',
            'cons': 'Poor Magic Use',
            'doubleUpStatLevels': [2, 3, 7],
            'bonusStats': ['strength', 'constitution'],
            'penaltyStats': ['intelligence', 'piety'],
            'baseDamage': 2,
            'baseHealth': 18,
            'baseMagic': 2,
            'identifyLevel': 10
            },
        1: {
            'name': 'rogue',
            'desc': 'A scoundrel fluent in stealth and trickery',
            'pros': 'Hiding/Defense Bonuses',
            'cons': 'Poor Attack',
            'doubleUpStatLevels': [3, 7, 9],
            'bonusStats': ['dexterity', 'charisma'],
            'penaltyStats': ['strength', 'piety'],
            'baseDamage': 1,
            'baseHealth': 14,
            'baseMagic': 6,
            'identifyLevel': 8
            },
        2: {
            'name': 'mage',
            'desc': 'A vulnerable and powerful scholarly spellcaster',
            'pros': 'Spell abilities and Bonuses',
            'cons': 'Can not use metal armor',
            'doubleUpStatLevels': [2, 6, 8],
            'bonusStats': ['intelligence', 'intelligence'],
            'penaltyStats': ['strength', 'strength'],
            'baseDamage': 0,
            'baseHealth': 6,
            'baseMagic': 14,
            'identifyLevel': 5
            },
        3: {
            'name': 'cleric',
            'desc': 'Healer and servant of higher powers',
            'pros': 'Healing Abilities and Bonuses + Undead Turning',
            'cons': 'Can not use bladed weapons',
            'doubleUpStatLevels': [4, 6, 8],
            'bonusStats': ['piety', 'piety'],
            'penaltyStats': ['strength', 'dexterity'],
            'baseDamage': 0,
            'baseHealth': 7,
            'baseMagic': 13,
            'identifyLevel': 8,
            },
        4: {
            'name': 'ranger',
            'desc': 'A rough and wild hunter ',
            'pros': 'Minor Defense Bonuses & Spell Abilities',
            'cons': 'Poor Charisma',
            'doubleUpStatLevels': [2, 4, 9],
            'bonusStats': ['dexterity', 'intelligence'],
            'penaltyStats': ['charisma', 'charisma'],
            'baseDamage': 1,
            'baseHealth': 12,
            'baseMagic': 8,
            'identifyLevel': 7,
            },
        5: {
            'name': 'paladin',
            'desc': 'A righteous fighter who hunts the forces of evil',
            'pros': 'Minor Attack Bonuses, Healing, and Undead Turning',
            'cons': 'Must be lawful, can not steal',
            'doubleUpStatLevels': [3, 8, 9],
            'bonusStats': ['charisma', 'piety'],
            'penaltyStats': ['intelligence', 'constitution'],
            'baseDamage': 2,
            'baseHealth': 10,
            'baseMagic': 10,
            'identifyLevel': 9
            }
        }  # end classDict

    classList = ['fighter', 'rogue', 'mage', 'cleric', 'ranger', 'paladin']
    genderList = ['male', 'female', 'fluid']
    alignmentList = ['lawful', 'neutral', 'chaotic']
    statList = ['strength', 'dexterity', 'intelligence', 'piety',
                'charisma', 'constitution', 'luck']
    skillDict = {
        '_slash': 'swords and axes come easily to you',
        '_bludgeon': 'hammers and maces are an extention of your arms',
        '_pierce': 'you gravitate toward daggers and spears',
        '_magic': 'an inner confidence that enhances spells',
        '_dodge': 'being quick on your feet helps avoid blows'}

    def __init__(self, client=None, acctName=''):
        self.client = client
        self._acctName = acctName

        super().__init__()
        Storage.__init__(self)
        Inventory.__init__(self)
        self.setName('')

        if self.client:
            self._spoolOut = self.client.spoolOut
        else:
            testIo = TestIo()
            self._spoolOut = testIo.spoolOut

        self._dm = False

        self.setPromptSize('full')

        # set base status
        for onestat in self.statList:
            setattr(self, onestat, 8)

        self._expToNextLevel = (2 ** 9)
        self._level = 1
        self._maxhp = 10
        self._maxmana = 10
        self._hp = 10
        self._mana = 10
        self._statsearnedlastlevel = 0
        self._maxitems = 12

        self._classname = 'fighter'

        # skills are percentages, one of which can go up each level
        self.initializeStats()
        self._achievedSkillForLevel = False

        # Daily limits
        #  Some spells, collectively, can only be cast X times per calendar day
        #    need a way to reset this
        self._limitedSpellsLeft = 5
        self._broadcastLimit = 5

        # guilds offer benefits - must pay daily dues
        # Need way to collect dues or to boot player out of guild
        self._guild = ''
        self._guildJoinDate = getNeverDate()
        self._dailyGuildDues = ''
        self._totalGuildPayments = ''
        self._lastGuildPayment = getNeverDate()
        self._taxesPaid = 0
        self._bankFeesPaid = 0

        # if piety gets too low, neutral creatures will attack on sight and
        # shop keepers will not sell to you.

        self._poisoned = False  # slowly lose hp

        self._plagued = False  # hp will not regen & skill bonuses are ignored

        # hidden stats
        self._evil = False
        self._invisible = False
        self._nonexistent = False
        self._playtester = False

        self._bankBalance = 0
        self._coins = 100
        self._knownSpells = []
        self._doubleUpStatLevels = []

        self._creationDate = datetime.now()
        self._lastLogoutDate = getNeverDate()
        self._lastPoisonDate = getNeverDate()

        self._playtester = False

        self._ac = 0             # Each point is 5% damage reduction
        self._dodgeBonus = 0     # Percent - Extra chance of not being hit

        self._weenykills = 0     # kills below current level
        self._matchedkills = 0   # kills at current level
        self._valiantkills = 0   # kills above current level
        self._epickills = 0      # special kills
        self._playerkills = 0    # player kills
        self._turnkills = 0      # kills from turning

        self.resetTmpStats()
        self.resetDailyStats()

        self._instanceDebug = Character._instanceDebug

        return(None)

    def __str__(self):
        return("Character " + self.getName() + " of account " +
               str(self._acctName))

    def debug(self):
        return(pprint.pformat(vars(self)))

    def toggleInstanceDebug(self):
        self._instanceDebug = not self._instanceDebug

    def setInstanceDebug(self, val):
        self._instanceDebug = bool(val)

    def getInstanceDebug(self):
        return(self._instanceDebug)

    def initializeStats(self, num=0):
        for onestat in self.skillDict.keys():
            setattr(self, onestat, 0)

    def login(self):
        ''' Login to game with a particular character
            * Return True if character was created or loaded
        '''
        buf = ''
        if self.selectCharacter():
            pStr = __class__.__name__ + ".login: "
            charName = str(self.getName())
            dLog('Attemping login for ' + charName, self._instanceDebug)
            # Import existing character
            if self.load(logStr=__class__.__name__):
                dLog(pStr + 'Character ' + charName + ' loaded for ' +
                     self._acctName, self._instanceDebug)
            else:
                dLog(pStr + 'Character ' + charName +
                     ' could not be loaded for ' + self._acctName +
                     " - New character?", self._instanceDebug)
                if self.create(charName):
                    dLog(pStr + 'Character ' + charName + ' created for ' +
                         self._acctName, self._instanceDebug)
                    self.client.acctObj.addCharacterToAccount(charName)
                    self.client.acctObj.save()
                else:
                    buf = ('Character ' + charName +
                           ' could not be created for ' + self._acctName)
                    dLog(pStr + buf, self._instanceDebug)
                    self._spoolOut(buf + '\n')
                    return(False)
            if not self.isValid():
                buf = 'Character ' + charName + ' is not valid'
                dLog(pStr + buf, self._instanceDebug)
                self._spoolOut(buf + '\n')
                return(False)
        else:
            return(False)

        self.setLoginDate()
        self.client.charObj = self

        self._spoolOut(buf)
        return(True)

    def create(self, charName, promptFlag=True):
        ''' create a new character
            * Call promptForNewCharacter to prompt user for customization
            * return True if character is _creature
            * return False and scrub character if character was not created
            '''
        self.__init__(self.client, self.client.acctObj.getEmail())
        self.setName(charName)
        self.setPromptSize('full')
        self.setLoginDate()

        # customize
        if self.promptForNewCharacter(promptFlag):
            if not self.isValid():
                return(False)

            self.customizeStats()
            self.randomlyIncrementStat(12)

            # set starting points for changing stats that depend on other stats
            self.setHitPoints(self.getMaxHP())
            self.setMana(self.getMaxMana())

            self.resetTmpStats()
        else:
            self.__init__(self.client, self.client.acctObj.getEmail())
            return(False)

        self.equipFist()

        if self.isValid():
            self.save()
        else:
            self.__init__(self.client, self.client.acctObj.getEmail())
            return(False)
        return(True)

    def fixAttributes(self):
        ''' Sometimes we change attributes, and need to fix them in rooms
            that are saved.  This method lets us do that.  First we call
            the generic superClass fixAttributes to fix the types and remove
            obsolete vars.  Here, we can also add class specific logic for
            copying values from one attribute to another, etc '''

        try:
            self._maxmana = self._maxspellpoints
        except (AttributeError, TypeError):
            pass
        try:
            self._mana = self._spellpoints
        except (AttributeError, TypeError):
            pass
        try:
            self._hp = self._hitpoints
        except (AttributeError, TypeError):
            pass
        try:
            self._maxhp = self._maxhitpoints
        except (AttributeError, TypeError):
            pass

        AttributeHelper.fixAttributes(self)

    def postLoad(self):
        self.truncateInventory(12)
        self.resetTmpStats()
        self.equipFist()

    def resetTmpStats(self):
        ''' Resets some stats that are not meant to be static/peristant
            This is typically used when re-entering the game '''
        self._equippedWeapon = None
        self._equippedArmor = None
        self._equippedShield = None
        self._equippedRing = None
        self._equippedNecklace = None

        self._follow = ""
        self._lastCommand = ''

        self.setAc()
        self.setMaxWeightForCharacter()

        self._hidden = False
        self._blessed = False
        self._drunk = False

        self._roomObj = None

        self._attackTargets = []

        self._lastInputDate = getNeverDate()
        self._lastAttackDate = getNeverDate()
        self._lastAttackCmd = 'attack'
        self._lastRegenDate = getNeverDate()
        self._currentlyAttacking = None
        self._secondsUntilNextAttack = 0
        self._vulnerable = False

        # Check if it's a different day
        if differentDay(datetime.now(), self._lastLogoutDate):
            self.resetDailyStats()

    def resetDailyStats(self):
        ''' Reset daily stats - typically called during login, if it's a
            different calendar day from last login and/or at midnight reset '''
        self._limitedSpellsLeft = 5
        self._broadcastLimit = 5

    def isValid(self):
        ''' Returns true if the class instance was created properly '''
        # ToDo: determine if a better check is required
        if hasattr(self, 'client'):
            return(True)
        if hasattr(self, '_name'):
            return(True)
        if hasattr(self, '_classname'):
            return(True)
        if hasattr(self, '_gender'):
            return(True)
        if hasattr(self, '_align'):
            return(True)
        return(False)

    def getDesc(self, showAlignment=True):
        ''' Returns a string that describes the in-game appearance '''
        buf = (self.getName() + ' is a ' + self.condition() + ', level ' +
               str(self.getLevel()) + " " + self.getGender() + " " +
               self.getClassName())
        if showAlignment:
            if self._alignment == 'lawful':
                buf += " who tends to follow the rules"
            elif self._alignment == 'chaotic':
                buf += " who lives life on the edge"
        buf += ".\n"
        return(buf)

    def examine(self):
        ''' This is what other's see if they look at you '''
        buf = self.getDesc(showAlignment=False)
        return(buf)

    def getInfo(self, dm=0):
        '''Display character'''
        # ROW_FORMAT = "{0:14}: {1:<30}\n"
        buf = self.getDesc()
        buf += self.healthInfo()
        buf += self.equippedInfo()
        buf += self.financialInfo()
        buf += self.expInfo()
        buf += self.statsInfo()
        buf += self.skillsInfo()
        buf += self.guildInfo()
        buf += self.inventoryInfo()
        return(buf)

    def inventoryInfo(self):
        buf = self.describeInventory(markerAfter=12)
        return(buf)

    def financialInfo(self):
        buf = ("You have " + str(self.getCoins()) + " shillings in " +
               "your purse.\n")
        return(buf)

    def statsInfo(self):
        ''' Display character stats'''
        buf = "Stats:\n"
        ROW_FORMAT = "  {0:14}: {1:<30}\n"
        for onestat in self.statList:
            buf += ROW_FORMAT.format(onestat, str(getattr(self, onestat)))
        return(buf)

    def skillsInfo(self):
        ''' Display character skills'''
        buf = ("Skills:")
        ROW_FORMAT = "  {0:14}: {1:<30}\n"
        if self.hasAchievedSkillForLevel():
            buf += ('  Proficiency earned for level ' + str(self.getLevel()) +
                    '\n')
        else:
            if self.getPromptSize() == 'full':
                buf += ('  To gain a proficiency at this level, you ' +
                        'must engage with higher level creatures\n')
            else:
                buf += ('  Proficiency not earned for level ' +
                        str(self.getLevel()) + '\n')

        for onestat in self.skillDict.keys():
            buf += ROW_FORMAT.format(onestat.rstrip('_'),
                                     str(getattr(self, onestat)) + '%')
        return(buf)

    def healthInfo(self):
        hitTxt = str(self.getHitPoints()) + "/" + str(self.getMaxHP())
        magTxt = str(self.getMana()) + "/" + str(self._maxmana)
        buf = ("You have " + hitTxt + " health pts and " +
               magTxt + " magic pts.")
        if self.isDm():
            buf += "  Your armor class is " + str(self._ac)
        buf += '\n'

        if self.isPoisoned():
            buf += 'You are slowly dying from poison.\n'

        if self.isPlagued():
            buf += 'You are infected with the plague.\n'

        return(buf)

    def expInfo(self):
        ROW_FORMAT = "  {0:14}: {1:<30}\n"
        buf = ("Experience:\n")
        buf += ROW_FORMAT.format("Level", str(self.getLevel()))
        if self.getPromptSize() == 'full':
            buf += ('  ' + str(max(0, self._expToNextLevel)) +
                    " experience needed to get to level " +
                    str(int(self.getLevel()) + 1) + '\n')
        else:
            buf += " - " + str(max(0, self._expToNextLevel)) + " to go."
        return(buf)

    def guildInfo(self):
        buf = ''
        if self._guild != '':
            buf = ('Guilds:\n' +
                   '  You are a member of the ' + self._guild + 'guild.\n' +
                   '  You joined on ' +
                   self._guildJoinDate.strftime("%Y/%m/%d") +
                   '  You have paid ' + self._totalGuildPayments +
                   ' to your guild and your daily dues are ' +
                   self._dailyGuildDues + '\n')
        return(buf)

    def equippedInfo(self, prefix="You are"):
        buf = ''

        buf += (prefix + " carrying " +
                str(self.getInventoryWeight()) + "/" +
                str(self.getInventoryMaxWeight()) + " lbs of items.\n")

        equippedList = []

        if self.getEquippedArmor():
            equippedList.append('wearing ' +
                                self.getEquippedArmor().describe())

        if self.getEquippedWeapon():
            if not self.isAttackingWithFist():
                equippedList.append('weilding ' +
                                    self.getEquippedWeapon().describe())

        if self.getEquippedShield():
            equippedList.append('holding ' +
                                self.getEquippedShield().describe())

        if self.getEquippedRing():
            equippedList.append('sporting ' +
                                self.getEquippedRing().describe() +
                                ' on your finger')

        if self.getEquippedNecklace():
            equippedList.append('presenting ' +
                                self.getEquippedNecklace().describe() +
                                ' around your neck')

        if len(equippedList) > 0:
            inf = inflect.engine()            # instanciate a inflect engine
            buf += prefix + " " + inf.join(equippedList) + ".\n"

        return(buf)

    def selectCharacter(self):
        ''' prompt user to select a character to load
            store resulting character name into self._name
            return True/False'''
        logPrefix = __class__.__name__ + " selectCharacter: "
        characterList = self.client.acctObj.getCharacterList()
        numOfCharacters = len(characterList)
        openCharacterSlots = (self.client.acctObj.getMaxNumOfCharacters() -
                              numOfCharacters)
        self.setName('')

        while True:
            prompt = "Select character to play : \n"
            if openCharacterSlots > 0:
                prompt += "  (0) Create new character\n"
            if numOfCharacters > 0:
                prompt += self.client.acctObj.showCharacterList(indent='  ')
            prompt += 'Enter number or press [enter] to exit: '
            inNum = self.client.promptForNumberInput(prompt, numOfCharacters)
            if inNum == -1:    # undisclosed way to exit with False Value
                return(False)
            elif inNum == 0:   # Prompt for a new character name
                minNameLength = 3
                maxNameLength = 40
                prompt = (
                          "To create a character, you will need to provide " +
                          "your character's name, class, gender, and " +
                          "alignment\n")
                prompt += 'Please enter your character\'s name: '
                errmsg = ("  You may only use alphanumerics, spaces, " +
                          "underbars, and hyphens.\n  The first letter must" +
                          " be alphabetic and the name must be between " +
                          str(minNameLength) + ' and ' + str(maxNameLength) +
                          ' characters long.')
                charName = self.client.promptForInput(prompt, r'^[A-Za-z][A-Za-z0-9_\- ]{2,}$', errmsg)  # noqa: E501
                if charName == "":
                    dLog(logPrefix + "name is blank", self._instanceDebug)
                    return(False)
                elif charName in self.client.acctObj.getCharactersOnDisk():
                    msg = ("Invalid Character Name.  You already have a " +
                           "character named " + charName + ".\n")
                    self._spoolOut(msg)
                    dLog(logPrefix + msg, self._instanceDebug)
                    continue
                elif not self.client.acctObj.characterNameIsUnique(charName):
                    msg = ("Name is already in use.  Please try again\n")
                    self._spoolOut(msg)
                    dLog(logPrefix + msg, self._instanceDebug)
                    continue
                self.setName(charName)
                break
            else:   # use existing character name, as defined in characterList
                self.setName(characterList[inNum - 1])
                break

        if re.match(r"^.+@.+\..+/.+$", self.getId()):
            return(True)

        logger.error(logPrefix + "Could not generate ID - " + self.getId())
        return(False)

    def getArticle(gender):
        if gender == 'male':
            article = 'he'
            possessive = 'his'
            predicate = "he is"
        if gender == 'female':
            article = 'she'
            possessive = 'her'
            predicate = "she is"
        if gender == 'fluid':
            article = 'they'
            possessive = 'their'
            predicate = "they are"
        if gender == 'self':
            article = 'you'
            possessive = 'my'
            predicate = "you are"
        return(article, possessive, predicate)

    def knowsSpell(self, spell):
        if spell in self._knownSpells:
            return(True)
        return(False)

    def learnSpell(self, spell):
        if spell not in SpellList:
            return(False)

        if not self.knowsSpell(spell):
            self._knownSpells.append(spell)
            return(True)
        return(False)

    def getCoins(self):
        return(self._coins)

    def setCoins(self, num):
        self._coins = int(num)

    def addCoins(self, num):
        self._coins += int(num)
        self.save()

    def subtractCoins(self, num):
        self._coins -= int(num)
        self.save()

    def canAffordAmount(self, num):
        if self._coins >= int(num):
            return(True)
        return(False)

    def getBankBalance(self):
        return(self._bankBalance)

    def setBankBalance(self, num):
        self._bankBalance = int(num)

    def bankAccountAdd(self, num):
        self._bankBalance += int(num)

    def bankAccountSubtract(self, num):
        self._bankBalance -= int(num)

    def bankFeeAdd(self, num):
        self._bankFeesPaid += int(num)

    def getBankFeesPaid(self):
        return(self._bankFeesPaid)

    def calculateBankFees(self, num, rate):
        ''' returns the bank fee and the amount remaining '''
        fee = int((rate / 100) * int(num))
        remaining = int(num) - fee
        return (int(fee), int(remaining))

    def bankDeposit(self, num, feeRate=5):
        ''' deposit funds from character's purse to character's bank account
            * subtract entire amount from characters's coin purse
            * subtract bank deposit fees (default 5%)
            * add resulting amout to character's bank account
        '''
        if self.canAffordAmount(int(num)):
            self.subtractCoins(num)          # character pays the actual value
            bankfee, remainingCoin = self.calculateBankFees(num, feeRate)
            self.bankAccountAdd(remainingCoin)
            self.bankFeeAdd(bankfee)
            self.save()
            logger.info("bank - " + self.getName() + " deposited " +
                        str(remainingCoin) + " and paid " + str(bankfee) +
                        " in fees")
            return(True)
        return(False)

    def bankWithdraw(self, num, feeRate=0):
        ''' withdraw funds from character's bank account to character's purse
            * remove entire amount from bank
            * subtract any bank withdraw fees (default is 0%)
            * add resulting amount to character's purse
        '''
        if self.canWithdraw(int(num)):
            self.bankAccountSubtract(num)
            bankfee, remainingCoin = self.calculateBankFees(num, feeRate)
            self.addCoins(remainingCoin)
            self.bankFeeAdd(bankfee)
            self.save()
            logger.info("bank - " + self.getName() + " withdrew " +
                        str(remainingCoin) + " and paid " + str(bankfee) +
                        " in fees")
            return(True)
        return(False)

    def canWithdraw(self, num):
        if self._bankBalance >= int(num):
            return(True)
        return(False)

    def recordTax(self, num):
        ''' Some transactions have a room penalty.  For these, we record
            them as taxes paid.  Maybe, in the future, we'll have ways for
            characters to recoup their paid taxes (lottery?)
             '''
        self._taxesPaid += max(0, int(num))
        self.save()
        return(True)

    def getTax(self):
        return(self._taxesPaid)

    def setTax(self, num):
        self._taxesPaid = int(num)

    def dmTxt(self, msg):
        ''' return the given msg only if the character is a DM '''
        if self.isDm():
            return(msg)
        return('')

    def getFollowingInfo(self, whosAsking='me'):
        buf = ''
        if whosAsking == "me":
            (article, possessive, predicate) = self.getArticle('self')
        else:
            (article, possessive, predicate) = (
                self.getArticle(self.getGender()))

        if self._following != '':
            buf = predicate + ' following.' + self.following
        return(buf)

    def getDrunkInfo(self, whosAsking='me'):
        buf = ''
        if whosAsking == "me":
            (article, possessive, predicate) = self.getArticle('self')
        else:
            (article, possessive, predicate) = (
                self.getArticle(self.getGender()))

        if self._drunkSecs != '':
            buf = (predicate + ' drunk, and will sober up in ' +
                   self._drunkSecs + ' seconds\n')
        return(buf)

    def getHiddenInfo(self):
        buf = ''
        if self.isHidden() != '':
            buf = 'You are hidden.\n'
        return(buf)

    def dmInfo(self):
        buf = ''
        if self.isDm():
            dblstatList = ", ".join(str(x) for x in self._doubleUpStatLevels)
            buf += "DM visible info:\n"
            ROW_FORMAT = "  {0:16}: {1:<30}\n"
            buf += (ROW_FORMAT.format('Prompt', self.getPromptSize()) +
                    ROW_FORMAT.format('Hidden', str(self.isHidden())) +
                    ROW_FORMAT.format('2xStatLvls', dblstatList) +
                    ROW_FORMAT.format('DodgeBonus',
                                      str(self.getDodgeBonus())) +
                    ROW_FORMAT.format('BankBalance',
                                      str(self.getBankBalance())) +
                    ROW_FORMAT.format('TaxesPaid', str(self.getTax())) +
                    ROW_FORMAT.format('BankFeesPaid',
                                      str(self.getBankFeesPaid()))
                    )
            buf += '  Kill Counts:\n'
            ROW_FORMAT = "    {0:16}: {1:<30}\n"
            buf += (ROW_FORMAT.format('Weenies', str(self._weenykills)) +
                    ROW_FORMAT.format('Matched', str(self._matchedkills)) +
                    ROW_FORMAT.format('Valiant', str(self._valiantkills)) +
                    ROW_FORMAT.format('Epic', str(self._epickills)) +
                    ROW_FORMAT.format('Player', str(self._playerkills)))

        return(buf)

    def getClassKey(self, className=''):
        ''' Get the key for the classname '''
        if className == '':
            className = self.getClassName()
        return(self.classList.index(className))

    def customizeStats(self):
        ''' customize stats based on class, gender, alignment, and random '''

        # get the index numbers of the named elements to use for dict lookup
        classKey = self.getClassKey()
        genderKey = self.genderList.index(self.getGender())

        self.setMaxHP()
        self.setMaxMana()
        # increment the value of the CLASS bonus stats
        for bonusStat in self.classDict[classKey]['bonusStats']:
            self.incrementStat(bonusStat)
        # decrement the value of the CLASS penalty stats
        for bonusStat in self.classDict[classKey]['penaltyStats']:
            self.decrementStat(bonusStat)
        # increment the value of the GENDER bonus stats
        for bonusStat in self.genderDict[genderKey]['bonusStats']:
            self.incrementStat(bonusStat)
        # luck bonuses for lawful and chaotic alignments, since they are
        # inherently more limiting
        if self._alignment in ['lawful', 'chaotic']:
            self.incrementStat('luck')
            self.incrementStat('luck')
        # Randomly select an additional unused double up stat level
        #   keep selecting a random number until we find an unused one
        self._doubleUpStatLevels = self.classDict[classKey]['doubleUpStatLevels']  # noqa: E501
        while True:
            randX = random.randint(2, 9)
            if randX in self._doubleUpStatLevels:
                pass
            else:
                self._doubleUpStatLevels.append(randX)
                break

    def promptForClass(self, ROW_FORMAT):
        prompt = 'Classes:\n'
        for oneNum, oneName in enumerate(self.classList):
            desc = str(oneName) + ' - ' + self.classDict[oneNum]['desc']
            prompt = (prompt + ROW_FORMAT.format(oneNum, desc))
        prompt = (prompt + 'Select your character\'s class: ')
        inNum = self.client.promptForNumberInput(prompt,
                                                 (len(self.classList) - 1))

        if inNum == -1:
            return(False)

        self.setClassName(self.classList[inNum])
        return(True)

    def promptForGender(self, ROW_FORMAT):
        prompt = 'Genders:\n'
        for oneNum, oneName in enumerate(self.genderList):
            prompt += ROW_FORMAT.format(str(oneNum), oneName)
        prompt += 'Select your character\'s gender: '
        inNum = self.client.promptForNumberInput(prompt,
                                                 (len(self.genderList) - 1))
        if inNum == -1:
            return(False)

        self.setGender(self.genderList[int(inNum)])
        return(True)

    def promptForAlignment(self, ROW_FORMAT):
        prompt = 'Alignment:\n'

        prompt += ROW_FORMAT.format('0', 'Lawful - ' +
                                    'friend of good, enemy of evil')
        aNumOptions = 0
        if self.getClassName() != 'paladin':
            prompt += ROW_FORMAT.format('1', 'Neutral - ' +
                                        'Neither lawful, nor chaotic')
            aNumOptions = aNumOptions + 1
        if self.getClassName().lower() not in ['cleric', 'paladin']:
            prompt += ROW_FORMAT.format('2', 'Chaotic - ' +
                                        'unpredictable and untrustworthy')
            aNumOptions = aNumOptions + 1
        prompt += 'Select your character\'s alignment: '
        inNum = self.client.promptForNumberInput(prompt, aNumOptions)
        if inNum == -1:
            return(False)

        self.setAlignment(self.alignmentList[int(inNum)])
        return(True)

    def promptForSkills(self, ROW_FORMAT):
        prompt = 'Skills:\n'
        sList = {}
        for num, skill in enumerate(self.skillDict):
            prompt += ROW_FORMAT.format(num, skill.lstrip('_') + ' - ' +
                                        self.skillDict[skill])
            sList[num] = skill
        inNum = self.client.promptForNumberInput(prompt, len(self.skillDict))
        if inNum == -1:
            return(False)

        setattr(self, sList[inNum], 10)          # Set skill of choice to 10%
        return(True)

    def promptForDm(self, ROW_FORMAT):
        if self.client:                          # not set when testing
            if self.client.acctObj.isAdmin():
                prompt = 'Should this Character be a Dungeon Master (admin)?'
                if self.client.promptForYN(prompt):
                    self.setDm()
                    return(True)
        return(False)

    def promptForNewCharacter(self, promptFlag=True):
        '''Prompt user to input character info and return the results'''

        if promptFlag:
            ROW_FORMAT = "  ({0:1}) {1:<30}\n"
            self.promptForClass(ROW_FORMAT)
            self.promptForGender(ROW_FORMAT)
            self.promptForAlignment(ROW_FORMAT)
            self.promptForSkills(ROW_FORMAT)
            self.promptForDm(ROW_FORMAT)
        else:
            self.setClassName(getRandomItemFromList(self.classList))
            self.setGender(getRandomItemFromList(self.genderList))
            self.setAlignment(getRandomItemFromList(self.alignmentList))
            self._dodge = 10
        return(True)

    def getRandomStat(self):
        """Randomly picks a stat and returns the stat name"""
        randX = random.randint(0, (len(self.statList) - 1))
        # get the stat name, based on the random number
        return(self.statList[randX])

    def randomlyIncrementStat(self, points=1):
        """Randomly assign points to attributes"""
        for x in range(1, points + 1):
            self.incrementStat(self.getRandomStat())

    def randomlyDecrementStat(self, points=1):
        """Randomly assign points to attributes"""
        for x in range(1, points + 1):
            self.decrementStat(self.getRandomStat())

    def incrementStat(self, stat):
        ''' increment a given stat by one '''
        newvalue = int(getattr(self, stat)) + 1
        setattr(self, stat, newvalue)

    def decrementStat(self, stat):
        ''' increment a given stat by one '''
        newvalue = int(getattr(self, stat)) - 1
        setattr(self, stat, newvalue)

    def levelUp(self):
        '''Level up a character'''
        self._level += 1
        self.levelUpStats()
        self.reCalculateStats()
        self._achievedSkillForLevel = False

    def reCalculateStats(self):
        self.setAc()
        self.setMaxHP()
        self.setMaxMana()
        self.setExpForLevel()
        self.setMaxWeightForCharacter()
        return(None)

    def getHitPoints(self):
        return(self._hp)

    def setHitPoints(self, num):
        self._hp = int(num)

    def addHP(self, num=0):
        self._hp = min((self._hp + num), self.getMaxHP())

    def subtractHP(self, num=0):
        self._hp -= max(0, num)

    def setMaxHP(self, num=0):
        if num == 0:
            baseHealth = self.classDict[self.getClassKey()]['baseHealth']
            num = baseHealth * self.getLevel()
        self._maxhp = num

    def getMaxHP(self):
        return(self._maxhp)

    def getMana(self):
        return(self._mana)

    def setMana(self, num):
        self._mana = int(num)

    def addMana(self, num=0):
        self._mana = min((self._mana + num), self.getMaxMana())

    def setMaxMana(self, num=0):
        if num == 0:
            baseMagic = self.classDict[self.getClassKey()]['baseMagic']
            num = (baseMagic * self.getLevel())
        self._maxmana = num

    def getMaxMana(self):
        return(self._maxmana)

    def subtractMana(self, num):
        self._mana -= int(num)

    def setExpForLevel(self):
        self._expToNextLevel = (2 ** (9 + self.getLevel()))

    def setNearDeathExperience(self):
        ''' set stats so that character can recover from a near death exp '''
        self.setHitPoints(1)
        self.setPoisoned(False)
        self.setPlagued(False)

    def levelUpStats(self):
        '''Level up a character's stats'''
        newpoints = 1
        # check to see if level is a doubleUp level
        if self.getLevel() in self._doubleUpStatLevels:
            # Grant extra stat point
            newpoints = newpoints + 1
        if self.getLevel() % 5 == 0:
            # Grant extra stat point every 5th level
            newpoints = newpoints + 1
        elif self.getLevel() > 10:
            if random.randint(0, 99) < (self.luck * 3):
                # After level 10, its based on luck (roughly 30% chance)
                # There's a chance of getting an extra point on levels not
                # divisible by 5
                newpoints = newpoints + 1
        if newpoints == 1:
            if random.randint(0, 99) < (self.luck * 2):
                # Based on luck, (roughly 20% chance) experience for next level
                # may be reduced by 10%
                self.client.spoolOut("Hermes blesses you!  Your next " +
                                     "level will arrive in haste.")
                self._expToNextLevel = int(self._expToNextLevel * .90)
        self.randomlyIncrementStat(newpoints)
        self._statsearnedlastlevel = newpoints
        # increase max hitpoints/mana
        self.reCalculateStats()
        return(None)

    def levelDownStats(self):
        ''' decrease stats - used when someone dies '''
        # Lose the number of stats gained last level
        for numstat in range(1, self._statsearnedlastlevel + 1):
            self.randomlyDecrementStat(1)
        # Reduce stats an extra time if it's a double stat level.
        if self.getLevel() in self._doubleUpStatLevels:
            self.randomlyDecrementStat(1)
        else:
            # random chance of losing one additional stat
            randX = random.randint(1, 100)
            if randX > 50:
                self.randomlyDecrementStat(1)
        self.reCalculateStats()
        return(None)

    def setPromptSize(self, size):
        ''' change the prompt verbosity '''
        if size in ['full', 'brief']:
            self._prompt = size
        elif size == '':
            # if promptStr is blank, toggle between the prompts
            if self._prompt == 'full':
                self._prompt = 'brief'
            else:
                self._prompt = 'full'
        return(None)

    def getPromptSize(self):
        return(self._prompt)

    def setAc(self):
        ''' calculate the character\'s armor class '''
        ac = 0
        db = 0
        equipppedList = [self.getEquippedWeapon(), self.getEquippedArmor(),
                         self.getEquippedShield(), self.getEquippedRing(),
                         self.getEquippedNecklace()]
        for oneObj in equipppedList:
            if oneObj is not None:
                ac += oneObj.getAc()
                db += oneObj.getDodgeBonus()
        self._ac = ac
        self._dodgeBonus = db

    def getAc(self):
        return(self._ac)

    def getDodgeBonus(self):
        return(self._dodgeBonus)

    def setLoginDate(self):
        self._lastLoginDate = datetime.now()

    def setLogoutDate(self):
        self._lastLogoutDate = datetime.now()

    def setInputDate(self):
        self._lastInputDate = datetime.now()

    def setLastCmd(self, str1):
        self._lastCommand = str1

    def getLastCmd(self):
        return(self._lastCommand)

    def setLastAttackCmd(self, str1):
        self._lastAttackCmd = str1

    def getLastAttackCmd(self):
        return(self._lastAttackCmd)

    def setLastAttack(self, cmd="attack"):
        self.setLastAttackCmd(cmd)
        self.setLastAttackDate()

    def setLastAttackDate(self):
        self._lastAttackDate = datetime.now()

    def getLastAttackDate(self):
        return(self._lastAttackDate)

    def setSecondsUntilNextAttack(self, secs=3):
        self._secondsUntilNextAttack = int(secs)

    def getSecondsUntilNextAttack(self):
        return(self._secondsUntilNextAttack)

    def canAttack(self):
        if self.checkCooldown(self.getSecondsUntilNextAttack(),
                              "until next attack"):
            return(True)
        return(False)

    def setLastRegen(self, when='now'):
        if when == 'never':
            self._lastRegenDate = getNeverDate()
        else:
            self._lastRegenDate = datetime.now()

    def setLastPoison(self, when='now'):
        if when == 'never':
            self._lastPoisonDate = getNeverDate()
        else:
            self._lastPoisonDate = datetime.now()

    def isVulnerable(self):
        return(self._vulnerable)

    def setVulnerable(self, val=True):
        self._vulnerable = bool(val)

    def isDm(self):
        return(self._dm)

    def setDm(self):
        self._dm = True

    def removeDm(self):
        self._dm = False

    def isUsable(self):      # True for some objects, but not for characters
        return(False)

    def isEquippable(self):  # True for some objects, but not for characters
        return(False)

    def isMagicItem(self):   # True for some objects, but not for characters
        return(False)

    def isCarryable(self):   # True for some objects, but not for characters
        return(False)

    def isInvisible(self):
        return(self._invisible)

    def setInvisible(self, val=True):
        self._invisible = val

    def getLimitedSpellCount(self):
        return(int(self._limitedSpellsLeft))

    def reduceLimitedSpellCount(self, num=1):
        self._limitedSpellsLeft -= int(num)

    def getLimitedBroadcastCount(self):
        return(int(self._broadcastLimit))

    def reduceLimitedBroadcastCount(self, num=1):
        self._broadcastLimit -= int(num)

    def addExp(self, num):
        self._expToNextLevel -= num

    def isHidden(self):
        return(self._hidden)

    def isDrunk(self):
        return(self._drunk)

    def setDrunk(self, val=True):
        self._drunk = val

    def isBlessed(self):
        return(self._blessed)

    def setBlessed(self, val=True):
        self._blessed = val

    def isPoisoned(self):
        return(self._poisoned)

    def setPoisoned(self, val=True):
        self._poisoned = val

    def isPlagued(self):
        return(self._plagued)

    def setPlagued(self, val=True):
        self._plagued = val

    def isEvil(self):
        return(self._evil)

    def setEvil(self, val=True):
        self._evil = val

    def getLevel(self):
        return(self._level)

    def setLevel(self, num):
        self._level = int(num)

    def subtractlevel(self, num=1):
        self._level -= int(num)

    def isMagic(self):
        return(False)

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

    def isAttackingWithFist(self):
        if self.getEquippedWeapon().getName() == 'fist':
            return(True)
        return(False)

    def getEquippedWeapon(self):
        return(self._equippedWeapon)

    def getEquippedArmor(self):
        return(self._equippedArmor)

    def getEquippedShield(self):
        return(self._equippedShield)

    def getEquippedRing(self):
        return(self._equippedRing)

    def getEquippedNecklace(self):
        return(self._equippedNecklace)

    def getEquippedWeaponDamage(self):
        ''' Given the equipped weapon and attack type, return the damage '''
        damage = self.getFistDamage()

        if self.isAttackingWithFist():
            return(damage)

        if self.getEquippedWeapon().isBroken():
            self._spoolOut("Your weapon is broken.\n")
            return(0)

        weapon = self.getEquippedWeapon()
        minDamage = weapon.getMinimumDamage()
        maxDamage = weapon.getMaximumDamage()
        dLog('character.getEquippedWeaponDamage: weaponMin: ' +
             str(minDamage) + ' - weaponMax: ' + str(maxDamage),
             self._instanceDebug)
        damage += random.randint(minDamage, maxDamage)
        return (damage)

    def getEquippedWeaponDamageType(self):
        return(self.getEquippedWeapon().getDamageType())

    def decreaseChargeOfEquippedWeapon(self):
        ''' decrease charge counters of equipped weapon + notify '''
        weapon = self.getEquippedWeapon()
        if weapon.getName() != 'fist':
            weapon.decrementChargeCounter()
            if weapon.isBroken():
                self._spoolOut("Snap!  Your " +
                               weapon.describe(article='none') +
                               " breaks\n")
            elif self.getClassName() == 'ranger' and weapon.getCharges() == 10:
                self._spoolOut("Your " + weapon.describe(article='none') +
                               " is worse for wear and in need of repair.\n")

    def getEquippedProtection(self):
        ''' returns equipped armor and/or shield, as a list '''
        armor = self.getEquippedArmor()
        shield = self.getEquippedShield()
        objList = []
        if armor:
            objList.append(armor)
        if shield:
            objList.append(shield)
        return(objList)

    def decreaseChargeOfEquippedProtection(self):
        ''' decrease charge counters of equipped armor/shield + notify '''
        for obj in self.getEquippedProtection():
            obj.decrementChargeCounter()
            if obj.isBroken():
                self._spoolOut("Your " + obj.describe(article='none') +
                               " falls apart\n")
            elif self.getClassName() == 'ranger' and obj.getCharges() == 10:
                self._spoolOut("Your " + obj.describe(article='none') +
                               " is worse for wear and in need of repair.\n")

    def getEquippedWeaponToHit(self):
        ''' return tohit percentage of weapon '''
        weapon = self.getEquippedWeapon()
        if weapon.getName() == 'fist':
            return(0)
        return(weapon.getToHitBonus())

    def getCumulativeDodge(self):
        ''' return dodge percentage of armor + shield '''
        logPrefix = 'character.getCumulativeDodge: '
        # Start off with dodge skill
        dodgePct = self._dodge
        dLog(logPrefix + "dodgeSkill=" + str(dodgePct), self._instanceDebug)

        # Add on dodge from armor/shields
        for obj in self.getEquippedProtection():
            if not obj.isBroken():
                dodgePct += obj.getDodgeBonus()

        dLog(logPrefix + "withGear=" + str(dodgePct), self._instanceDebug)

        # It's a little bit strange to have to traverse back to the game/combat
        # class to get this data, but it seems to make more sense than trying
        # to pass it all around.
        fullAttackDict = self.client.gameObj.getAttackDict()
        attackDict = fullAttackDict.get(self.getLastAttackCmd(), {})
        dodgePct += attackDict.get('dodge', 0)
        dLog(logPrefix + "totalDodge=" + str(dodgePct), self._instanceDebug)
        return(dodgePct)

    def getSkillPercentage(self, skill):
        if skill[0] != '_':
            skill = '_' + skill   # Prepend underbar, if needed
        try:
            return(getattr(self, skill))
        except KeyError:
            pass
        return(0)

    def getEquippedSkillPercentage(self):
        ''' includes bonuses from skills and gear '''
        if self.isPlagued():
            return(0)
        skillName = self.getEquippedWeaponDamageType()
        percent = self.getSkillPercentage(skillName)
        necklace = self.getEquippedNecklace()
        if necklace:
            percent += necklace.getProtectionFromSkill(skillName)
        return(percent)

    def hasAchievedSkillForLevel(self):
        return(self._achievedSkillForLevel)

    def rollToBumpSkillForLevel(self, skill, percentChance=33):
        ''' given a skill name, if eligible, bump character's skill
            * Only one skill bump allowed per level
            * There's a random (default=33%) chance that skill is bumped
            * maximum skill is 50%
            '''

        if self.hasAchievedSkillForLevel():
            return(False)

        skilllevel = self.getSkillPercentage(skill)

        if skilllevel > 50:
            return(False)

        if random.randint(1, 100) <= percentChance:
            setattr(self, skill, skilllevel + 10)
            self._achievedSkillForLevel = True
            return(True)
        return(False)

    def checkCooldown(self, secs, msgStr=''):
        if self._lastAttackDate == getNeverDate():
            return(True)

        secsSinceLastAttack = secsSinceDate(self._lastAttackDate)
        secsRemaining = secs - secsSinceLastAttack

        # logger.debug("cooldown: ses(" + str(secs) +
        #               ') - secsSinceLastAttack(' +
        #               str(secsSinceLastAttack) + ") = secsRemaining(" +
        #               str(secsRemaining) + ") - " +
        #               dateStr(self._lastAttackDate))

        if secsRemaining <= 0:
            return(True)

        buf = ("You are not ready.  " +
               str(truncateWithInt(secsRemaining, 1)) + " seconds remain")
        if msgStr != '':
            buf += ' ' + msgStr
        buf += ".\n"
        self._spoolOut(buf)
        return(False)

    def getName(self):
        return(self._name)

    def describe(self):
        return(self._name)

    def getType(self):
        return(self.__class__.__name__)

    def isPermanent(self):
        return(False)

    def setName(self, _name):
        self._name = str(_name)

    def getGender(self):
        return(self._gender)

    def setGender(self, _gender):
        if _gender in self.genderList:
            self._gender = str(_gender)
        else:
            logger.error('setGender: Attempt to set invalid gender')

    def getClassName(self):
        return(self._classname)

    def setClassName(self, _classname):
        if _classname in self.classList:
            self._classname = str(_classname)
        else:
            logger.error('setClassName: Attempt to set invalid gender')

    def getAlignment(self):
        return(self._alignment)

    def setAlignment(self, _alignment):
        if _alignment in self.alignmentList:
            self._alignment = str(_alignment)
        else:
            logger.error('setAlignment: Attempt to set invalid gender')

    def getId(self):
        return(self._acctName + "/" + str(self.getName()))

    def getStrength(self):
        return(int(self.strength))

    def getDexterity(self):
        return(int(self.dexterity))

    def getIntelligence(self):
        return(int(self.intelligence))

    def getCharisma(self):
        return(int(self.charisma))

    def getConstitution(self):
        return(int(self.constitution))

    def getLuck(self):
        return(int(self.constitution))

    def getAttacking(self):
        return(self._attackTargets)

    def canSeeInTheDark(self):
        ''' ToDo: a light spell should allow players to see in the dark '''
        if self.isDm():
            return(True)
        return(False)

    def canSeeInvisible(self):
        if self.isDm():
            return(True)
        return(False)

    def canSeeHidden(self):
        if self.isDm():
            return(True)
        if self.getClassName().lower() in ["ranger", "rogue"]:
            return(True)
        if random.randint(1, 100) < int(self.getLuck() / 3):
            return(True)
        return(False)

    def kidnaps(self):
        return(False)

    def sendsToJail(self):
        return(False)

    def condition(self):
        ''' Return a non-numerical health status '''
        status = 'unknown'
        if self.getHitPoints() <= 0:
            status = 'dead'
        elif self.getHitPoints() < self.getMaxHP() * .10:
            # Less than 10% of health remains
            status = 'desperate'
        elif self.getHitPoints() < self.getMaxHP() * .25:
            # 11-25% of health remains
            status = 'injured'
        elif self.getHitPoints() < self.getMaxHP() * .50:
            # 26-50% of health remains
            status = 'drained'
        elif self.getHitPoints() < self.getMaxHP() * .75:
            # 51-75% of health remains
            status = 'fatigued'
        elif self.getHitPoints() < self.getMaxHP() * .99:
            # 76-99% of health remains
            status = 'healthy'
        elif self.getHitPoints() == self.getMaxHP():
            # totally healthy
            status = 'fresh'
        return(status)

    def dodge(self, basePercent=100):
        ''' Return true if dodged
            * If basePercent is increased, chance of dodging goes down.
            * chances improved by dex, class, dodge skill, and dodgeBonus '''
        randX = random.randint(1, 100)
        classMult = 2 if self.getClassName().lower() == "rogue" else 1
        skillMult = self._dodge + self._dodgeBonus

        dodgeAdv = (self.getDexterity() * (classMult + skillMult)/10)
        dodgeCalc = (randX + dodgeAdv) * 2
        dLog("dodge - calc=" + dodgeCalc + " >? basePercent=" +
             basePercent, self._instanceDebug)
        if dodgeCalc > basePercent:
            return(True)
        return(False)

    def acDamageReduction(self, damage):
        ''' reduce damage based on AC '''
        ac = self.getAc()

        # reduce AC if protection is broken
        for obj in self.getEquippedProtection():
            if obj.isBroken():
                ac -= obj.getAc()

        # reduce damage based on percentage:
        acReduction = int(damage * (.05 * ac))
        damage -= acReduction

        return(max(0, damage))

    def damageIsLethal(self, num=0):
        if num >= self.getHitPoints():
            return(True)
        return(False)

    def takeDamage(self, damage=0, nokill=False):
        ''' Take damage and check for death '''
        self.subtractHP(damage)
        if nokill and self.getHitPoints() <= 0:
            self.setNearDeathExperience()
        condition = self.condition()
        dLog(self.getName() + " takes " + str(damage) + " damage",
             self._instanceDebug)
        self.save()
        if self.getHitPoints() <= 0:
            if self.isDm():
                self._spoolOut("You would be dead if you weren't a dm." +
                               "  Resetting hp to maxhp.\n")
                self.setHitPoints(self._maxhp)
            else:
                self.processDeath()
        return(condition)

    def processDeath(self):
        # lose one or two levels
        buf = 'You are Dead'
        self.client.broadcast(self.describe() + ' has died\n')   # toDo: fix
        logger.info(self.describe() + ' has died')

        # random chance of losing two levels
        randX = random.randint(1, 100)
        chanceOfLosingTwoLevels = 50 - self.piety - (self.luck / 2)
        if self.getClassName().lower() in ['cleric', 'paladin']:
            # 10% reduction for clerics and paladins
            chanceOfLosingTwoLevels = chanceOfLosingTwoLevels - 10
        if randX > chanceOfLosingTwoLevels:
            levelsToLose = 2
        else:
            levelsToLose = 1

        for numlvl in range(1, levelsToLose + 1):
            self.levelDownStats()
            if self.getLevel() > 1:
                self.subtractlevel()

        self.setHitPoints(self.getMaxHP())
        self.setPoisoned(False)
        self.setPlagued(False)

        # return to starting room or guild
        self.client.gameObj.joinRoom(1, self)

        self.save()
        self._spoolOut(buf)
        return(True)

    def setRoom(self, roomObj):
        self._roomObj = roomObj

    def getRoom(self):
        return(self._roomObj)

    def removeRoom(self):
        self._roomObj = None

    def searchSucceeds(self, obj, basePercent=30):
        ''' Returns True if search succeeds
            * chance of success based on dex, level, and luck '''
        logPrefix = __class__.__name__ + " searchSucceeds: "

        if self.canSeeHidden():
            dLog(logPrefix + "Pass - Character can see hidden",
                 self._instanceDebug)
            return(True)

        percentChance = (basePercent + self.getDexterity() + self.getLevel() +
                         self.getLuck())

        if obj.getType() == 'Creature' or obj.getType() == 'Character':
            # +/- 10% per level difference
            percentChance += (self.getLevel() - obj.getLevel()) * 10

        if random.randint(1, 20) == 1:  # Always a 5 percent chance of success
            dLog(logPrefix + "Pass - Always 5% Chance", self._instanceDebug)
            return(True)

        randX = random.randint(1, 100)
        if randX <= percentChance:
            dLog(logPrefix + "Pass - Roll - " + str(randX) + " < " +
                 str(percentChance), self._instanceDebug)
            return(True)

        dLog(logPrefix + "Failed", self._instanceDebug)
        return(False)

    def equipFist(self):
        ''' equip fist, the default weapon - fist is a special weapon that is
            not in any inventory '''
        obj = Weapon()
        obj.setName("fist")
        obj._article = 'a'
        obj._singledesc = "fist"
        obj.setMaximumDamage(self.getFistDamage())
        self.equip(obj)

    def getFistDamage(self):
        ''' calculate damage for the fist, the default weapon '''
        damage = int((self.getStrength() / 5) + (self.getLevel() / 2))
        damage += self.classDict[self.getClassKey()]['baseDamage']
        damage -= random.randint(0, 3)
        return(max(0, damage))

    def equip(self, obj):
        # Deal with currently equipped item
        equippedObj = getattr(self, obj.getEquippedSlotName())
        if equippedObj is None:            # Nothing is currently equipped
            pass
        elif equippedObj == obj:        # desired object is already in use
            return(True)
        elif obj is not None:           # wearing some other item
            self.unEquip(obj)  # Pass object so we know which slot to vacate

        slotName = obj.getEquippedSlotName()
        if slotName:
            setattr(self, slotName, obj)
            self.setAc()
            return(True)
        return(False)

    def unEquip(self, obj=None, slotName=''):
        if obj and slotName == '':
            # Use the current object to determine slot name
            if obj.isEquippable():
                slotName = obj.getEquippedSlotName()

        if slotName == '':
            return(False)

        setattr(self, slotName, None)
        self.setAc()

        if self.getEquippedWeapon() is None:
            self.equipFist()

        return(True)

    def setDataFilename(self, dfStr=''):
        ''' sets the data file name.  - Override the superclass because we
            want the account info to be in the account directory. '''
        logPrefix = __class__.__name__ + " setDataFilename-c: "

        # generate the data file name based on class and id
        try:
            id = self.getId()
        except AttributeError:
            pass

        if not id:
            logger.error(logPrefix + "Could not retrieve Id to " +
                         "generate filename")
            return(False)

        if not re.match(r"^.+@.+\..+/.+$", id):
            logger.error(logPrefix + "ID is blank while generating filename." +
                         'id=' + id)
            return(False)

        self._datafile = os.path.abspath(DATADIR + '/Account/' +
                                         str(id) + '.pickle')

        return(True)

    def setHidden(self, val=True):
        self._hidden = val

    def attemptToHide(self):
        randX = random.randint(0, 99)

        hidechance = self.getLevel() * 20 + self.dexterity

        if self.getClassName().lower() == 'rogue':
            hidechance *= 2  # double the chance of success for rogues
        # consider additional bonus for guild status
        # half the chance of success if there are already creatures in the room
        if len(self._roomObj.getCreatureList()) > 0:
            hidechance /= 2

        hidechance = max(66, hidechance)  # Chance to hide tops out at 66%

        if (hidechance > randX):
            self.setHidden()
            return(True)
        return(False)

    def hearsWhispers(self):
        ''' calculate whether a character can hear whispers in a room
            todo: make this more random and skill/sluck based '''
        if self.getClassName().lower() == 'ranger':
            return(True)
        return(False)

    def adjustPrice(self, price):
        ''' Adjust the price of goods depending on character attributes
            * non-character price changes occur elsewhere '''
        # consider adjustments for charisma, alignment, luck
        return(price)

    def setMaxWeightForCharacter(self):
        ''' Maxweight varies depending on attributes '''
        weight = 10 * max(7, int(self.strength))
        self.setInventoryMaxWeight(weight)

    def fumbles(self, basePercent=20):
        ''' Return true if player fumbles.
            * Fumble is a trip while attacking which causes player to unequip
              weapon and shield and wait 30 seconds before attacking again
            * random chance, partially based on dex.
            * if fumble, player's weapon is unequipped
        '''
        fumbles = False

        if self.isAttackingWithFist():
            return(False)

        fumbleRoll = random.randint(1, 100)
        if fumbleRoll == 1:  # always a 1% change of fumbling
            fumbles = True
        elif fumbleRoll < (basePercent - self.getDexterity()):
            fumbles = True

        if fumbles:
            self.unEquip(slotName='_equippedWeapon')
            self.unEquip(slotName='_equippedShield')
            self.setSecondsUntilNextAttack(30)
        return(fumbles)

    def possibilyLoseHiddenWhenMoving(self):
        ''' set hidden to false if you fail the roll.
            * when moving, there is a chance that you will not remain hidden
                * base chance of remaining hidden is 50% + dex
                * rangers and theives get improved chance = dex
                a ranger/thief with 20 dex has 99% chance of staying hidden '''
        if not self.isHidden:
            return(False)

        oddsOfStayingHidden = 60 + self.getDexterity()
        if self.getClassName() in ['rogue', 'ranger']:
            oddsOfStayingHidden += self.getDexterity()
        if random.randint(1, 100) >= oddsOfStayingHidden:
            self.setHidden(False)

        return(True)

    def processPoisonAndRegen(self, regenInterval=90, poisonInterval=60):
        ''' At certain intervals, poison and hp regeneration kick in
            * poison should be faster and/or stronger than regen '''
        conAdj = self.getConstitution() - 12
        intAdj = self.getIntelligence() - 12
        regenHp = max(1, int(self.getMaxHP() / 10) + conAdj)
        regenMana = max(1, int(self.getMaxMana() / 8) + intAdj)
        poisonHp = max(1, int(self.getLevel() - conAdj))

        if not self.isPlagued():       # no regen if plagued
            # Check the time
            if self._lastRegenDate == getNeverDate():
                regenSecsRemaining = 0
            else:
                regenSecsRemaining = (regenInterval -
                                      secsSinceDate(self._lastRegenDate))
            dLog("regen counter: " + str(regenSecsRemaining) +
                 " secs - " + str(self._lastRegenDate) + " - " +
                 str(secsSinceDate(self._lastRegenDate)), False)
            if regenSecsRemaining <= 0:
                self.addHP(regenHp)
                self.addMana(regenMana)
                self.setLastRegen()

        if self.isPoisoned():          # take damage if poisoned
            # Check the time
            if self._lastPoisonDate == getNeverDate():
                poisonSecsRemaining = 0
            else:
                poisonSecsRemaining = (poisonInterval -
                                       secsSinceDate(self._lastPoisonDate))
            dLog("poison cntr: " + str(regenSecsRemaining) + " secs", False)

            if poisonSecsRemaining <= 0:
                self.spoolOut("As the poison circulates, you take " +
                              poisonHp + " damage.\n")
                self.takeDamage(poisonHp)
                self.setLastPoison()

    def updateKillCount(self, opponent):
        opponentLevel = opponent.getLevel()
        killerLevel = self.getLevel()

        if opponentLevel < killerLevel:
            self._weenykills += 1
        elif opponentLevel == killerLevel:
            self._matchedkills += 1
        elif opponentLevel > killerLevel:
            self._valiantkills += 1

        if opponent.getType() == 'Character':
            self._playerkills += 1

        if opponent.isPermanent():
            self._epickills += 1

    def getCircleSecs(self):
        ''' Returns the number seconds a creature will wait given a sucessful
            circle - based on character level/stats'''
        secsToWait = random.randint(self.getLevel(),
                                    20 + self.getDexterity())
        return(secsToWait)
