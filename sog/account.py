''' Account class'''

from datetime import datetime
# import getpass
import logging
import os
import re

from character import Character
from common.attributes import AttributeHelper
from common.general import getNeverDate, dateStr
from common.storage import Storage
from common.paths import DATADIR


class Account(Storage, AttributeHelper):
    ''' Account class'''

    attributesThatShouldntBeSaved = ['svrObj']

    def __init__(self, svrObj=None):
        self.svrObj = svrObj

        self.email = ''
        self.password = ''
        self._displayName = ''
        self.characterList = []
        self._maxcharacters = 5
        self.admin = False

        self._lastLoginDate = datetime.now()
        self._creationDate = datetime.now()
        self._lastLogoutDate = getNeverDate()

        self._debugAccountStorage = False      # Turn on/off debug logging

    def __str__(self):
        return("Account " + str(self.getId()))

    def __repr__(self):
        buf = self.getInfo()
        buf += "IsAdmin: " + str(self.admin) + '\n'
        buf += "svrObj: " + str(self.svrObj) + '\n'
        return(buf)

    def login(self):
        ''' login and return the acctObj - acct created if needed '''

        if not self.svrObj.isRunning():
            # Abort if client is not connected/reachable
            return(False)

        self.getUserEmailAddress()     # prompt user for email address
        email = self.getEmail()

        if email == '' or email == 'exit' or email == 'quit':
            self.svrObj.spoolOut("Aborting...\n")
            self.logout()
            self.svrObj.terminateClientConnection()
            return(False)

        self.setDataFilename()
        if self.dataFileExists():
            if self.verifyAcctPassword():
                self.load(logStr=__class__.__name__)
                self.svrObj.spoolOut('Welcome ' + self.getDisplayName() + '\n')
                self.admin = self.adminFileExists(email)
            else:
                self.__init__(self.svrObj)  # reset with existing connection
        else:  # Prompt for new account
            prompt = ("Account for " + email + " doesn't exist\n" +
                      "Create new account? [y/N] : ")
            errMsg = ('Please enter y or n')
            accountCheck = self.svrObj.promptForInput(prompt, r'^[yYnN]$',
                                                      errMsg)
            if accountCheck.lower() == 'y':
                if self.create(email):
                    pass
                else:
                    self.svrObj.spoolOut('Account could not be created.  ' +
                                         'Aborting...\n')
                    self.__init__(self.svrObj)
                    return(False)
            else:
                self.svrObj.spoolOut("Login Aborted...\n")
                self.__init__(self.svrObj)
                return(False)

        self.setLoginDate()

        if self.isValid():
            logging.info(str(self.svrObj) + ' Account login sucessful - ' +
                         self.getEmail())
        else:
            logging.info(str(self.svrObj) + ' Account ' + self.getEmail() +
                         " is invalid")
            self.svrObj.spoolOut("Password verification failed.  This " +
                                 "transaction has been logged and will be " +
                                 "investigated.\n")
            return(False)

        if self.repairCharacterList():
            self.save(logStr=(__class__.__name__ + "(rcl)"))

        return(True)

    def logout(self):
        ''' clean up when the user is done '''
        buf = ""
        if "" == self.getEmail():
            return(True)
        self.setLogoutDate()
        buf += (self.getEmail() + " is logged out\n" +
                "Login Date:  " +
                dateStr(self.getLastLoginDate()) + "\n" +
                "Logout Date: " +
                dateStr(self.getLastLogoutDate()) + "\n" +
                self.svrObj.txtLine('=') + "\n")
        self.svrObj.spoolOut(buf)
        self.save(logStr=__class__.__name__)
        if self.svrObj:
            logging.info(str(self.svrObj) + ' Logout ' + self.getEmail())
        self.__init__(self.svrObj)
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
            self._datafile = os.path.abspath(DATADIR + '/' +
                                             self.__class__.__name__ +
                                             '/' + str(id) +
                                             '/account.pickle')
            return(True)
        return(False)

    def getUserEmailAddress(self):
        ''' Prompt user for email address and validate input '''
        prompt = "Enter email address or [enter] to quit: "
        regex = r'^[A-Za-z0-9_\-\.]+@[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+$'
        self.email = self.svrObj.promptForInput(prompt, regex,
                                                "Invalid Email address\n")
        if self.email != '':
            return(True)
        return(False)

    def setUserEmailAddress(self, address=''):
        self.email = address

    def postLoad(self):
        self.setLogoutDate()

    def create(self, email):
        self.svrObj.spoolOut("Creating new account\n")
        self.setDisplayName(self.promptForDisplayName())
        if self.getDisplayName() == '':
            return(False)
        self.password = self.promptForPassword()
        if self.password == '':
            return(False)
        if self.validatePassword(self.password):
            self.email = email
            self._maxcharacters = 5
            self._creationDate = datetime.now()
            self.setLoginDate()
            self._lastLogoutDate = self.setLogoutDate()
            self.prompt = "full"
            self.save(logStr=__class__.__name__)
            self.svrObj.spoolOut("Account created for " + self.email + '\n')
            return(True)
        return(False)

    def isValid(self):
        ''' Returns true if the class instance was created properly '''
        if hasattr(self, 'email'):
            if self.email != '':
                return(True)
            else:
                logging.warning("Account is missing email address")
        return(False)

    def getInfo(self):
        ''' Show Account Info '''
        ROW_FORMAT = "  {0:16}: {1:<30}\n"

        buf = ("Account Info:\n")
        buf += ROW_FORMAT.format("Email", self.email)
        buf += ROW_FORMAT.format("Display Name", self.getDisplayName())
        buf += ROW_FORMAT.format("Creation Date",
                                 dateStr(self._creationDate))
        buf += ROW_FORMAT.format("Last Login Date",
                                 dateStr(self.getLastLoginDate()))
        buf += ROW_FORMAT.format("Last Logout Date",
                                 dateStr(self.getLastLogoutDate()))
        buf += ROW_FORMAT.format("Number of Characters",
                                 str(len(self.characterList)) + " of " +
                                 str(self._maxcharacters))
        buf += ROW_FORMAT.format("Character List:", '')
        buf += (self.showCharacterList(indent='    '))
        return(buf)

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
        obsoleteAtt = ['maxcharacter']

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

    def promptForDisplayName(self):
        ''' prompt user for displayName '''
        errMsg = ('Invalid name, displayName must be at least 3 characters, ' +
                  'must start with\n an alphanumeric, and contain only ' +
                  'alphanumerics, spaces, underscores, and hyphens')
        displayName = self.svrObj.promptForInput('Display Name: ', r'^[A-Za-z][A-Za-z0-9_-]{2}', errMsg)  # noqa: E501
        if displayName == '':
            self.svrObj.spoolOut('Aborting...\n')
            return('')
        else:
            return(displayName)

    def promptForPassword(self, promptStr='Enter Password:'):
        ''' Prompts user for password, verifies it, and returns password '''
        while True:
            self.svrObj.spoolOut(promptStr)
            self.svrObj._sendAndReceive()
            password = self.svrObj.getInputStr()

            if re.match("^[A-Za-z0-9_-]+$", password):
                return(password)
            elif password == '':
                self.svrObj.spoolOut('Aborting...\n')
                return('')
            else:
                self.svrObj.spoolOut("Invalid password.  Try Again\n")

    def verifyAcctPassword(self, promptStr='Enter Account Password:'):
        ''' Prompt user to verify password, returns True if successful '''

        if not self.email or self.email == '':
            logging.debug("verifyAcctPassword failed.  email not defined")
            return(False)

        if self.load(['password'], logStr=__class__.__name__):
            for x in range(1, 4):
                if self.validatePassword(self.password, promptStr):
                    return(True)
                else:
                    self.svrObj.spoolOut('Password invalid for account ' +
                                         self.email + ' (attempt ' + str(x) +
                                         ' of 3).\n')
                    if x == 3:
                        logging.warning("Failed password verification for " +
                                        "account " + self.email)
        return(False)

    def validatePassword(self, loadedpassword, promptStr='Verify Password:'):
        ''' Prompt user to verify password, returns True if successful '''
        self.svrObj.spoolOut(promptStr)
        self.svrObj._sendAndReceive()
        password = self.svrObj.getInputStr()

        if password == loadedpassword:
            return(True)
        return(False)

    def repairCharacterList(self):
        ''' Fix the cases where:
            * characters in the characterList are no longer on disk '''
        charObj = None
        changed = False
        if self.svrObj.charObj:
            charObj = self.svrObj.charObj
        else:
            charObj = Character(self.svrObj, self.getId())  # temp for methods

        for cName in self.characterList:
            charObj.setName(cName)            # set the charName
            self.setDataFilename()            # set the filename
            if not self.dataFileExists():
                logging.warning(__class__.__name__ + ' - Character ' + cName +
                                ' of player ' + self.email + ' does ' +
                                ' not exist at ' + self.getDataFilename() +
                                '.  Removing character from account')
                self.characterList.remove(cName)
                changed = True
        charObj = None
        return(changed)

    def showCharacterList(self, indent=''):
        ''' return a numbered list of characters from account's char list '''
        buf = ''
        if len(self.characterList) == 0:
            buf = indent + "None\n"
        else:
            ROW_FORMAT = indent + "({1:1}) {0:40}\n"
            for characterName, num in enumerate(self.characterList, start=1):
                buf += ROW_FORMAT.format(str(num), characterName)
        return(buf)

    def setPromptSize(self, size):
        ''' change the prompt verbosity '''
        if size == 'full' or size == 'brief':
            self.prompt = size
        elif size == '':
            # if promptStr is blank, toggle between the prompts
            if self.prompt == 'full':
                self.prompt = 'brief'
            else:
                self.prompt = 'full'
        return(None)

    def getPromptSize(self):
        ''' get the prompt size. '''
        try:
            return(self.prompt)
        except AttributeError:
            # In some cases, this gets called before the account is loaded
            pass
        return('full')

    def addCharacterToAccount(self, characterName):
        if characterName not in self.characterList:
            self.characterList.append(characterName)
            self.save(logStr=__class__.__name__)

    def removeCharacterFromAccount(self, characterName):
        if characterName in self.characterList:
            self.characterList.remove(characterName)
            self.save(logStr=__class__.__name__)
        else:
            logging.warning("Could not remove character " + characterName +
                            " from account " + self.getId())

    def getMaxNumOfCharacters(self):
        return(self._maxcharacters)

    def getCharacterList(self):
        return(self.characterList)

    def getDisplayName(self):
        return(self._displayName)

    def setDisplayName(self, nameStr):
        self._displayName = str(nameStr)

    def getLastLoginDate(self):
        return(self._lastLoginDate)

    def getLastLogoutDate(self):
        return(self._lastLogoutDate)

    def getName(self):
        return(str(self._displayName))

    def getEmail(self):
        return(self.email)

    def getId(self):
        return(self.email)

    def isAdmin(self):
        if (self.admin):
            return(True)
        return(False)

    def setLoginDate(self):
        self._lastLoginDate = datetime.now()

    def setLogoutDate(self):
        self._lastLogoutDate = datetime.now()

    def adminFileExists(self, id=''):
        ''' returns True if a admin file exists in account directory) '''
        if id == '':
            id = str(self.getId())
        if os.path.exists(os.path.abspath(DATADIR + "/account/" + id +
                                          '/isAdmin.txt')):
            return(True)
        return(False)

    def getCharactersOnDisk(self, id=''):
        ''' returns a list of characters based on the files on disk
            used when repairing an account which is missing it's charList '''
        charList = []
        if id == '':
            id = str(self.getId())
        mypath = os.path.abspath(DATADIR + "/account/" + id)
        for f in os.listdir(mypath):
            if os.path.isfile(os.path.join(mypath, f)):
                [charName, junk] = f.split('.')
                charList.append(charName)
        return(charList)

    def characterNameIsUnique(self, name):
        ''' Return true if the name does not match a character file on disk
            * walks the account tree checking to see if a file matching the
              character name exists '''
        filename = name + '.pickle'
        for dirpath, dirnames, files in os.walk(DATADIR + "/account"):
            for name in files:
                if name == filename:
                    return(False)
        return(True)
