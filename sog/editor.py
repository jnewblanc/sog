#!/usr/bin/env python
''' SoG Editor
  * Offline editing of accounts, rooms, creatures, and characters
'''
import logging
from pathlib import Path
import re
import sys

# from account import Account
from character import Character
# from creature import Creature
from common.ioLib import IoLib
from common.paths import LOGDIR
from common.storage import getNextUnusedFileNumber
# from object import Portal, Door
# from object import Armor, Weapon, Shield, Container, Key
# from object import Card, Scroll, Potion, Wand, Teleport, Ring, Necklace
# from object import Coins, Treasure
from object import getObjectFactoryTypes, ObjectFactory
from room import RoomFactory


class Editor(IoLib):

    def __init__(self):
        self._running = True
        super().__init__()

    def getAttributeType(self, attValue):
        attType = str(type(attValue))
        attType = re.sub(r"^<class '(.*)'>.*", r'\1', attType)
        return(attType)

    def changeListValue(self, obj, name, type):
        changed = False
        attObj = getattr(obj, name)
        attType = 'unknown'
        if len(attObj) > 0:
            attType = self.getAttributeType(attObj[0])
        prompt = "Editing list " + name + "(type: " + attType + "):\n"
        prompt += "To append a value, enter \'a <value>\'\n"
        prompt += 'To remove a value, enter \'r <value>\'\n'
        prompt += 'To clear all values, enter \'clear\'\n'
        prompt += "List command for " + name + ": "
        cmdargs = input(prompt).split(' ')
        if cmdargs[0] == 'clear':
            if len(attObj) > 0:
                setattr(obj, name, [])
                changed = True
        elif len(cmdargs) > 1 and cmdargs[0] == "a":
            attObj.append(cmdargs[1])
            setattr(obj, name, attObj)
            changed = True
        elif len(cmdargs) > 1 and cmdargs[0] == "r":
            attObj.remove(cmdargs[1])
            setattr(obj, name, attObj)
            changed = True
        else:
            print("List command unsupported")
        return(changed)

    def changeValue(self, obj, name, type):
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
            newval = input("Enter " + type + " value for " + name + ": ")
            if re.match('^[0-9]+$', str(newval)):
                setattr(obj, name, int(newval))
                changed = True
            else:
                print("Value" + newval + "is not an int.  Skipping...")
        elif (type) == "str":
            newval = input("Enter " + type + " value for " + name + ": ")
            setattr(obj, name, newval)
            changed = True
        elif (type) == "list":
            changed = self.changeListValue(obj, name, type)
        else:
            print("Editing of", type,
                  "types is not supported yet.")
        return(changed)

    def wizard(self, objName, obj):
        ''' Prompt for field input '''
        ROW_FORMAT = "({0:3}) {1:25s}({2:4s}): {3}\n"
        wizFields = obj.getWizFields()
        if len(wizFields) > 0:
            print('===== ' + objName.capitalize() + " Wizard -- Editing " +
                  objName.capitalize() + " " + str(obj.getId()) + " =====")
            if objName.lower() == "door":
                print("Doors are single objects that have a " +
                      "corresponding door in the room to which they point.  " +
                      "Thus, doors should always be created in pairs")
            for attributeName in wizFields:
                if attributeName in vars(obj):
                    # Change the given fields immediately
                    attributeValue = getattr(obj, attributeName)
                    attributeType = self.getAttributeType(attributeValue)
                    print(ROW_FORMAT.format('OLD', attributeName,
                          attributeType, attributeValue), end='')
                    if self.changeValue(obj, attributeName, attributeType):
                        pass
        return(True)

    def editRaw(self, objName, obj, changedSinceLastSave=False):   # noqa C901
        ROW_FORMAT = "({0:3}) {1:25s}({2:4s}): {3}\n"
        while True:
            buf = ('===== Editing ' + objName.capitalize() + " " +
                   str(obj.getId()) + ' =====\n')

            instanceAttributes = vars(obj)

            varDict = {}
            for num, attributeName in enumerate(instanceAttributes):
                if attributeName == "svrObj" or attributeName == "gameObj":
                    pass  # don't want these
                else:
                    attributeValue = getattr(obj, attributeName)
                    attributeType = self.getAttributeType(attributeValue)

                    varDict[num] = {}
                    varDict[num]['name'] = attributeName
                    varDict[num]['type'] = attributeType
                    varDict[num]['value'] = attributeValue
                    buf += (ROW_FORMAT.format(num, attributeName,
                            attributeType, attributeValue))
            print(buf)
            inStr = input("Enter [s]ave, [q]uit, or a number to edit: ")
            if ((inStr == 's' or inStr == 'sq' or
                 inStr == 'wq' or inStr == "save")):
                if str(obj.getId()) == '' or str(obj.getId()) == "0":
                    print("ERROR", objName, "could not be saved.  Bad Id:",
                          obj.getId())
                elif obj.save():
                    print(objName.capitalize(), obj.getId(), "saved")
                    changedSinceLastSave = False   # reset flag after save
                else:
                    print("ERROR", objName, "could not be saved")
            if ((inStr == 'q' or inStr == 'sq' or
                 inStr == 'wq' or inStr == '')):
                if changedSinceLastSave:
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
            # process results of prompt
            if re.match('^[0-9]+$', inStr):
                inNum = int(inStr)
                self.changeValue(obj, varDict[inNum]['name'],
                                 varDict[inNum]['type'])
        return(True)

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
            # print("creature - edit creature")
            print("quit - quit editor")
        elif cmd == "account":
            print("Not implemented")
        elif cmd == "creature":
            print("Not implemented")
        else:
            if not self.initAndEdit(cmdargs):
                print("Command failed")

        return(True)

    def initAndEdit(self, cmdargs):
        objId = self.findId(cmdargs)
        if isinstance(objId, int):
            if objId <= 0:
                print("Invalid input")
                return(False)

        if cmdargs[0] == 'room' or cmdargs[0] == 'shop':
            obj = RoomFactory(cmdargs[0], objId)
        elif cmdargs[0].lower() == 'character':
            prompt = ("Enter the Account email address for character " +
                      objId + ": ")
            acctName = self.promptForInput(prompt)
            obj = Character(None, acctName)
            obj.setName(objId)
        elif cmdargs[0] in getObjectFactoryTypes():
            obj = ObjectFactory(cmdargs[0], objId)
        else:
            return(False)

        changeFlag = False
        if not obj:
            msg = "Object doesn't exist.  Aborting..."
            print(msg + '\n')
            logging.warning(msg)
            return(False)
        if not obj.load():
            if obj.getId() == 0:
                msg = "Couldn't load object and ID is 0.  Aborting..."
                print(msg + '\n')
                logging.warning(msg)
                return(False)
            print("WARN:", cmdargs[0], objId, "doesn't exist - Creating")
            self.wizard(cmdargs[0], obj)
            changeFlag = True

        if self.editRaw(cmdargs[0], obj, changeFlag):
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

    def isRunning(self):
        if self._running:
            return(True)
        return(False)

    def start(self):
        ''' Start the editor '''
        # Set up logging
        logpath = Path('logs')
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
