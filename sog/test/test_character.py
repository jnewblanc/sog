import unittest
import character


class TestCharacter(unittest.TestCase):

    def testIntAttributes(self):
        charObj = character.Character()
        for oneAtt in charObj.intAttributes:
            val = getattr(charObj, oneAtt)
            self.assertEqual(isinstance(val, int), True, oneAtt + " should be a int")  # noqa: E501

    def testBoolAttributes(self):
        charObj = character.Character()
        for oneAtt in charObj.boolAttributes:
            val = getattr(charObj, oneAtt)
            self.assertEqual(isinstance(val, bool), True, oneAtt + " should be a bool")  # noqa: E501

    def testStrAttributes(self):
        charObj = character.Character()
        for oneAtt in charObj.strAttributes:
            val = getattr(charObj, oneAtt)
            self.assertEqual(isinstance(val, str), True, oneAtt + " should be a str")  # noqa: E501

    def testListAttributes(self):
        charObj = character.Character()
        for oneAtt in charObj.listAttributes:
            val = getattr(charObj, oneAtt)
            self.assertEqual(isinstance(val, list), True, oneAtt + " should be a list")  # noqa: E501


if __name__ == '__main__':
    unittest.main()
