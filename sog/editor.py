#!/usr/bin/env python
''' SoG Editor
  * Offline editing of accounts, rooms, creatures, and characters
'''
import logging
from pathlib import Path
# import pprint
import random
import re
import sys

# from account import Account
from character import Character
from creature import Creature
from common.attributes import AttributeHelper
from common.ioLib import IoLib
from common.paths import LOGDIR
from common.storage import getNextUnusedFileNumber
from common.general import isIntStr
# from object import Portal, Door
# from object import Armor, Weapon, Shield, Container, Key
# from object import Card, Scroll, Potion, Wand, Teleport, Ring, Necklace
# from object import Coins, Treasure
from object import getObjectFactoryTypes, ObjectFactory
from room import RoomFactory


class Editor(IoLib, AttributeHelper):

    def __init__(self):
        self._running = True
        super().__init__()

    def processCommand(self, inputStr):
        ''' Process the editor commands '''

        cmdargs = inputStr.split(' ')
        cmd = cmdargs[0]

        if cmd == "exit" or cmd == "quit" or cmd == "q":
            self.stop()
            return(False)
        if cmd == "help":
            print("room [num] - edit room")
            print("shop [num] - edit shop")
            print("<object> [num] - edit <object>")
            # print("account - edit account")
            print("character - edit character")
            print("creature - edit creature")
            print("quit - quit editor")
        elif cmd == "account":
            print("Not implemented")
        elif cmd == "list":
            if len(cmdargs) < 3:
                print("Usage: list <type> <number-range | all>\n")
                print("  For example: list creature all")
                return(False)
            targetStr = cmdargs[1]
            listNums = str.rstrip(cmdargs[2], '\n')
            self.showList(targetStr, listNums)
        else:
            if not self.initAndEdit(cmdargs):
                print("Command failed")
        return(True)

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

        changeFlag = False

        if hasattr(itemObj, '_isNew'):
            delattr(itemObj, '_isNew')
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
        if itemStr == 'room' or itemStr == 'shop':
            itemObj = RoomFactory(itemStr, id1)
        elif itemStr.lower() == 'character':
            itemObj = Character(None, id2)
            itemObj.setName(id1)
        elif itemStr.lower() == 'creature':
            itemObj = Creature(id1)
        elif itemStr.lower() in getObjectFactoryTypes():
            itemObj = ObjectFactory(itemStr, id1)
        else:
            print("Can not determine object type.")
            return(None)

        if not itemObj:
            msg = "Object doesn't exist.  Aborting..."
            print(msg + '\n')
            logging.warning(msg)
            return(None)
        if not itemObj.load():
            if itemObj.getId() == 0:
                msg = "Couldn't load object and ID is 0.  Aborting..."
                print(msg + '\n')
                logging.warning(msg)
                return(None)
            else:
                print("WARN:", itemStr, id1, "doesn't exist - Creating")
                itemObj._isNew = True
        return(itemObj)

    def getAttributeType(self, attValue):
        attType = str(type(attValue))
        attType = re.sub(r"^<class '(.*)'>.*", r'\1', attType)
        return(attType)

    def changeListValue(self, obj, name, type, value):
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
            prompt += '  * Enter \'done\' to stop editing this list\n'
            prompt += "List command for " + name + ": "
            cmdargs = input(prompt).split(' ')
            if cmdargs[0] == '':
                pass
            elif cmdargs[0] == 'done' or cmdargs[0] == 'stop':
                stop = True
            elif cmdargs[0] == 'clear':
                if len(attObj) > 0:
                    setattr(obj, name, [])
                    changed = True
            elif len(cmdargs) > 1 and cmdargs[0] == "a":
                attObj.append(cmdargs[1])
                setattr(obj, name, attObj)
                changed = True
            elif len(cmdargs) > 1 and (cmdargs[0] == "r" or cmdargs[0] == "d"):
                if cmdargs[1] in attObj:
                    attObj.remove(cmdargs[1])
                    setattr(obj, name, attObj)
                changed = True
            else:
                print("List command unsupported")
        return(changed)

    def promptForNewValue(self, obj, attName, attType, attValue):
        ''' prompt for new values '''
        helpStr = obj.getWizHelp(attName)
        if helpStr != '':
            print(attName, "-", helpStr)
        print("  Old Value: " + str(attValue))
        buf = ("Enter the new " + attType + " value for " + str(attName) +
               " or [enter] " + "to leave unchanged: ")
        newval = input(buf)
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
            if re.match('^[0-9]+$', str(newval)):
                setattr(obj, name, int(newval))
                changed = True
            else:
                print("Value" + newval + "is not an int.  Skipping...")
        elif (type) == "str":
            newval = self.promptForNewValue(obj, name, type, value)
            setattr(obj, name, newval)
            changed = True
        elif (type) == "list":
            changed = self.changeListValue(obj, name, type, value)
        else:
            print("Editing of", type,
                  "types is not supported yet.")
        return(changed)

    def setDefaults(self, obj, attName):
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
        wizFields = obj.getWizFields()
        if len(wizFields) > 0:
            print('===== ' + objName.capitalize() + " Wizard -- Editing " +
                  objName.capitalize() + " " + str(obj.getId()) + " =====")
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
                        pass
                    self.setDefaults(obj, attName)
        return(True)

    def editRaw(self, objName, obj, changedSinceLastSave=False):   # noqa C901
        ROW_FORMAT = "({0:3}) {1:25s}({2:4s}): {3}\n"
        logging.info("Editing " + objName.capitalize())
        self.fixAttributes()
        while True:
            buf = ('===== Editing ' + objName.capitalize() + " " +
                   str(obj.getId()) + ' =====\n')

            instanceAttributes = vars(obj)

            varDict = {}
            for num, attName in enumerate(instanceAttributes):
                if attName in ["svrObj", "gameObj", "acctObj"]:
                    pass  # don't want these
                else:
                    attValue = getattr(obj, attName)
                    attType = self.getAttributeType(attValue)

                    varDict[num] = {}
                    varDict[num]['name'] = attName
                    varDict[num]['type'] = attType
                    varDict[num]['value'] = attValue
                    buf += (ROW_FORMAT.format(num, attName,
                            attType, attValue))
            print(buf)
            inStr = input("Enter [s]ave, [q]uit, or a number to edit: ")
            if ((inStr == 's' or inStr == 'sq' or
                 inStr == 'wq' or inStr == "save")):
                # save edited item
                if str(obj.getId()) == '' or str(obj.getId()) == "0":
                    print("ERROR", objName, "could not be saved.  Bad Id:",
                          obj.getId())
                elif obj.save():
                    print(objName.capitalize(), obj.getId(), "saved")
                    logging.info(objName + " changes saved")
                    changedSinceLastSave = False   # reset flag after save
                else:
                    print("ERROR", objName, "could not be saved")
            if ((inStr == 'q' or inStr == 'sq' or
                 inStr == 'wq' or inStr == '')):
                # quit
                if changedSinceLastSave:
                    # warn if user is quitting with unsaved changes
                    verifyStr = input("You have made changes since your " +
                                      "last save.\nAre you sure that " +
                                      "you want to abandon these changes" +
                                      " and quit [y/N]: ")
                    if verifyStr == "y":
                        print("Changes abandoned")
                        logging.info(objName + " changes abandoned")
                        break
                else:
                    break

            if re.match('^d [0-9]+$', inStr):
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
                    self.changeValue(obj, attName, attType, attValue)
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
                self.changeValue(obj, attName, attType, attValue)
        return(True)

    def showList(self, targetStr, listNums=''):
        ''' Display a list of objects.  Show wizardAttributes '''
        ROW_FORMAT = "{0:3}:"

        fields_to_ignore = ['_article', '_pluraldesc', '_longdesc', '_desc']

        headerList = ['id']
        fullList = []

        startNum = 0
        endNum = 0
        if listNums == 'all':
            startNum = 1
            endNum = getNextUnusedFileNumber(targetStr)
        else:
            if '-' in listNums:
                nums = listNums.split("-")
                if len(nums) == 2:
                    if isIntStr(nums[0]):
                        startNum = int(nums[0])
                    if isIntStr(nums[1]):
                        endNum = int(nums[1]) + 1

        if not startNum or not endNum:
            print("Invalid Range")

        for itemNum in range(startNum, endNum):
            obj = self.getItemObj(targetStr, itemNum)
            if obj is None:
                continue
            dataList = [str(itemNum)]
            dataCount = 1
            for att in obj.wizardAttributes:
                data = getattr(obj, att)
                if att in fields_to_ignore:
                    continue
                if len(fullList) == 0:
                    # build format on the fly
                    if isinstance(data, int) or isinstance(data, bool):
                        ROW_FORMAT += " {" + str(dataCount) + ":7.7}"
                    else:
                        ROW_FORMAT += " {" + str(dataCount) + ":15.15}"
                    dataCount += 1
                    # store att names for use as a header
                    headerList.append(str(att))
                dataList.append(str(data))
            fullList.append(dataList)

        ROW_FORMAT += "\n"

        if len(fullList) != 0:
            print(ROW_FORMAT.format(*headerList))
            for dataList in fullList:
                print(ROW_FORMAT.format(*dataList))

    def isRunning(self):
        if self._running:
            return(True)
        return(False)

    def start(self):
        ''' Start the editor '''
        # Set up logging
        logpath = Path(LOGDIR)
        logpath.mkdir(parents=True, exist_ok=True)
        FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
        logging.basicConfig(filename=(LOGDIR + '/editor.log'),
                            level=logging.DEBUG,
                            format=FORMAT, datefmt='%m/%d/%y %H:%M:%S')
        logging.info("Editor Started - " + sys.argv[0])
        print("Logs: " + LOGDIR + '\\editor.log')

        while self.isRunning():
            prompt = "(Editor)"
            inputStr = input(prompt)
            self.processCommand(inputStr)

    def stop(self):
        self._running = False


# ----------------#
editor = Editor()
editor.start()
print("Done")
