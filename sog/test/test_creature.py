''' test_creature '''
import unittest

# from common.general import logger
import creature


class TestCreature(unittest.TestCase):

    testCreatureNumber = 99999

    def testCreatureInstanciation(self):
        creObj = creature.Creature(self.testCreatureNumber)
        out = "Could not instanciate the creature object"
        self.assertEqual(creObj._name == '', True, out)


if __name__ == '__main__':
    unittest.main()
