''' common attribute superClass '''


class AttributeHelper():
    ''' SuperClass for attribute maintenance and testing '''

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
            setattr(self, attName, '')

    def fixAttributes(self):
        ''' Sometimes we change attributes, and need to fix them in rooms
            that are saved.  This method lets us do that.  This is the
            generic case, but subClasses may choose to do more class
            specific fixes '''
        # integer attributes

        for attName in self.intAttributes:
            try:
                newVal = int(getattr(self, attName, 0))
            except ValueError:
                newVal = 0
            setattr(self, attName, newVal)
        for attName in self.boolAttributes:
            try:
                newVal = bool(getattr(self, attName, False))
            except ValueError:
                newVal = False
            setattr(self, attName, newVal)
        for attName in self.strAttributes:
            try:
                newVal = str(getattr(self, attName, False))
            except ValueError:
                newVal = ''
            setattr(self, attName, newVal)
        for attName in (self.obsoleteAttributes):
            try:
                delattr(self, attName)
            except AttributeError:
                pass

    def test_attributes(self):
        ''' Generic test to check attribute types '''
        RF = "Attribute {0} should be a {1}\n"

        for attName in self.intAttributes:
            attVal = getattr(self, attName)
            typeCheck = isinstance(attVal, int)
            self.assertTrue(typeCheck, RF.format(attName, "int"))

        for attName in self.boolAttributes:
            attVal = getattr(self, attName)
            typeCheck = isinstance(attVal, bool)
            self.assertTrue(typeCheck, RF.format(attName, "bool"))

        for attName in self.strAttributes:
            attVal = getattr(self, attName)
            typeCheck = isinstance(attVal, str)
            self.assertTrue(typeCheck, RF.format(attName, "str"))

        for attName in self.listAttributes:
            attVal = getattr(self, attName)
            typeCheck = isinstance(attVal, list)
            self.assertTrue(typeCheck, RF.format(attName, "list"))
