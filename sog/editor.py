#!/usr/bin/env python
''' SoG Editor
  * Offline editing of accounts, rooms, creatures, and characters
'''
import colorama
# import pprint
import random
import re
import sys

# from account import Account
from character import Character
from creature import Creature
from common.attributes import AttributeHelper
from common.ioLib import LocalIo
from common.paths import LOGDIR
from common.storage import getNextUnusedFileNumber
from common.general import isIntStr, logger
# from object import Portal, Door
# from object import Armor, Weapon, Shield, Container, Key
# from object import Card, Scroll, Potion, Wand, Teleport, Ring, Necklace
# from object import Coins, Treasure
from object import isObjectFactoryType, ObjectFactory, ObjFactoryTypes
from room import isRoomFactoryType, RoomFactory, RoomFactoryTypes


class Editor(LocalIo, AttributeHelper):

    def __init__(self):
        self._running = True
        super().__init__()
        self._instanceDebug = True

        self._customCmdDict = {0: [], 1: [], 2: [], 3: [], 4: [],
                               5: [], 6: [], 7: [], 8: [], 9: []}

        self._cmdHistory = []

    def processCommand(self, inputStr):
        ''' Process the editor commands '''

        cmdargs = inputStr.split(' ')
        cmd = cmdargs[0]

        if cmd == "exit" or cmd == "quit" or cmd == "q":
            self.stop()
            return(False)
        if cmd == "help":
            for obj in RoomFactoryTypes + ObjFactoryTypes:
                print(obj + " [num] - edit " + obj)
            # print("account - edit account")
            print("character - edit character")
            print("creature - edit creature")
            print('------------------------')
            print("custom - set up custom functions to assist in editing")
            print("history - view the last 20 commands")
            print("quit - quit editor")
        elif cmd == "account":
            print("Not implemented")
        elif cmd == "list":
            targetStr, startNum, endNum = self.parseListArgs(cmdargs)
            if targetStr != '':
                self.showList(targetStr, startNum, endNum)
        elif cmd == 'custom':
            self.editCustomFunctions(cmdargs)
        elif cmd == 'history':
            print("Command History:\n  " + "\n  ".join(self._cmdHistory))
        else:
            if not self.initAndEdit(cmdargs):
                print("Command failed")
        return(True)

    def parseListArgs(self, cmdargs):   # noqa: C901
        ''' parses the arguments for the list command '''
        if len(cmdargs) < 3:
            print("Usage: list <type> <number-range | all>\n")
            print("  For example: list creature 1-5")
            if len(cmdargs) == 2:
                nextnum = getNextUnusedFileNumber(cmdargs[1])
                if nextnum:
                    print("\nLast used number for " + str(cmdargs[1]) +
                          " is " + str(nextnum - 1))
            return('', 0, 0)
        targetStr = cmdargs[1]
        if targetStr.lower() != 'coins':
            targetStr = targetStr.rstrip('s')
        listNums = str.rstrip(cmdargs[2], '\n')

        startNum = 0
        endNum = 0
        if listNums == 'all':
            startNum = 1
        elif '-' in listNums:
            nums = listNums.split("-")
            if len(nums) == 2:
                if isIntStr(nums[0]):
                    startNum = int(nums[0])
                if isIntStr(nums[1]):
                    endNum = int(nums[1]) + 1

        if startNum <= 0:
            print("Invalid Range")
            return('', 0, 0)

        lastUnused = getNextUnusedFileNumber(targetStr)
        if endNum <= 0 or endNum > lastUnused:
            endNum = lastUnused

        return(targetStr, startNum, endNum)

    def printError(self, msg):
        print(colorama.Fore.RED + msg + colorama.Fore.RESET)

    def initAndEdit(self, cmdargs):
        ''' load the object and kick off the editor '''

        itemId = self.findId(cmdargs)
        if isinstance(itemId, int):
            if itemId <= 0:
                print("Invalid input")
                return(None)

        secondId = ''
        if cmdargs[0].lower() == 'character':
            prompt = ("Enter the Account email address for character " +
                      str(itemId) + ": ")
            secondId = self.promptForInput(prompt)

        itemObj = self.getItemObj(cmdargs[0], itemId, secondId)

        if itemObj is None:
            return(False)

        changeFlag = False

        if hasattr(itemObj, '_isNew'):
            delattr(itemObj, '_isNew')
            print("WARN:", str(cmdargs[0]), str(itemId),
                  "doesn't exist - Creating")
            self.wizard(cmdargs[0], itemObj)
            changeFlag = True

        if self.editRaw(cmdargs[0], itemObj, changeFlag):
            return(True)
        return(False)

    def findId(self, cmdargs):
        ''' Return object id. Get it from previous command, or prompt '''
        if len(cmdargs) > 1:
            ''' The id is provided along with the command '''
            if re.match("^[0-9]+$", cmdargs[1]):
                return(int(cmdargs[1]))
            if cmdargs[0].lower() == "character":
                return(str(cmdargs[1]))
        else:
            ''' Prompt for the ID '''
            if cmdargs[0].lower() == "character":
                ''' prompt for string, since Character Ids are strings '''
                prompt = "Enter " + cmdargs[0] + " id: "
                idStr = self.promptForInput(prompt)
                return(idStr)
            else:
                ''' prompt for number '''
                prompt = "Enter " + cmdargs[0] + " number"
                nextnum = getNextUnusedFileNumber(cmdargs[0])
                if nextnum != 0:
                    prompt += " (next unused = " + str(nextnum) + ")"
                prompt += ": "
                num = self.promptForNumberInput(prompt)
                return(int(num))
        return(0)

    def getItemObj(self, itemStr, id1, id2=''):
        ''' given return an existing object, or None if it doesn't exist '''
        if isRoomFactoryType(itemStr.lower()):
            itemObj = RoomFactory(itemStr, id1)
        elif itemStr.lower() == 'character':
            itemObj = Character(None, id2)
            itemObj.setName(id1)
        elif itemStr.lower() == 'creature':
            itemObj = Creature(id1)
        elif isObjectFactoryType(itemStr.lower()):
            itemObj = ObjectFactory(itemStr, id1)
        else:
            print("Can not determine object type.")
            return(None)

        if not itemObj:
            msg = "Object doesn't exist.  Aborting..."
            print(msg + '\n')
            logger.warning(msg)
            return(None)
        if not itemObj.load():
            if itemObj.getId() == 0:
                msg = "Couldn't load object and ID is 0.  Aborting..."
                print(msg + '\n')
                logger.warning(msg)
                return(None)
            else:
                itemObj._isNew = True
        return(itemObj)

    def getAttributeType(self, attValue):
        attType = str(type(attValue))
        attType = re.sub(r"^<class '(.*)'>.*", r'\1', attType)
        return(attType)

    def showCustomFunctions(self):
        C_ROW_FORMAT = "  ({0:3}) {1:70}\n"
        shown = False
        for custKey in self._customCmdDict.keys():
            if len(self._customCmdDict[custKey]) > 0:
                print(C_ROW_FORMAT.format(str(custKey),
                                          str(self._customCmdDict[custKey])))
                shown = True
        if not shown:
            print("  No custom functions defined")

    def editCustomFunctions(self, cmdargs):
        ccBanner = (colorama.Fore.CYAN + '===== Custom functions =====' +
                    colorama.Fore.RESET)
        ccMsg = ("Define one or more custom reusable functions that" +
                 "you can later\napply to multiple objects.\n")
        ccExMsg = ("Each custom function needs to be a list of tuples\n" +
                   "For example:\n" +
                   '  [("_weight", 20), ("_value", 30)]\n' +
                   "  [('_itemCatalog', ['Weapon/1','Armor/1']), " +
                   "(_numOfItemsCarried, [0,1,2])]\n")
        ccAppMsg = ("Use the the following to apply your custom " +
                    "function:\n" + colorama.Fore.YELLOW +
                    "  'custom apply <#>'" + colorama.Fore.RESET)
        ccListMsg = ("Use the following to view all of the saved custom " +
                     "functions:\n" + colorama.Fore.YELLOW +
                     "  'custom list'" + colorama.Fore.RESET)
        ccDefMsg = ("Use the following to add or replace a custom " +
                    "function:\n" + colorama.Fore.YELLOW +
                    "  'custom define <#>'" + colorama.Fore.RESET)
        if len(cmdargs) == 3 and isIntStr(cmdargs[2]):
            print('\n'.join([ccBanner, ccMsg, ccExMsg]))
            num = cmdargs[2]
            customData = input("Enter custom function #" + str(num) + ": ")
            if self.validateCustomData(customData):
                self._customCmdDict[num] = self.importCustomData(customData)
                print("Saved as custom function #" + str(num) + ".")
                print(ccAppMsg)
        elif len(cmdargs) == 2 and cmdargs[1] == 'list':
            print(ccBanner)
            self.showCustomFunctions()
            print(ccAppMsg)
        else:
            print('\n'.join([ccBanner, ccListMsg, ccDefMsg, ccAppMsg]))

        return (None)

    def importCustomData(self, inStr):
        ''' returns the evaled result of the input string '''
        inList = eval(inStr)

        if not isinstance(inList, list):
            self.printError("Error: custom data is not a list")
            return([])

        return(inList)

    def validateCustomData(self, data):
        if not data:
            return(False)

        # I hate to use eval, but this is the editor running locally.
        dataList = self.importCustomData(data)

        if len(dataList) < 1:
            self.printError("Error: custom data list is empty")
            return(False)

        try:
            # process tuples to make sure that they can be unpacked
            for onekey, oneval in dataList:
                pass
        except ValueError:
            self.printError("Error: custom data tuple is not valid")
            return(False)

        return(True)

    def changeListValue(self, obj, name, type, value):          # noqa: C901
        changed = False
        stop = False
        while not stop:
            attObj = getattr(obj, name)
            attType = 'unknown'
            if len(attObj) > 0:
                attType = self.getAttributeType(attObj[0])
            prompt = "Editing list " + name + "(type: " + attType + "):\n"
            prompt += "  Old Value: " + str(value) + '\n'
            prompt += "  * To append a value, enter \'a\' <value>\n"
            prompt += '  * To remove a value, enter \'r\' <value>\n'
            prompt += '  * To clear all values, enter \'clear\'\n'
            prompt += '  * Press [enter] to leave unchanged\n'
            prompt += '  * Enter \'q\' to stop editing this list\n'
            prompt += "List command for " + name + ": "
            cmdargs = input(prompt).split(' ', 1)
            if cmdargs[0] == '':
                pass
            elif (cmdargs[0] == 'done' or cmdargs[0][0] == 's'
                  or cmdargs[0][0] == 'q'):
                stop = True
            elif cmdargs[0] == 'clear':
                if len(attObj) > 0:
                    setattr(obj, name, [])
                    changed = True
            elif len(cmdargs) > 1 and cmdargs[0][0] == "a":
                rVal = cmdargs[1]
                if cmdargs[0] == "ai":
                    rVal = int(rVal)
                if len(attObj) > 0 and isinstance(attObj[0], int):
                    if isIntStr(rVal):
                        rVal = int(rVal)  # handle lists of ints
                if name == '_permanentList':
                    if '/' not in rVal:
                        self.printError("PermanentList must contain a slash." +
                                        "  Aborting.")
                        continue
                attObj.append(rVal)
                setattr(obj, name, attObj)
                changed = True
            elif len(cmdargs) > 1 and (cmdargs[0][0] == "r" or
                                       cmdargs[0][0] == "d"):
                rVal = cmdargs[1]
                if len(attObj) > 0 and isinstance(attObj[0], int):
                    if isIntStr(rVal):
                        rVal = int(rVal)  # handle lists of ints
                if rVal in attObj:
                    attObj.remove(rVal)
                    setattr(obj, name, attObj)
                    changed = True
            else:
                self.printError("List command unsupported")
            value = getattr(obj, name)
        return(changed)

    def promptForNewValue(self, obj, attName, attType, attValue):
        ''' prompt for new values '''
        helpStr = obj.getWizHelp(attName)
        if helpStr != '':
            print(attName, "-", helpStr)
        print("  Old Value: " + str(attValue))
        print("Enter the new " + attType + " value for " + colorama.Fore.CYAN +
              str(attName) + colorama.Fore.RESET + " or [enter] to leave " +
              "unchanged: ", end='')
        newval = input('')
        if newval == '':
            return(attValue)   # no change
        elif newval == "''" or newval == '""':
            return('')         # empty str
        else:
            return(newval)

    def changeValue(self, obj, name, type, value):
        changed = False
        ''' Alter instance, given the object, field name, and field type
            return True/False depending on whether the instance was changed '''
        if (type) == "bool":
            if getattr(obj, name) is False:
                newval = True
            elif getattr(obj, name) is True:
                newval = False
            setattr(obj, name, newval)
            changed = True
        elif (type) == "int":
            newval = self.promptForNewValue(obj, name, type, value)
            if isIntStr(str(newval)):
                setattr(obj, name, int(newval))
                changed = True
            elif (isRoomFactoryType(obj.getType())):
                setattr(obj, name, newval)
                changed = True
                # self.printError("WARN: Non numeric Room IDs are only " +
                #                 "accessible by doors/portals.  " +
                #                 "Resetting to 0.")
                # if getattr(obj, name) != 0:
                #     setattr(obj, name, 0)
                #     changed = True
            else:
                self.printError("Value" + newval +
                                "is not an int.  Skipping...")
        elif (type) == "str":
            newval = self.promptForNewValue(obj, name, type, value)
            setattr(obj, name, newval)
            changed = True
        elif (type) == "list":
            changed = self.changeListValue(obj, name, type, value)
        else:
            self.printError("Editing of", type, "types is not supported yet.")
        return(changed)

    def setDefaults(self, obj, attName):                        # C901
        ''' Some wizard field values may trigger us to set the starting values
            of other fields '''
        attValue = getattr(obj, attName)
        objType = obj.getType()
        if objType.lower() == 'creature':
            if attName == '_level':
                print("Setting defaults for creature level")
                for oneAtt in obj._levelDefaultsDict[attValue].keys():
                    newval = obj._levelDefaultsDict[attValue][oneAtt]
                    if oneAtt in ['_exp', '_maxhp']:
                        if random.randint(0, 1) == 1:
                            percent = 1 + random.randint(0, 9) / 100
                        else:
                            percent = 1 - random.randint(0, 9) / 100
                        newval = int(newval * percent)
                    print("defaults: " + oneAtt + " = " + str(newval))
                    setattr(obj, oneAtt, newval)
            elif attName == '_maxhp':
                print("Setting defaults for _hp to be equal to _maxhp")
                setattr(obj, '_hp', attValue)
            elif attName == '_parleyAction':
                print("Setting defaults for _parleyTxt")
                try:
                    newval = obj._parleyDefaultsDict[obj._parleyAction]
                except KeyError:
                    newval = obj._parleyDefaultsDict['None']
                print("defaults: " + '_parleyTxt = ' + str(newval))
                setattr(obj, '_parleyTxt', newval)
        elif attName == '_maxCharges':
            print("Setting defaults for _charges to be equal to _maxcharges")
            setattr(obj, '_charges', attValue)

    def wizard(self, objName, obj):
        ''' Prompt for field input '''
        changedSinceLastSave = False
        wizFields = obj.getWizFields()
        if len(wizFields) > 0:
            print(colorama.Fore.CYAN + '===== ' + objName.capitalize() +
                  " Wizard -- Editing " +
                  objName.capitalize() + " " + str(obj.getId()) + " =====" +
                  colorama.Fore.RESET)
            if objName.lower() == "door":
                print("Doors are single objects that have a " +
                      "corresponding door in the room to which they point.  " +
                      "Thus, doors should always be created in pairs")
            for attName in wizFields:
                if attName in vars(obj):
                    # Change the given fields immediately
                    attValue = getattr(obj, attName)
                    attType = self.getAttributeType(attValue)
                    if self.changeValue(obj, attName, attType, attValue):
                        changedSinceLastSave = True
                    self.setDefaults(obj, attName)
        return(changedSinceLastSave)

    def customSort(self, s):
        ''' returns the key for sorting '''
        if re.match('.*Id', s) or s == '_roomNum':
            return('!' + s)
        elif re.match('_name', s):
            return("\"" + s)
        elif s in ['_desc', '_shortDesc', '_longDesc']:
            return("\'" + s)
        elif re.match('^_', s):
            return('}' + s)
        return(s)

    def editRaw(self, objName, obj, changedSinceLastSave=False):   # noqa C901
        ROW_FORMAT = "({0:3}) {1:25s}({2:4s}): {3}\n"
        logger.info("Editing " + objName.capitalize() + " -- id = " +
                    obj.describe())
        obj.fixAttributes()
        while True:
            buf = (colorama.Fore.CYAN + '===== Editing ' +
                   objName.capitalize() + " " + str(obj.getId()) +
                   ' =====\n' + colorama.Fore.RESET)

            instanceAttributes = vars(obj)

            varDict = {}
            attributeList = sorted(instanceAttributes, key=self.customSort)
            bufCount = 0
            for num, attName in enumerate(attributeList):
                if attName in (["client", "gameObj", "acctObj", "_datafile"] +
                               obj.obsoleteAttributes +
                               obj.attributesThatShouldntBeSaved):
                    pass  # don't want these
                else:
                    attValue = getattr(obj, attName)
                    attType = self.getAttributeType(attValue)

                    varDict[num] = {}
                    varDict[num]['name'] = attName
                    varDict[num]['type'] = attType
                    varDict[num]['value'] = attValue
                    if bufCount % 5 == 0:
                        color = colorama.Fore.YELLOW
                    else:
                        color = colorama.Fore.RESET

                    buf += (color + ROW_FORMAT.format(num, attName,
                            attType, attValue))
                    bufCount += 1
            print(buf)
            print('Commands: [s]ave, [q]uit, [wiz]ard, [cust]om')
            inStr = input("Enter command or attribute to edit: ")
            cmdargs = inStr.split(' ')
            if ((inStr == 's' or inStr == 'sq' or
                 inStr == 'wq' or inStr == "save")):
                # save edited item
                if str(obj.getId()) == '' or str(obj.getId()) == "0":
                    print("ERROR", objName, "could not be saved.  Bad Id:",
                          obj.getId())
                elif obj.save():
                    print(objName.capitalize(), obj.getId(), "saved")
                    logger.info(objName + " changes saved")
                    changedSinceLastSave = False   # reset flag after save
                else:
                    print("ERROR", objName, "could not be saved")
            if ((inStr == 'q' or inStr == 'sq' or
                 inStr == 'wq' or inStr == '')):
                # quit
                objDescription = objName + " " + str(obj.getId())
                objDesc2 = obj.describe(article='')
                if objDesc2.lower() != objDescription.lower():
                    objDescription += ' (' + objDesc2 + ')'
                if changedSinceLastSave:
                    # warn if user is quitting with unsaved changes
                    verifyStr = input("You have made changes since your " +
                                      "last save.\nAre you sure that " +
                                      "you want to abandon these changes" +
                                      " and quit [y/N]: ")
                    if verifyStr == "y":
                        print("Changes to " + objDescription + " abandoned")
                        logger.info(objName + " changes to " + objDescription +
                                    " abandoned")
                        break
                else:
                    print("Done editing " + objDescription)
                    break
            if inStr == "wizard" or inStr == "wiz":
                self.wizard(objName, obj)
                changedSinceLastSave = True
            elif re.match('^d [0-9]+$', inStr):
                # delete attribute
                cmd, inNum = inStr.split(" ")
                inNum = int(inNum)
                print("Attribute " + varDict[inNum]['name'] + "deleted")
                delattr(obj, varDict[inNum]['name'])
                changedSinceLastSave = True
            elif re.match('^[0-9]+$', inStr):
                # number entry - edit the corresponding field
                inNum = int(inStr)
                try:
                    attName = varDict[inNum]['name']
                    attType = varDict[inNum]['type']
                    attValue = varDict[inNum]['value']
                    if self.changeValue(obj, attName, attType, attValue):
                        changedSinceLastSave = True
                except KeyError:
                    print("Invalid number")
            elif re.match('^_[^ ]+$', inStr):    # named entry
                try:
                    attValue = getattr(obj, inStr)
                except AttributeError:
                    print("Can't edit that by name")
                    return(False)
                attName = inStr
                attType = self.getAttributeType(attValue)
                if self.changeValue(obj, attName, attType, attValue):
                    changedSinceLastSave = True
            elif re.match('^custom apply', inStr):
                if len(cmdargs) == 3 and isIntStr(cmdargs[2]):
                    num = cmdargs[2]
                    for item, val in self._customCmdDict[num]:
                        setattr(obj, item, val)
            elif re.match('^cust', inStr):
                self.editCustomFunctions(cmdargs)
        return(True)

    def fixList(self, targetStr, startNum=0, endNum=0):
        ''' Fixes a set of stored objects without confirmation
            * Uses the object's fixAttributes method '''
        for itemNum in range(startNum, endNum):
            obj = self.getItemObj(targetStr, itemNum)
            if obj is None:
                continue
            if hasattr(obj, '_isNew'):
                continue
            obj.fixAttributes()
            obj.save()

    def showList(self, targetStr, startNum=0, endNum=0):
        ''' Display a list of objects.  Show wizardAttributes '''
        ROW_FORMAT = "{0:3}:"

        fields_to_ignore = ['_article', '_pluraldesc', '_longdesc', '_desc']
        long_fields = ['_singledesc', '_shortDesc']

        headerList = ['id']
        fullList = []

        for itemNum in range(startNum, endNum):
            obj = self.getItemObj(targetStr, itemNum)
            if obj is None:
                continue
            if hasattr(obj, '_isNew'):
                continue
            dataList = [str(itemNum)]
            dataCount = 1
            for att in obj.wizardAttributes:
                if att in fields_to_ignore:
                    continue
                data = getattr(obj, att)
                if len(fullList) == 0:
                    # build format on the fly
                    if isinstance(data, int) or isinstance(data, bool):
                        ROW_FORMAT += " {" + str(dataCount) + ":7.7}"
                    elif att in long_fields:
                        ROW_FORMAT += " {" + str(dataCount) + ":20.20}"
                    else:
                        ROW_FORMAT += " {" + str(dataCount) + ":10.10}"
                    dataCount += 1
                    # store att names for use as a header
                    headerList.append(str(att))
                dataList.append(str(data))
            fullList.append(dataList)

        ROW_FORMAT += "\n"

        if len(fullList) != 0:
            print(colorama.Fore.CYAN + ROW_FORMAT.format(*headerList) +
                  colorama.Fore.RESET)
            for num, dataList in enumerate(fullList):
                if num % 3 == 0:
                    color = colorama.Fore.YELLOW
                else:
                    color = colorama.Fore.RESET
                print(color + ROW_FORMAT.format(*dataList))

    def isRunning(self):
        if self._running:
            return(True)
        return(False)

    def start(self):
        ''' Start the editor '''
        logger.info("Editor Started - " + sys.argv[0])
        print("Logs: " + LOGDIR + '\\editor.log')

        colorama.init()

        while self.isRunning():
            prompt = "(Editor)"
            inputStr = input(prompt)
            self.processCommand(inputStr)
            self._cmdHistory.append(inputStr)
            if len(self._cmdHistory) > 20:
                self._cmdHistory.pop(0)

        colorama.deinit()

    def stop(self):
        self._running = False


# ----------------#
editor = Editor()
editor.start()
print("Done")
