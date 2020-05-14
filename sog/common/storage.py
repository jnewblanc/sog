''' common functions '''

import jsonpickle
import os
from pathlib import Path
import pickle
import re
import traceback

from common.general import logger
from common.globals import DATADIR


class Storage():
    ''' Storage object superClass '''

    _debugStorage = False
    attributesThatShouldntBeSaved = []

    def __init__(self):
        self._datafile = ''

    def dataFileExists(self):
        ''' returns True if the file exists '''
        if os.path.isfile(self._datafile):
            return(True)
        return(False)

    def getDataFilename(self):
        ''' returns the filename - should always be overridden '''
        logger.error("storage.getDataFilename: method not overwritten")
        return(self._datafile)

    def setDataFilename(self, dfStr=''):
        ''' sets the data file name.
            If no datafilename arg is provided, generate the datafile name
            based on the class and ID.  We can also override this method
            to use a different filename '''
        id = ''
        logPrefix = __class__.__name__ + " setDataFilename: "

        if dfStr == '':
            # generate the data file name based on class and id
            try:
                id = self.getId()
            except AttributeError:
                pass

            if not id:
                logger.error(logPrefix + "Could not retrieve Id to " +
                             "generate filename")
                return(False)

            if id == '':
                logger.error(logPrefix + "ID is empty while generating " +
                             "datafile name")
                return(False)

            if hasattr(self, '_fileextension'):
                extension = self._fileextension
            else:
                extension = '.pickle'

            self._datafile = os.path.abspath(DATADIR + '/' +
                                             self.__class__.__name__ +
                                             '/' + str(id) + extension)
        else:
            # set data file name to name provided
            self._datafile = os.path.abspath(str(dfStr))

        if self._debugStorage:
            logger.debug(logPrefix + "_datafile = " + self._datafile)
        return(True)

    def getId(self):
        ''' available for override '''
        return(None)

    def load(self, requestedAttNames=[], logStr='', fileType='pickle'):
        ''' load from persistant storage
              - load data into tmp object
              - iterate through the attributes assigning all, except the
                 ones that we specificly exclude, to the current object
              - values of excluded objects are not overwritten '''
        if logStr != '':
            logStr += ' '   # append a space for easy logging

        self.setDataFilename()
        # We may muck with the object data.  Before we do, store
        # the datafile info as a local variable so that there is no conflict.
        filename = self._datafile

        logPrefix = self.__class__.__name__ + " load: "

        if filename == "":
            logger.error(logPrefix + " Could not determine " +
                         "filename for loading " + logStr)
            return(False)

        if self._debugStorage:
            logger.debug(logPrefix + "Loading " + filename + "...")

        if self.dataFileExists():
            # read the persisted content
            if re.search('\\.json$', filename):
                loadedDict = self.readJsonFile(filename, logStr)
            else:
                loadedDict = self.readPickleFile(filename, logStr)

            if not loadedDict:
                logger.error("storage.load - Could not get loaded instance")

            # Add attributes to current class object, based on revised list
            self.addAttributesToSelf(loadedDict, requestedAttNames, logStr)

            if self._debugStorage:
                logger.debug(logPrefix + " loaded " + logStr +
                             str(self.getId()) + " - " + self.describe())

            self.initTmpAttributes()
            self.fixAttributes()
            self.postLoad()
            if self.isValid():
                return(True)
            else:
                logger.error(logPrefix + logStr + str(self.getId()) +
                             " is not valid")
        else:
            logger.warning(logPrefix + " " + logStr +
                           'datafile doesn\'t exist at ' + self._datafile)
        return(False)

    def save(self, logStr=''):
        ''' save to persistant storage '''
        if logStr != '':
            logStr += ' '   # append a space for easy logging

        self.setDataFilename()
        # We are about to muck with the object data.  Before we do, store
        # the datafile info as a local variable so that there is no conflict.
        filename = self._datafile

        logPrefix = self.__class__.__name__ + " save: "
        if filename == "":
            logger.error(logPrefix + "Could not determine filename " +
                         " while saving " + logStr + str(self.getId()))
            return(False)
        if not self.isValid():  # if the instance we are saving is not valid
            logger.error(logPrefix + "Save aborted - " + logStr +
                         str(self.getId()) + " is not valid")
            return(False)

        # create directory
        path = Path(os.path.dirname(self._datafile))
        path.mkdir(parents=True, exist_ok=True)

        # some attributes should not be, or can not be pickled, so we
        # store the values before we save, then we will restore them
        # immediately after.
        tmpStore = {}
        for attName in (self.attributesThatShouldntBeSaved +
                        ['_datafile', '_instanceDebug']):
            try:
                tmpStore[attName] = getattr(self, attName)
                if hasattr(self, attName):
                    delattr(self, attName)
                if self._debugStorage:
                    logger.debug(logPrefix + "Ignoring " + attName +
                                 " during save")
            except AttributeError:
                if self._debugStorage:
                    logger.debug(logPrefix + "Could not ignore " + attName +
                                 " during save")

        # persist content - create data file
        if re.search('\\.json$', filename):
            self.writeJSonFile(filename)
        else:
            self.writePickleFile(filename)

        # Restore attributes that we temporarily set aside when saving.
        for attName in tmpStore.keys():
            setattr(self, attName, tmpStore[attName])

        if self._debugStorage:
            logger.debug(logPrefix + "saved " + logStr + " - " +
                         str(self.getId()))
        return(True)

    def writePickleFile(self, filename):
        with open(filename, 'wb') as outputfilehandle:
            try:
                pickle.dump(self, outputfilehandle, pickle.DEFAULT_PROTOCOL)
            except TypeError:
                logger.debug(self.debug())
                traceback.print_exc()

    def readPickleFile(self, filename, logStr=''):
        with open(filename, 'rb') as inputfilehandle:
            loadedItem = pickle.load(inputfilehandle)

        pickleDict = {}
        for onevar in vars(loadedItem):
            # filter out attributes that should be excluded
            if self.attributeShouldBeIgnored(onevar):
                continue
            pickleDict[onevar] = getattr(loadedItem, onevar)
        return(pickleDict)

    def writeJSonFile(self, filename):
        jsonpickle.set_encoder_options('json', sort_keys=True, indent=4,
                                       ensure_ascii=False)
        frozen = jsonpickle.encode(self)
        with open(filename, 'w') as filehandle:
            try:
                filehandle.write(frozen)
                # json.dump(frozen, filehandle)
            except TypeError:
                logger.debug(self.debug())
                traceback.print_exc()

    def readJsonFile(self, filename, logStr=''):
        logPrefix = 'readJsonFile: '
        with open(filename, 'r') as filehandle:
            loadedItem = filehandle.read()
            thawedDict = jsonpickle.decode(loadedItem)

            if isinstance(thawedDict, dict):
                logger.warn(logPrefix + "Loaded content is of type: " +
                            str(type(thawedDict)) + " which probably means " +
                            " that it was saved or loaded incorrectly")

                # filter out attributes that should be excluded
                for onevar in self.attributesThatShouldntBeSaved:
                    if hasattr(thawedDict, onevar):
                        if self._debugStorage:
                            logger.debug(logPrefix + " ignoring " + logStr +
                                         "attribute " + onevar +
                                         " during import")
                        thawedDict = list(filter((onevar).__ne__, thawedDict))

            else:  # imported content is a known object (Creature, Char, etc)
                jsonDict = {}
                for onevar in vars(thawedDict):
                    # filter out attributes that should be excluded
                    if self.attributeShouldBeIgnored(onevar):
                        continue
                    jsonDict[onevar] = getattr(thawedDict, onevar)
                thawedDict = jsonDict

            return(thawedDict)
        return(None)

    def attributeShouldBeIgnored(self, attName, logStr=''):
        ''' Return True if given attribute should be ignored '''
        logPrefix = 'attributeShouldBeIgnored: '
        if attName in self.attributesThatShouldntBeSaved:
            if self._debugStorage:
                logger.debug(logPrefix + " ignoring " + logStr +
                             "attribute " + attName + " during import")
            return(True)
        return(False)

    def addAttributesToSelf(self, loadedDict, requestedAttNames=[], logStr=''):
        ''' Add attributes to current class object '''
        logPrefix = 'addAttributesToSelf: '

        if not isinstance(loadedDict, dict):
            logger.error(logPrefix + 'loadedDict is not a dict.' +
                         '  Its of type ' + str(type(loadedDict)))

        for key, value in zip(loadedDict.keys(), loadedDict.values()):
            # If specific attributes are requested, skip all attributes that
            # do not match.
            if len(requestedAttNames) > 0:
                if key not in requestedAttNames:
                    continue

            setattr(self, key, value)
            buf = "imported " + logStr + "attribute " + key
            if ((isinstance(value, str) or isinstance(value, int) or
                 isinstance(value, list))):
                buf += '=' + str(value)
            if self._debugStorage:
                logger.debug(logPrefix + " " + buf + '\n')

    def delete(self, logStr=''):
        logPrefix = self.__class__.__name__ + " delete: "
        self.setDataFilename()
        filename = self._datafile
        if filename == "":
            logger.error(logPrefix + " Could not determine filename " +
                         " while deleting " + logStr + str(self.getId()))
            return(False)
        if not os.path.isfile(filename):
            logger.error(logPrefix + " Could not delete " + filename +
                         " because it is not a file ")
            return(False)
        if self.dataFileExists():
            logger.info(logPrefix + " Preparing to delete " +
                        logStr + " " + filename)
            try:
                os.remove(filename)
            except OSError as e:
                logger.error(logPrefix + "Failed with:" + e.strerror)
                logger.error(logPrefix + "Error code:" + e.code)

            if os.path.isfile(filename):
                logger.error(logPrefix + " " + filename + " could not " +
                             "be deleted")
                return(False)
            else:
                logger.info(logPrefix + " " + filename + " deleted")
                return(True)
        else:
            logger.error(logPrefix + " " + filename + " could not " +
                         "be deleted because it doesn't exist")
            return(False)
        return(False)

    def initTmpAttributes(self):
        ''' available for override '''
        return(True)

    def fixAttributes(self):
        ''' available for override '''
        return(True)

    def postLoad(self):
        ''' available for override '''
        return(True)

    def isValid(self):
        ''' available for override '''
        return(True)
