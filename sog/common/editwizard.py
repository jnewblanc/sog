''' editWizard '''


class EditWizard():
    ''' SuperClass for objects that get edited
        * Definitions are provided by the classes and are consumed by the
          editor '''

    def __init__(self):
        self.wizardAttributes = []
        self.attributeInfo = {}

    def getWizFields(self):
        ''' Editor uses to determine which fields to prompt for '''
        return(self.wizardAttributes)

    def getWizHelp(self, attName):
        ''' Returns the attribute help info '''
        try:
            value = self.attributeInfo[attName]
        except KeyError:
            value = ''
        return(value)
