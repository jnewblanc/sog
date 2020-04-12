''' general functions that can be shared across classes '''

from datetime import datetime
import logging
import re


def getNeverDate():
    ''' Return a date object/value that represents never '''
    return(datetime(1900, 1, 1))


def dateStr(onedate, datefmt="%Y/%m/%d %H:%M"):
    ''' return a given date Obj as a string, in our standard format '''
    if onedate == getNeverDate():
        return("Never")
    elif onedate == 'now':
        return(datetime.now().strftime(datefmt))
    else:
        return(onedate.strftime(datefmt))


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


def splitCmd(cmdargs):
    ''' break cmdargs into parts consisting of:
        1) command - Always the first arg
        2) list of targets, including their number.  Target examples:
           * staff
           * staff 2
           * staff #2
           * player
           * player #3
    '''
    cmd = ''
    argStr = ''
    targetList = []
    for arg in cmdargs:
        if cmd == '':                      # The first arg is the command
            cmd = arg
        elif argStr == '':                 # The second arg is the item
            argStr = arg
        elif isCountStr(arg):              # if the second arg is a number
            targetList.append(argStr + " " + arg)
            argStr = ''
        else:                   # the last one is complete, this one is new
            targetList.append(argStr)
            argStr = arg

    if argStr != '':           # if the last arg hasn't been appended
        targetList.append(argStr)
    return(cmd, targetList)


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


def itemSearch(itemList, name, desiredNum="#1", typeList=[]):
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

    if debugItemSearch:
        logging.debug("sea - Trying to search for item " + name +
                      " #" + str(desiredNum))

    cnt = 0
    for oneitem in itemList:
        if debugItemSearch:
            logging.debug("sea - Checking item name " + oneitem.getName() +
                          "...")
        if re.match("^" + name, oneitem.getName()):  # fuzzy name search
            cnt += 1
            if debugItemSearch:
                logging.debug("sea - item name " + oneitem.getName() +
                              " matched.  Checking type...")
            if len(typeList) > 0:
                if oneitem.getType().lower() not in typeList:
                    if debugItemSearch:
                        logging.debug("sea - skipping item " +
                                      oneitem.getName() + " because it "
                                      "doesn't match type " +
                                      str(typeList))
                    continue                # skip if not the desired type
            else:
                if debugItemSearch:
                    logging.debug("sea - skipping typecheck for item " +
                                  oneitem.getName())
            if debugItemSearch:
                logging.debug("sea - Checking number for item name " +
                              oneitem.getName() + " .  Looking for #" +
                              str(desiredNum))
            if cnt == desiredNum:  # skip if not desired number
                if debugItemSearch:
                    logging.debug("sea - Found item " +
                                  oneitem.getName() + " matching number "
                                  + str(cnt))
                myitem = oneitem
                break
            else:
                if debugItemSearch:
                    logging.debug("sea - Could not find " +
                                  oneitem.getName() +
                                  " with matching number " +
                                  str(desiredNum))
        else:
            if debugItemSearch:
                logging.debug("sea - Item " + oneitem.getName() +
                              " did not match.")
    if myitem:
        if debugItemSearch:
            logging.debug("sea - Found item " + myitem.getName())

    return(myitem)
