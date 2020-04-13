''' common functions '''

import glob
import logging
import os
from pathlib import Path
import pickle
import re

from common.paths import DATADIR


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
        return(self._datafile)

    def setDataFilename(self, dfStr=''):
        ''' sets the data file name.
            If no datafilename arg is provided, generate the datafile name
            based on the class and ID.  We can also override this method
            to use a different filename '''
        id = ''

        if dfStr == '':
            # generate the data file name based on class and id
            try:
                id = self.getId()
            except AttributeError:
                pass

            if id and id != '':
                self._datafile = os.path.abspath(DATADIR + '/' +
                                                 self.__class__.__name__ +
                                                 '/' + str(id) + '.pickle')
                if self._debugStorage:
                    logging.debug("setDataFilename: _datafile = " +
                                  self._datafile)
                return(True)
            else:
                logging.error("setDataFilename: Could not get id from " +
                              "object")
                return(False)
        else:
            # set data file name to name provided
            self._datafile = os.path.abspath(str(dfStr))
            return(True)
        return(False)

    def getId(self):
        return(None)

    def getSubClassName(self):
        return(self.__class__.__name__)

    def save(self, logStr=''):
        ''' save to persistant storage '''
        if logStr != '':
            logStr += ' '   # append a space for easy logging

        self.setDataFilename()
        # We are about to muck with the object data.  Before we do, store
        # the datafile info as a local variable so that there is no conflict.
        filename = self._datafile

        subclassname = self.getSubClassName()
        if filename == "":
            logging.error(subclassname + " Could not determine filename " +
                          " while saving " + logStr + str(self.getId()))
            return(False)
        if not self.isValid():  # if the instance we are saving is not valid
            logging.error(subclassname + " Save aborted - " + logStr +
                          str(self.getId()) + " is not valid")
            return(False)

        # create directory
        path = Path(os.path.dirname(self._datafile))
        path.mkdir(parents=True, exist_ok=True)

        # some attributes should not be, or can not be pickled, so we
        # store the values before we save, then we will restore them
        # immediately after.
        tmpStore = {}
        for attName in self.attributesThatShouldntBeSaved:
            try:
                tmpStore[attName] = getattr(self, attName)
            except AttributeError:
                pass
            setattr(self, attName, None)
            if self._debugStorage:
                logging.debug(subclassname + " ignoring " +
                              attName + " during save")
        # create data file
        delattr(self, '_datafile')     # never save _datafile attribute
        with open(filename, 'wb') as outputfilehandle:
            pickle.dump(self, outputfilehandle, pickle.HIGHEST_PROTOCOL)
        # Restore attributes that we temporarily set aside when saving.
        for attName in tmpStore.keys():
            setattr(self, attName, tmpStore[attName])
        if self._debugStorage:
            logging.debug(subclassname + " saved " + logStr +
                          str(self.getId()))
        return(True)

    def load(self, desiredAttributes=[], logStr=''):   # noqa: C901
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

        subclassname = self.getSubClassName()

        if filename == "":
            logging.error(subclassname + "Could not determine " +
                          "filename for loading " + logStr)
            return(False)

        if self.dataFileExists():
            with open(filename, 'rb') as inputfilehandle:
                loadedInst = pickle.load(inputfilehandle)
            instanceAttributes = vars(loadedInst)

            # filter out instance attributes that we want to ignore
            for onevar in self.attributesThatShouldntBeSaved:
                if self._debugStorage:
                    logging.debug(subclassname + " ignoring " +
                                  logStr + "attribute " +
                                  onevar + " during import")
                instanceAttributes = list(filter((onevar).__ne__,
                                                 instanceAttributes))

            # If we specified a list of desired attributes, revise our
            # attribute list to only contain the desired names.  Skip over
            # names that don't exist
            if len(desiredAttributes) > 0:
                newAttList = []
                for onevar in desiredAttributes:
                    if onevar in instanceAttributes:
                        newAttList.append(onevar)
                instanceAttributes = newAttList

            for onevar in instanceAttributes:
                setattr(self, onevar, getattr(loadedInst, onevar))
                buf = "imported " + logStr + "attribute " + onevar
                value = getattr(self, onevar)
                if ((isinstance(value, str) or isinstance(value, int) or
                     isinstance(value, list))):
                    buf += '=' + str(value)
                if self._debugStorage:
                    logging.debug(subclassname + " " + buf + '\n')

            if self._debugStorage:
                logging.debug(subclassname + " loaded " + logStr +
                              str(self.getId()))
            self.initTmpAttributes()
            self.fixAttributes()
            self.postLoad()
            if self.isValid():
                return(True)
        else:
            logging.warn(subclassname + " " + logStr +
                         'info doesn\'t exist at ' + self._datafile)
        return(False)

    def delete(self, logStr=''):
        subclassname = self.getSubClassName()
        self.setDataFilename()
        filename = self._datafile
        if filename == "":
            logging.error(subclassname + " Could not determine filename " +
                          " while deleting " + logStr + str(self.getId()))
            return(False)
        if not os.path.isfile(filename):
            logging.error(subclassname + " Could not delete " + filename +
                          " because it is not a file ")
            return(False)
        if self.dataFileExists():
            logging.info(subclassname + " Preparing to delete " +
                         logStr + " " + filename)
            os.remove(filename)
            if os.path.isfile(filename):
                logging.error(subclassname + " " + filename + " could not " +
                              "be deleted")
                return(False)
            else:
                logging.info(subclassname + " " + filename + " deleted")
                return(True)
        else:
            logging.error(subclassname + " " + filename + " could not " +
                          "be deleted because it doesn't exist")
            return(False)
        return(False)

    def initTmpAttributes(self):
        return(True)

    def fixAttributes(self):
        return(True)

    def postLoad(self):
        return(True)

    def isValid(self):
        return(True)


def getNextUnusedFileNumber(type):
    ''' return the next unused item number, by looking through the
        corresponding files for the last one used.  This is typically
        used when creating new objects or creatures '''
    dir = DATADIR
    if type != '':
        dir += '/' + type.capitalize()

    numberlist = []
    if os.path.exists(dir):
        filelist = glob.glob(dir + '/*.pickle')
        for fqfn in filelist:
            filenumber = re.sub('[^0-9]', '', os.path.basename(fqfn))
            if filenumber != '':
                numberlist.append(int(filenumber))
    if len(numberlist) > 0:
        return((numberlist[-1] + 1))
    return 0
