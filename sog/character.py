''' Character class '''

from datetime import datetime
import logging
import os
import pprint
import random

from common.storage import Storage
from common.attributes import AttributeHelper
from common.general import getNeverDate, differentDay, dLog, secsSinceDate
from common.paths import DATADIR


class Character(Storage, AttributeHelper):
    """ Character class """

    _instanceDebug = False

    statList = ['strength', 'dexterity', 'intelligence', 'piety',
                'charisma', 'constitution', 'luck']
    genderList = ['male', 'female', 'fluid']
    alignmentList = ['lawful', 'neutral', 'chaotic']
    classList = ['fighter', 'rogue', 'mage', 'cleric', 'ranger', 'paladin']
    skillDict = {
        '_slash': 'swords and axes come easily to you',
        '_bludgeon': 'hammers and maces are an extention of your arms',
        '_pierce': 'you gravitate toward daggers and spears',
        '_magicuse': 'an inner confidence that enhances spells',
        '_heal': 'a natural ability to mend and cure',
        '_dodge': 'being quick on your feet helps avoid blows'}

    genderDict = {
        '0': {
            'name': 'male',
            'pronoun': 'him',
            'possisivepronoun': 'his',
            'bonusStats': ['strength', 'constitution']},
        '1': {
            'name': 'female',
            'pronoun': 'her',
            'possisivepronoun': 'her',
            'bonusStats': ['charisma', 'intelligence']},
        '2': {
            'name': 'fluid',
            'pronoun': 'them',
            'possisivepronoun': 'their',
            'bonusStats': ['piety', 'dexterity']}
        }
    classDict = {
        '0': {
            'name': 'fighter',
            'desc': 'Master of combat, skilled in weapondry',
            'pros': 'Attack/Defense Bonuses',
            'cons': 'Poor Magic Use',
            'hitpointAdjustment': 4,
            'magicpointAdjustment': -4,
            'damageAdjustment': 1,
            'doubleUpStatLevels': [2, 3, 7],
            'bonusStats': ['strength', 'constitution'],
            'penaltyStats': ['intelligence', 'piety'],
            'baseHealth': 18,
            'baseMagic': 2
            },
        '1': {
            'name': 'rogue',
            'desc': 'A scoundrel fluent in stealth and trickery',
            'pros': 'Hiding/Defense Bonuses',
            'cons': 'Poor Attack',
            'hitpointAdjustment': 2,
            'magicpointAdjustment': -2,
            'damageAdjustment': 0,
            'doubleUpStatLevels': [3, 7, 9],
            'bonusStats': ['dexterity', 'charisma'],
            'penaltyStats': ['strength', 'piety'],
            'baseHealth': 14,
            'baseMagic': 6
            },
        '2': {
            'name': 'mage',
            'desc': 'A vulnerable and powerful scholarly spellcaster',
            'pros': 'Spell abilities and Bonuses',
            'cons': 'Can not use metal armor',
            'hitpointAdjustment': -4,
            'magicpointAdjustment': 4,
            'damageAdjustment': -1,
            'doubleUpStatLevels': [2, 6, 8],
            'bonusStats': ['intelligence', 'intelligence'],
            'penaltyStats': ['strength', 'strength'],
            'baseHealth': 6,
            'baseMagic': 14
            },
        '3': {
            'name': 'cleric',
            'desc': 'Healer and servant of higher powers',
            'pros': 'Healing Abilities and Bonuses + Undead Turning',
            'cons': 'Can not use bladed weapons',
            'hitpointAdjustment': -3,
            'magicpointAdjustment': 3,
            'damageAdjustment': -1,
            'doubleUpStatLevels': [4, 6, 8],
            'bonusStats': ['piety', 'piety'],
            'penaltyStats': ['strength', 'dexterity'],
            'baseHealth': 7,
            'baseMagic': 13,
            },
        '4': {
            'name': 'ranger',
            'desc': 'A rough and wild hunter ',
            'pros': 'Minor Defense Bonuses & Spell Abilities',
            'cons': 'Poor Charisma',
            'hitpointAdjustment': 0,
            'magicpointAdjustment': 0,
            'doubleUpStatLevels': [2, 4, 9],
            'damageAdjustment': 0,
            'bonusStats': ['dexterity', 'intelligence'],
            'penaltyStats': ['charisma', 'charisma'],
            'baseHealth': 12,
            'baseMagic': 8,
            },
        '5': {
            'name': 'paladin',
            'desc': 'A righteous fighter who hunts the forces of evil',
            'pros': 'Minor Attack Bonuses, Healing, and Undead Turning',
            'cons': 'Must be lawful, can not steal',
            'hitpointAdjustment': 1,
            'magicpointAdjustment': -1,
            'damageAdjustment': 1,
            'doubleUpStatLevels': [3, 8, 9],
            'bonusStats': ['charisma', 'piety'],
            'penaltyStats': ['intelligence', 'constitution'],
            'baseHealth': 10,
            'baseMagic': 10
            }
        }  # end classDict

    attributesThatShouldntBeSaved = ['svrObj']

    # int attributes
    intAttributes = ['_expToNextLevel', '_level', '_maxhitpoints',
                     '_hitpoints', '_maxspellpoints', '_spellpoints',
                     '_statsearnedlastlevel', '_limitedSpellsLeft',
                     '_broadcastLimit', '_slash', '_bludgeon', '_pierce',
                     '_magicuse', '_heal', '_dodge', '_coins', '_ac',
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
    listAttributes = ['_inventory', '_knownSpells', '_doubleUpStatLevels']

    # obsolete attributes (to be removed)
    obsoleteAtt = ['_money', '_weight']

    def __init__(self, svrObj=None, acctName=''):
        AttributeHelper.__init__(self)
        self.svrObj = svrObj
        self._acctName = acctName
        self.setName('')

        self._dm = False

        self.setPromptSize('full')

        # set base status
        for onestat in self.statList:
            setattr(self, onestat, '8')

        self._expToNextLevel = (2 ** 9)
        self._level = 1
        self._maxhitpoints = 10
        self._maxspellpoints = 10
        self._hitpoints = 10
        self._spellpoints = 10
        self._statsearnedlastlevel = 0
        self._maxitems = 12

        # skills are percentages, one of which can go up each level
        for onestat in self.skillDict.keys():
            setattr(self, onestat, 0)
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
        self._poisoned = False
        self._plagued = False

        # hidden stats
        self._evil = False
        self._invisible = False
        self._nonexistent = False
        self._playtester = False

        self.roomObj = None

        self._bankBalance = 0
        self._coins = 100
        self._inventory = []
        self._knownSpells = []
        self._doubleUpStatLevels = []

        self._creationDate = datetime.now()
        self._lastLogoutDate = getNeverDate()
        self._lastInput = getNeverDate()
        self._lastAttack = getNeverDate()
        self._lastHeal = getNeverDate()
        self._playtester = False

        self._ac = 0             # Each point is 5% damage reduction
        self._dodgeBonus = 0     # Percent - Extra chance of not being hit

        self._weenykills = 0     # kills below current level
        self._matchedkills = 0   # kills at current level
        self._valiantkills = 0   # kills above current level
        self._epickills = 0      # special kills
        self._playerkills = 0    # player kills

        self.resetTempStats()
        self.resetDailyStats()

        return(None)

    def __str__(self):
        return("Character " + self.getName() + " of account " +
               str(self._acctName))

    def debug(self):
        return(pprint.pformat(vars(self)))

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
                    self.svrObj.acctObj.addCharacterToAccount(charName)
                    self.svrObj.acctObj.save()
                else:
                    buf = ('Character ' + charName +
                           ' could not be created for ' + self._acctName)
                    dLog(pStr + buf, self._instanceDebug)
                    self.svrObj.spoolOut(buf + '\n')
                    return(False)
            if not self.isValid():
                buf = 'Character ' + charName + ' is not valid'
                dLog(pStr + buf, self._instanceDebug)
                self.svrObj.spoolOut(buf + '\n')
                return(False)
        else:
            return(False)

        self.setLoginDate()
        self.svrObj.charObj = self

        self.svrObj.spoolOut(buf)
        return(True)

    def create(self, charName):
        ''' create a new character
            * Call promptForNewCharacter to prompt user for customization
            * return True if character is _creature
            * return False and scrub character if character was not created
            '''
        self.__init__(self.svrObj)
        self.setName(charName)
        self.setPromptSize('full')
        self.setLoginDate()

        # customize
        if self.promptForNewCharacter():
            if not self.isValid():
                return(False)

            self.customizeStats()
            self.randomlyIncrementStat(12)

            # set starting points for changing stats that depend on other stats
            self._hitpoints = self._maxhitpoints
            self._spellpoints = self._maxspellpoints

            self.resetTempStats()
        else:
            self.__init__(self.svrObj)
            return(False)

        if self.isValid():
            self.save()
        else:
            self.__init__(self.svrObj)
            return(False)
        return(True)

    def fixAttributes(self):
        ''' Sometimes we change attributes, and need to fix them in rooms
            that are saved.  This method lets us do that.  First we call
            the generic superClass fixAttributes to fix the types and remove
            obsolete vars.  Here, we can also add class specific logic for
            copying values from one attribute to another, etc '''

        AttributeHelper.fixAttributes(self)

    def postLoad(self):
        self.truncateInventory(12)
        self.resetTempStats()

    def resetTempStats(self):
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
        self.setMaxWeight()

        self._hidden = False
        self._blessed = False
        self._drunk = False

        self._roomObj = None

        self._attackTargets = []

        self._lastInput = getNeverDate()
        self._lastAttack = getNeverDate()
        self._lastHeal = getNeverDate()

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
        if hasattr(self, 'svrObj'):
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

    def getDesc(self):
        ''' Returns a string that describes the in-game appearance '''
        buf = (self.getName() + ' is a level ' + str(self.getLevel()) + " " +
               self._gender + " " + self.getClassName())
        if self._alignment == 'lawful':
            buf += " who tends to follow the rules"
        elif self._alignment == 'chaotic':
            buf += " who lives life on the edge"
        buf += ".\n"
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
        buf += self.dmInfo()
        return(buf)

    def financialInfo(self):
        buf = ("You have " + str(self.getCoins()) + " shillings in " +
               "your purse.\n")
        return(buf)

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
            logging.info("bank - " + self.getName() + " deposited " +
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
            logging.info("bank - " + self.getName() + " withdrew " +
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

    def dmTxt(self, msg):
        ''' return the given msg only if the character is a DM '''
        if self.isDm():
            return(msg)
        return('')

    def statsInfo(self):
        ''' Display character stats'''
        buf = "Stats:\n"
        ROW_FORMAT = "  {0:14}: {1:<30}\n"
        for onestat in self.statList:
            buf += ROW_FORMAT.format(onestat, str(getattr(self, onestat)))
        return(buf)

    def inventoryInfo(self):
        ''' Display inventory '''
        buf = "Inventory:\n"
        ROW_FORMAT = "  ({0:2}) {1:<60}\n"
        itemlist = ''
        for num, oneObj in enumerate(self._inventory):
            dmInfo = '(' + str(oneObj.getId()) + ')'
            itemlist += (ROW_FORMAT.format(num, oneObj.describe() +
                         self.dmTxt(dmInfo)))

        if itemlist:
            buf += itemlist
        else:
            buf += "  Nothing\n"
        return(buf)

    def skillsInfo(self):
        ''' Display character skills'''
        buf = ("Skills:")
        ROW_FORMAT = "  {0:14}: {1:<30}\n"
        if self._achievedSkillForLevel:
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
        hitTxt = str(self.getHitPoints()) + "/" + str(self._maxhitpoints)
        magTxt = str(self.getSpellPoints()) + "/" + str(self._maxspellpoints)
        buf = ("You have " + hitTxt + " health pts and " +
               magTxt + " magic pts.")
        if self.isDm():
            buf += "  Your armor class is " + str(self._ac)
        buf += '\n'
        return(buf)

    def expInfo(self):
        ROW_FORMAT = "  {0:14}: {1:<30}\n"
        buf = ("Experience:\n")
        buf += ROW_FORMAT.format("Level", str(self.getLevel()))
        if self.getPromptSize() == 'full':
            buf += ('  ' + str(self._expToNextLevel) +
                    " experience needed to get to level " +
                    str(int(self.getLevel()) + 1) + '\n')
        else:
            buf += " - " + str(self._expToNextLevel) + " to go."
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
                str(self.calculateWeight(self.getInventory())) + "/" +
                str(self._maxweight) + " lbs of items.\n")
        buf += prefix + ' wearing '
        if self.getEquippedArmor() is None:
            buf += 'no armor, '
        else:
            buf += self.getEquippedArmor().describe() + ', '

        buf += 'holding '
        if self.getEquippedWeapon() is None:
            buf += 'no weapon, '
        else:
            buf += self.getEquippedWeapon().describe() + ', '

        buf += 'and holding '
        if self.getEquippedShield() is None:
            buf += 'no shield.\n'
        else:
            buf += self.getEquippedShield().describe() + '.\n'

        buf += prefix + ' are sporting '
        if self.getEquippedRing() is None:
            buf += 'nothing'
        else:
            buf += (" " + self.getEquippedRing().getArticle() + " " +
                    self.getEquippedRing().describe())
        buf += ' on your finger and '

        if self.getEquippedNecklace() is None:
            buf += 'nothing'
        else:
            buf += (" " + self.getEquippedNecklace().getArticle() + " " +
                    self.getEquippedNecklace().describe())
        buf += ' around your neck\n'
        return(buf)

    def selectCharacter(self):
        ''' prompt user to select a character to load
            store resulting character name into self._name
            return True/False'''
        characterList = self.svrObj.acctObj.getCharacterList()
        numOfCharacters = len(characterList)
        openCharacterSlots = (self.svrObj.acctObj.getMaxNumOfCharacters() -
                              numOfCharacters)
        self.setName('')

        while True:
            prompt = "Select character to play : \n"
            if openCharacterSlots > 0:
                prompt += "  (0) Create new character\n"
            if numOfCharacters > 0:
                prompt += self.svrObj.acctObj.showCharacterList(indent='  ')
            prompt += 'Enter number or press [enter] to exit: '
            inNum = self.svrObj.promptForNumberInput(prompt, numOfCharacters)
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
                charName = self.svrObj.promptForInput(prompt, r'^[A-Za-z][A-Za-z0-9_\- ]{2,}$', errmsg)  # noqa: E501
                if charName == "":
                    dLog("selectCharacter: name is blank",
                         self._instanceDebug)
                    return(False)
                elif charName in self.svrObj.acctObj.getCharactersOnDisk():
                    msg = ("Invalid Character Name.  You already have a " +
                           "character named " + charName + ".\n")
                    self.svrObj.spoolOut(msg)
                    dLog("selectCharacter: " + msg, self._instanceDebug)
                    return(False)
                elif not self.svrObj.acctObj.characterNameIsUnique(charName):
                    msg = ("Name is already in use.  Please try again\n")
                    self.svrObj.spoolOut(msg)
                    dLog("selectCharacter: " + msg, self._instanceDebug)
                    return(False)
                self.setName(charName)
                return(True)
            else:   # use existing character name, as defined in characterList
                self.setName(characterList[inNum - 1])
                return(True)
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

    def getFollowingInfo(self, whosAsking='me'):
        buf = ''
        if whosAsking == "me":
            (article, possessive, predicate) = self.getArticle('self')
        else:
            (article, possessive, predicate) = self.getArticle(self._gender)

        if self._following != '':
            buf = predicate + ' following.' + self.following
        return(buf)

    def getDrunkInfo(self, whosAsking='me'):
        buf = ''
        if whosAsking == "me":
            (article, possessive, predicate) = self.getArticle('self')
        else:
            (article, possessive, predicate) = self.getArticle(self._gender)

        if self._drunkSecs != '':
            buf = (predicate + ' drunk, and will sober up in ' +
                   self._drunkSecs + ' seconds\n')
        return(buf)

    def getHiddenInfo(self):
        buf = ''
        if self.getHidden() != '':
            buf = 'You are hidden.\n'
        return(buf)

    def getPoisonInfo(self):
        buf = ''
        if self.getPoisoned() != '':
            buf = 'You are slowly dying from poison.\n'
        return(buf)

    def getPlagueInfo(self):
        buf = ''
        if self.getPlagued() != '':
            buf = 'You are infected with the plague.\n'
        return(buf)

    def dmInfo(self):
        buf = ''
        if self.isDm():
            dblstatList = ", ".join(str(x) for x in self._doubleUpStatLevels)
            buf += "DM visible info:\n"
            ROW_FORMAT = "  {0:16}: {1:<30}\n"
            buf += (ROW_FORMAT.format('Prompt', self.getPromptSize()) +
                    ROW_FORMAT.format('2xStatLvls', dblstatList) +
                    ROW_FORMAT.format('DodgeBounus',
                                      str(self.getDodgeBonus())) +
                    ROW_FORMAT.format('BankBalance', str(self._bankBalance)) +
                    ROW_FORMAT.format('TaxesPaid', str(self._taxesPaid)) +
                    ROW_FORMAT.format('BankFeesPaid', str(self._bankFeesPaid))
                    )
            buf += '  Kill Counts:\n'
            ROW_FORMAT = "    {0:16}: {1:<30}\n"
            buf += (ROW_FORMAT.format('Weenies', str(self._weenykills)) +
                    ROW_FORMAT.format('Matched', str(self._matchedkills)) +
                    ROW_FORMAT.format('Valiant', str(self._valiantkills)) +
                    ROW_FORMAT.format('Epic', str(self._epickills)) +
                    ROW_FORMAT.format('Player', str(self._playerkills)))

        return(buf)

    def getClassKey(self, className):
        ''' Get the key for the classname '''
        if className == '':
            className = self.className()
        return(str(self.classList.index(className)))

    def customizeStats(self):
        ''' customize stats based on class, gender, alignment, and random '''

        # get the index numbers of the named elements to use for dict lookup
        classKey = self.getClassKey(self.getClassName())
        genderKey = self.genderList.index(self._gender)

        self._maxhitpoints = self.classDict[classKey]['baseHealth']
        self._maxspellpoints = self.classDict[classKey]['baseMagic']
        # increment the value of the CLASS bonus stats
        for bonusStat in self.classDict[classKey]['bonusStats']:
            self.incrementStat(bonusStat)
        # decrement the value of the CLASS penalty stats
        for bonusStat in self.classDict[classKey]['penaltyStats']:
            self.decrementStat(bonusStat)
        # increment the value of the GENDER bonus stats
        for bonusStat in self.genderDict[str(genderKey)]['bonusStats']:
            self.incrementStat(bonusStat)
        # luck bonuses for lawful and chaotic alignments, since they are
        # inherently more limiting
        if self._alignment in ['lawful', 'chaotic']:
            self.incrementStat('luck')
            self.incrementStat('luck')
        # Randomly select an additional unused double up stat level
        #   keep selecting a random number until we find an unused one
        self._doubleUpStatLevels = self.classList[classKey]['doubleUpStatLevels']  # noqa: E501
        while True:
            randX = random.randint(2, 9)
            if randX in self._doubleUpStatLevels:
                pass
            else:
                self._doubleUpStatLevels.append(randX)
                break
        # hitpoint/magicpoint adjustments
        self._maxhitpoints += self.classDict[classKey]['hitpointAdjustment']
        self._maxmagicpoints += self.classDict[classKey]['magicpointAdjustment']  # noqa: E501

    def promptForClass(self, ROW_FORMAT):
        prompt = 'Classes:\n'
        for oneNum, oneName in enumerate(self.classList):
            desc = str(oneName) + ' - ' + self.classDict[str(oneNum)]['desc']
            prompt = (prompt + ROW_FORMAT.format(oneNum, desc))
        prompt = (prompt + 'Select your character\'s class: ')
        inNum = self.svrObj.promptForNumberInput(prompt,
                                                 (len(self.classList) - 1))
        if inNum == -1:
            return(False)

        self._classname = self.classList[inNum]
        return(True)

    def promptForGender(self, ROW_FORMAT):
        prompt = 'Genders:\n'
        for oneNum, oneName in enumerate(self.genderList):
            prompt += ROW_FORMAT.format(str(oneNum), oneName)
        prompt += 'Select your character\'s gender: '
        inNum = self.svrObj.promptForNumberInput(prompt,
                                                 (len(self.genderList) - 1))
        if inNum == -1:
            return(False)

        self._gender = self.genderList[int(inNum)]
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
        if self.getClassName().lower() in ['cleric', 'paladin']:
            prompt += ROW_FORMAT.format('2', 'Chaotic - ' +
                                        'unpredictable and untrustworthy')
            aNumOptions = aNumOptions + 1
        prompt += 'Select your character\'s alignment: '
        inNum = self.svrObj.promptForNumberInput(prompt, aNumOptions)
        if inNum == -1:
            return(False)

        self._alignment = self.alignmentList[int(inNum)]
        return(True)

    def promptForSkills(self, ROW_FORMAT):
        prompt = 'Skills:\n'
        sList = {}
        for num, skill in enumerate(self.skillDict):
            prompt += ROW_FORMAT.format(num, skill.lstrip('_') + ' - ' +
                                        self.skillDict[skill])
            sList[num] = skill
        inNum = self.svrObj.promptForNumberInput(prompt, len(self.skillDict))
        if inNum == -1:
            return(False)

        setattr(self, sList[inNum], 10)          # Set skill of choice to 10%
        return(True)

    def promptForDm(self, ROW_FORMAT):
        if self.svrObj:                          # not set when testing
            if self.svrObj.acctObj.isAdmin():
                prompt = 'Should this Character be a Dungeon Master (admin)?'
                if self.svrObj.promptForYN(prompt):
                    self.setDm()
                    return(True)
        return(False)

    def promptForNewCharacter(self, ):
        '''Prompt user to input character info and return the results'''

        ROW_FORMAT = "  ({0:1}) {1:<30}\n"
        self.promptForClass(ROW_FORMAT)
        self.promptForGender(ROW_FORMAT)
        self.promptForAlignment(ROW_FORMAT)
        self.promptForSkills(ROW_FORMAT)
        self.promptForDm(ROW_FORMAT)
        return(True)

    def getRandomStat(self):
        """Randomly picks a stat and returns the stat name"""
        randX = random.randint(0, (len(self.statList) - 1))
        # get the stat name, based on the random number
        return(self.statList[randX])

    def randomlyIncrementStat(self, points=1):
        """Randomly assign points to attributes"""
        for x in range(1, points):
            self.incrementStat(self.getRandomStat())

    def randomlyDecrementStat(self, points=1):
        """Randomly assign points to attributes"""
        for x in range(1, points):
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
        self._level = self._level + 1
        self._levelUpStats()
        self.reCalculateStats()
        self._achievedSkillForLevel = False

    def reCalculateStats(self):
        self.setAc()
        self.setMaxHP()
        self.setMaxSP()
        self.setExpForLevel()
        self.setMaxWeight()
        return(None)

    def setMaxHP(self):
        self._maxhitpoints = (self.classDict[self.getClassKey()]['baseHealth']
                              * self._level)

    def setMaxSP(self):
        self._maxspellpoints = (self.classDict[self.getClassKey()]['baseMagic']
                                * self._level)

    def setExpForLevel(self):
        self._expToNextLevel = (2 ** (9 + self._level))

    def levelUpStats(self):
        '''Level up a character's stats'''
        newpoints = 1
        # check to see if level is a doubleUp level
        if self._level in self._doubleUpStatLevels:
            # Grant extra stat point
            newpoints = newpoints + 1
        if self._level % 5 == 0:
            # Grant extra stat point every 5th level
            newpoints = newpoints + 1
        elif self._level > 10:
            if random.randint(0, 99) < (self._luck * 3):
                # After level 10, its based on luck (roughly 30% chance)
                # There's a chance of getting an extra point on levels not
                # divisible by 5
                newpoints = newpoints + 1
        if newpoints == 1:
            if random.randint(0, 99) < (self._luck * 2):
                # Based on luck, (roughly 20% chance) experience for next level
                # may be lowered by 10%
                self._expToNextLevel = int(self._expToNextLevel * .90)
        # increase max hitpoints/spellpoints
        self.randomlyIncrementStat(self, newpoints)
        self._statsearnedlastlevel = newpoints
        self.reCalculateStats()
        return(None)

    def levelDownStats(self):
        ''' decrease stats - used when someone dies '''
        # Lose the number of stats gained last level
        for numstat in range(1, self._statsearnedlastlevel):
            self.randomlyDecrementStat(self, 1)
        # Reduce stats an extra time if it's a double stat level.
        if self._level in self._doubleUpStatLevels:
            self.randomlyDecrementStat(self, 1)
        else:
            # random chance of losing one additional stat
            randX = random.randint(1, 100)
            if randX > 50:
                self.randomlyDecrementStat(self, 1)
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

    def setLastAttack(self):
        self._lastAttack = datetime.now()

    def setLastHeal(self):
        self._lastHeal = datetime.now()

    def getHitPoints(self):
        return(self._hitpoints)

    def getSpellPoints(self):
        return(self._spellpoints)

    def getClassName(self):
        return(self._classname)

    def isDm(self):
        return(self._dm)

    def setDm(self):
        self._dm = True

    def removeDm(self):
        self._dm = False

    def isInvisible(self):
        return(self._invisible)

    def setInvisible(self, val=True):
        self._invisible = val

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

    def setInputCommand(self, cmd):
        self._lastInputCommand = cmd

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

    def getSkillPercentage(self, skill='slash'):
        return(getattr(self, skill))

    def getInventory(self):
        return(self._inventory)

    def removeFromInventory(self, objObj):
        self.unEquip(objObj)
        self.setAc()
        self._inventory.remove(objObj)
        self.save()
        return(True)

    def addToInventory(self, objObj):
        self._inventory.append(objObj)
        self.save()
        return(True)

    def truncateInventory(self, num):
        ''' remove everything from inventory that exceeds <num> items '''
        del self._inventory[num:]

    def checkCooldown(self, secs):
        secsSinceLastAttack = secsSinceDate(self._lastAttack)
        if secsSinceLastAttack < secs:
            return(True)
        else:
            secsRemaining = secs - secsSinceDate(self._lastAttack)
            self.svrObj.spoolOut("You must wait " + secsRemaining +
                                 " seconds")
        return(False)

    def getName(self):
        return(self._name)

    def setName(self, name):
        self._name = str(name)

    def getStrength(self):
        return(self.strength)

    def getDexterity(self):
        return(self.dexterity)

    def getIntelligence(self):
        return(self.intelligence)

    def getCharisma(self):
        return(self.charisma)

    def getConstitution(self):
        return(self.constitution)

    def getLuck(self):
        return(self.constitution)

    def getAttacking(self):
        return(self._attackTargets)

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

    def weightAvailable(self):
        weight = self._maxweight - self.calculateWeight(self._inventory)
        return(int(weight))

    def canCarryAdditionalWeight(self, num):
        if self.weightAvailable() >= int(num):
            return(True)
        return(False)

    def calculateWeight(self, inventory=[]):
        ''' Calculate the weight of a list of objects '''
        weight = 0
        for oneObj in list(inventory):
            weight += oneObj.getWeight()
        return(weight)

    def condition(self):
        ''' Return a non-numerical health status '''
        if self.getHitPoints() <= 0:
            status = 'dead'
        elif self.getHitPoints() < self._maxhitpoints * .10:
            # Less than 10% of health remains
            status = 'desperate'
        elif self.getHitPoints() < self._maxhitpoints * .25:
            # 11-25% of health remains
            status = 'injured'
        elif self.getHitPoints() < self._maxhitpoints * .50:
            # 26-50% of health remains
            status = 'drained'
        elif self.getHitPoints() < self._maxhitpoints * .75:
            # 51-75% of health remains
            status = 'fatigued'
        elif self.getHitPoints() < self._maxhitpoints * .99:
            # 76-99% of health remains
            status = 'healthy'
        elif self.getHitPoints() == self._maxhitpoints:
            # Less than 25% of health remains
            status = 'fresh'
        return(status)

    def dodge(self, basePercent=100):
        ''' Return true if dodged
            * If basePercent is increased, chance of dodging goes down.
            * chances improved by dex, class, dodge skill, and dodgeBonus '''
        randX = random.randint(1, 100)
        classMult = 2 if self.getClass().lower() == "rogue" else 1
        skillMult = self._dodge + self._dodgeBonus

        dodgeAdv = (self.getDex() * (classMult + skillMult)/10)
        dodgeCalc = (randX + dodgeAdv) * 2
        dLog("dodge - calc=" + dodgeCalc + " >? basePercent=" +
             basePercent, self._instanceDebug)
        if dodgeCalc > basePercent:
            return(True)
        return(False)

    def takeDamage(self, damage=0):
        ''' Take damage and check for death '''
        # reduce damage based on AC
        damage *= (.05 * self.getAc())

        self._hitpoints = self.getHitPoints() - damage
        condition = self.condition()
        self.save()
        if condition == 'dead':
            self.processDeath()
        return(condition)

    def processDeath(self):
        # lose one or two levels
        buf = 'You are Dead'
        self.svrObj.broadcast(self._displayName + ' has died')   # toDo: fix
        logging.info(self._displayName + ' has died')

        # random chance of losing two levels
        randX = random.randint(1, 100)
        chanceOfLosingTwoLevels = 50 - self._piety - (self._luck / 2)
        if self.getClassName().lower() in ['cleric', 'paladin']:
            # 10% reduction for clerics and paladins
            chanceOfLosingTwoLevels = chanceOfLosingTwoLevels - 10
        if randX > chanceOfLosingTwoLevels:
            levelsToLose = 2
        else:
            levelsToLose = 1

        for numlvl in range(1, levelsToLose):
            self._levelDownStats()
            self._level = self._level - 1

        self._hitpoints = self._maxhitpoints

        # return to starting room or guild
        self._roomObj = self.svrObj.gameObj.placePlayer(0)

        self.save()
        self.svrObj.spoolOut(buf)
        return(True)

    def setRoom(self, roomObj):
        self._roomObj = roomObj

    def getRoom(self):
        return(self._roomObj)

    def removeRoom(self):
        self._roomObj = None

    def getId(self):
        return(self._acctName + "/" + str(self.getName()))

    def equip(self, objObj):
        # Deal with currently equipped item
        equippedObj = getattr(self, objObj.getEquippedSlotName())
        if equippedObj is None:            # Nothing is currently equipped
            pass
        elif equippedObj == objObj:        # desired object is already in use
            return(True)
        elif objObj is not None:           # wearing some other item
            self.unEquip(objObj)  # Pass object so we know which slot to vacate

        slotName = objObj.getEquippedSlotName()
        if slotName:
            setattr(self, slotName, objObj)
            self.setAc()
            return(True)
        return(False)

    def unEquip(self, objObj):
        if objObj.isEquippable():
            setattr(self, objObj.getEquippedSlotName(), None)
            self.setAc()
        return(True)

    def setDataFilename(self, dfStr=''):
        ''' sets the data file name.  - Override the superclass because we
            want the account info to be in the account directory. '''

        # generate the data file name based on class and id
        try:
            id = self.getId()
        except AttributeError:
            pass

        if id and id != '':
            self._datafile = os.path.abspath(DATADIR + '/Account/' +
                                             '/' + str(id) + '.pickle')
            return(True)
        return(False)

    def setHidden(self, val=True):
        self._hidden = val

    def attemptToHide(self):
        randX = random.randint(0, 99)

        hidechance = self._level * 20 + self.dexterity

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

    def setMaxWeight(self):
        ''' Maxweight varies depending on attributes '''
        weight = 10 * max(7, int(self.strength))
        self._maxweight = weight
