""" common attribute superClass """

from common.general import logger


class AttributeHelper:
    """ SuperClass for attribute maintenance and testing """

    # Default lists of attributes, by type - override in SubClass
    intAttributes = []
    boolAttributes = []
    strAttributes = []
    listAttributes = []

    # obsolete attributes (to be removed)
    obsoleteAttributes = []

    def __init__(self):
        for attName in self.intAttributes:
            setattr(self, attName, 0)
        for attName in self.boolAttributes:
            setattr(self, attName, False)
        for attName in self.strAttributes:
            setattr(self, attName, "")

    def fixAttributes(self):  # noqa C901
        """ Sometimes we change attributes, and need to fix them in rooms
            that are saved.  This method lets us do that.  This is the
            generic case, but subClasses may choose to do more class
            specific fixes """
        logPrefix = "fixAttributes: "
        changed = False

        for attName in self.intAttributes:
            try:
                if not isinstance(getattr(self, attName), int):
                    newVal = int(getattr(self, attName, 0))
                    setattr(self, attName, newVal)
                    changed = True
                    logger.warning(
                        logPrefix
                        + "Changed "
                        + attName
                        + " to int for "
                        + self.describe()
                    )
            except ValueError:
                setattr(self, attName, 0)
                logger.warning(logPrefix + "Set " + attName + "= 0")
        for attName in self.boolAttributes:
            try:
                if not isinstance(getattr(self, attName), bool):
                    newVal = bool(getattr(self, attName, False))
                    setattr(self, attName, newVal)
                    changed = True
                    logger.warning(
                        logPrefix
                        + "Changed "
                        + attName
                        + " to bool for "
                        + self.describe()
                    )
            except ValueError:
                setattr(self, attName, False)
                logger.warning(logPrefix + "Set " + attName + "= False")
        for attName in self.strAttributes:
            try:
                if not isinstance(getattr(self, attName), str):
                    newVal = str(getattr(self, attName, False))
                    setattr(self, attName, newVal)
                    changed = True
                    logger.warning(
                        logPrefix
                        + "Changed "
                        + attName
                        + " to str for "
                        + self.describe()
                    )
            except ValueError:
                setattr(self, attName, "")
                logger.warning(logPrefix + "Set " + attName + "= ''")
        for attName in self.obsoleteAttributes:
            try:
                if hasattr(self, attName):
                    delattr(self, attName)
                    changed = True
                    logger.warning(
                        logPrefix + "Removed '" + attName + "' from " + self.describe()
                    )
            except AttributeError:
                pass
        return changed

    def testAttributes(self):
        """ Generic test to check attribute types """
        RF = "Attribute {0} should be a {1}\n"

        passed = True
        msg = ""

        for attName in self.intAttributes:
            attVal = getattr(self, attName)
            typeCheck = isinstance(attVal, int)
            if not typeCheck:
                passed = False
                msg += RF.format(attName, "int")

        for attName in self.boolAttributes:
            attVal = getattr(self, attName)
            typeCheck = isinstance(attVal, bool)
            if not typeCheck:
                passed = False
                msg += RF.format(attName, "bool")

        for attName in self.strAttributes:
            attVal = getattr(self, attName)
            typeCheck = isinstance(attVal, str)
            if not typeCheck:
                passed = False
                msg += RF.format(attName, "str")

        for attName in self.listAttributes:
            attVal = getattr(self, attName)
            typeCheck = isinstance(attVal, list)
            if not typeCheck:
                passed = False
                msg += RF.format(attName, "list")

        return (passed, msg)
