''' general functions that can be shared across classes '''

from datetime import datetime
import logging
from logging.handlers import TimedRotatingFileHandler
from os.path import basename
from pathlib import Path
import random
import re
import sys

from common.globals import LOGDIR


class Terminator(Exception):
    """ Custom exception to trigger termination of all threads & main. """
    pass


def sig_handler(signal_received, frame):
    print('SIGINT, SIGTERM, or CTRL-C detected. Exiting gracefully')
    raise Terminator


def getLogger(logName, loglevel=logging.DEBUG):
    logpath = Path(LOGDIR)
    logpath.mkdir(parents=True, exist_ok=True)
    FORMAT = '%(asctime)-15s %(levelname)s %(message)s'
    DATEFORMAT = '%m/%d/%y %H:%M:%S'
    LOGFILE = LOGDIR + '/' + logName + '.log'

    logger = logging.getLogger(logName)
    logger.setLevel(loglevel)

    # create a file handler
    # logHandler = logging.FileHandler(LOGFILE)
    # daily logs rotated after 30 days
    logHandler = TimedRotatingFileHandler(LOGFILE, when="d", interval=1,
                                          backupCount=30)
    logHandler.setLevel(loglevel)

    # create a logging format
    logFormatter = logging.Formatter(FORMAT, DATEFORMAT)
    # add the format to the handler
    logHandler.setFormatter(logFormatter)

    # add the handler to the logger
    logger.addHandler(logHandler)
    return(logger)


def dLog(msg, show=False):
    ''' Show debug log messages if flag is set '''
    if show:
        logger.debug(msg)
    return(None)


def getNeverDate():
    ''' Return a date object/value that represents never '''
    return(datetime(1900, 1, 1))


def secsSinceDate(date1):
    ''' return seconds since a given date '''
    if not date1:
        logger.error("secsSinceDate: date was not defined.  Returning 0")
        return(0)
    if date1 == getNeverDate():
        logger.warning("secsSinceDate: received NeverDate.  Returning 0")
        return(0)
    return((datetime.now() - date1).total_seconds())


def dateStr(date1, datefmt="%Y/%m/%d %H:%M"):
    ''' return a given date Obj as a string, in our standard format '''
    if not date1:
        logger.error("dateStr: date was not defined.  Returning ''")
        return('')
    if date1 == getNeverDate():
        return("Never")
    elif date1 == 'now':
        return(datetime.now().strftime(datefmt))
    elif date1:
        return(date1.strftime(datefmt))
    else:
        logger.error("dateStr: Could not parse - returned an empty value")
        return('')


def differentDay(date1, date2):
    ''' Compare dates to see if they are the same day
        * typically used for daily events, counters, stats, etc '''
    if not date1:
        logger.error("differentDay: date was not defined.  Returning False")
        return(False)
    if not date2:
        logger.error("differentDay: date was not defined.  Returning False")
        return(False)
    if ((date1.strftime("%Y/%m/%d") != date2.strftime("%Y/%m/%d"))):
        return(True)
    return(False)


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


def sortItemFunc(s):
    ''' Sort function '''
    return(s.describe())


def itemSort(itemList):
    newItemList = sorted(itemList, key=sortItemFunc)
    return(newItemList)


def getRandomItemFromList(list1):
    ''' Given a list, returns random element '''
    if len(list1) == 0:
        return(None)
    indexNum = random.randint(0, len(list1) - 1)
    return(list1[indexNum])


def truncateWithInt(num, decimalPlaces=3):
    ''' Given a number, returns that number truncated to X decimal places '''
    if not num:
        logger.error("truncateWithInt: num was not defined.  Returning 0")
        return(0)
    if not isinstance(num, float) and not isinstance(num, int):
        logger.error("truncateWithInt: invalid num.  Returning 0")
        return(0)
    shifter = 10 ** decimalPlaces
    return int(num * shifter) / shifter


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


def itemSearch(itemList, name, desiredNum="#1", typeList=[],
               sortList=False):  # noqa: C901
    ''' Often we need a fuzzy search lookup of items in a list (of class
        instances).  Given a list, return an item that matches the name,
        number, and type.
        * Requires that instances have getName and getType methods
        * can be used for objects in room, items in inventory, etc
    '''
    logPrefix = "sea: "
    myitem = None
    debugItemSearch = True

    # strip out anything that's not a digit (i.e. number signs)
    desiredNum = int(re.sub('[^0-9]', '', str(desiredNum)))

    if sortList:
        itemList = itemSort(itemList)

    dLog(logPrefix + "Trying to search for item " + name + " #"
         + str(desiredNum) + ' in ' +
         str([x.describe() for x in itemList]), debugItemSearch)

    cnt = 0
    for oneitem in itemList:
        dLog(logPrefix + "Checking item name " + oneitem.getName() + "...",
             debugItemSearch)
        if re.match("^" + name.lower(), oneitem.getName().lower()):  # fuzzy
            cnt += 1
            dLog(logPrefix + "item name " + oneitem.getName() +
                 " matched.  Checking type...", debugItemSearch)
            if len(typeList) > 0:
                if oneitem.getType().lower() not in typeList:
                    dLog(logPrefix + "skipping item " + oneitem.getName() +
                         " because it doesn't match type " + str(typeList),
                         debugItemSearch)
                    continue                # skip if not the desired type
            else:
                dLog(logPrefix + "skipping typecheck for item " +
                     oneitem.getName(), debugItemSearch)
            dLog(logPrefix + "Checking number for item name " +
                 oneitem.getName() + " .  Looking for #" +
                 str(desiredNum), debugItemSearch)
            if cnt == desiredNum:  # skip if not desired number
                dLog(logPrefix + "Found item " + oneitem.getName() +
                     " matching number " + str(cnt), debugItemSearch)
                myitem = oneitem
                break
            else:
                dLog(logPrefix + "Could not find " + oneitem.getName() +
                     " with matching number " + str(desiredNum),
                     debugItemSearch)
        else:
            dLog(logPrefix + "Item " + oneitem.getName() + " did not match.",
                 debugItemSearch)
    if myitem:
        dLog(logPrefix + "Found item " + myitem.getName(), debugItemSearch)

    return(myitem)


# Set up global logger
global logger
try:
    logger            # Test to see if logger is defined
except NameError:
    # Set up the logger if it doesn't already exist
    logname = re.sub('\\..*$', '', str(basename(sys.argv[0])).lower())
    if logname == '':
        logname = 'generic'
    logger = getLogger(logname)
    logLocation = LOGDIR + '\\' + logname + '.log'
    print("Log: " + logLocation)
    logger.info("")
    logger.info("-----------------------------------------------------------")
    logger.info("Log start: " + logLocation)
