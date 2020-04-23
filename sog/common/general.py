''' general functions that can be shared across classes '''

from datetime import datetime
import logging
import random
import re


def getNeverDate():
    ''' Return a date object/value that represents never '''
    return(datetime(1900, 1, 1))


def secsSinceDate(date1):
    ''' return seconds since a given date '''
    if not date1:
        return(0)
    if date1 == getNeverDate():
        return(0)
    return((datetime.now() - date1).total_seconds())


def dateStr(onedate, datefmt="%Y/%m/%d %H:%M"):
    ''' return a given date Obj as a string, in our standard format '''
    if onedate == getNeverDate():
        return("Never")
    elif onedate == 'now':
        return(datetime.now().strftime(datefmt))
    elif onedate:
        return(onedate.strftime(datefmt))
    else:
        logging.error("dateStr returned an empty value")
        return('')


def differentDay(date1, date2):
    ''' Compare dates to see if they are the same day
        * typically used for daily events, counters, stats, etc '''
    if ((date1.strftime("%Y/%m/%d") != date2.strftime("%Y/%m/%d"))):
        return(True)
    return(False)


def rreplace(s, old, new, occurrence=1):
    ''' replace last occurance of a string '''
    li = s.rsplit(old, occurrence)
    return new.join(li)


def isIntStr(numstr):
    ''' Return True if the given string contains ony digits '''
    if re.match("^[0-9]+$", str(numstr)):
        return(True)
    return(False)


def isCountStr(numstr):
    ''' Return True if the given string contains ony digits of # and digits '''
    if re.match("^#*[0-9]+$", str(numstr)):
        return(True)
    return(False)


def getRandomItemFromList(list1):
    ''' Given a list, returns random element '''
    if len(list1) == 0:
        return(None)
    indexNum = random.randint(0, len(list1) - 1)
    return(list1[indexNum])


def splitTargets(targetStr):
    ''' break cmdargs into parts consisting of:
        1) cmdargs are already stripped of their first arg
        2) list of targets, including their number.  Target examples:
           * staff
           * staff 2
           * staff #2
           * player
           * player #3
    '''
    argStr = ''
    targetList = []
    for arg in targetStr.split(' '):
        if argStr == '':                 # The first arg is the item
            argStr = arg
        elif isCountStr(arg):              # if the first arg is a number
            targetList.append(argStr + " " + arg)
            argStr = ''
        else:                   # the last one is complete, this one is new
            targetList.append(argStr)
            argStr = arg

    if argStr != '':           # if the last arg hasn't been appended
        targetList.append(argStr)
    return(targetList)


def targetSearch(itemList, targetStr):
    ''' returns the first matching item from itemList or None
        * breaks up targetStr into parts
        * calls itemSearch with the proper arguments
    '''
    targetWords = targetStr.split(' ')
    if len(targetWords) == 1:
        targetObj = itemSearch(itemList, targetWords[0])
    if len(targetWords) > 1:
        targetObj = itemSearch(itemList, targetWords[0], targetWords[1])
    return(targetObj)


def dLog(msg, show=False):
    ''' Show debug log messages if flag is set '''
    if show:
        logging.debug(msg)
    return(None)


def itemSearch(itemList, name, desiredNum="#1", typeList=[]):  # noqa: C901
    ''' Often we need a fuzzy search lookup of items in a list (of class
        instances).  Given a list, return an item that matches the name,
        number, and type.
        * Requires that instances have getName and getType methods
        * can be used for objects in room, items in inventory, etc
    '''
    myitem = None
    debugItemSearch = False

    # strip out anything that's not a digit (i.e. number signs)
    desiredNum = int(re.sub('[^0-9]', '', str(desiredNum)))

    dLog("sea - Trying to search for item " + name + " #" + str(desiredNum),
         debugItemSearch)

    cnt = 0
    for oneitem in itemList:
        dLog("sea - Checking item name " + oneitem.getName() + "...",
             debugItemSearch)
        if re.match("^" + name, oneitem.getName()):  # fuzzy name search
            cnt += 1
            dLog("sea - item name " + oneitem.getName() +
                 " matched.  Checking type...", debugItemSearch)
            if len(typeList) > 0:
                if oneitem.getType().lower() not in typeList:
                    dLog("sea - skipping item " + oneitem.getName() +
                         " because it doesn't match type " + str(typeList),
                         debugItemSearch)
                    continue                # skip if not the desired type
            else:
                dLog("sea - skipping typecheck for item " + oneitem.getName(),
                     debugItemSearch)
            dLog("sea - Checking number for item name " + oneitem.getName() +
                 " .  Looking for #" + str(desiredNum), debugItemSearch)
            if cnt == desiredNum:  # skip if not desired number
                dLog("sea - Found item " + oneitem.getName() +
                     " matching number " + str(cnt), debugItemSearch)
                myitem = oneitem
                break
            else:
                dLog("sea - Could not find " + oneitem.getName() +
                     " with matching number " + str(desiredNum),
                     debugItemSearch)
        else:
            dLog("sea - Item " + oneitem.getName() + " did not match.",
                 debugItemSearch)
    if myitem:
        dLog("sea - Found item " + myitem.getName(), debugItemSearch)

    return(myitem)
