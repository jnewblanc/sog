''' test_creature '''
import unittest

from common.test import TestGameBase
# from common.general import logger
import creature


class TestCreature(TestGameBase):

    testCreatureNumber = 99999

    def setUp(self):
        self.banner('start', testName=__class__.__name__)

    def testCreatureInstanciation(self):
        creObj = creature.Creature(self.testCreatureNumber)
        out = "Could not instanciate the creature object"
        self.assertEqual(creObj._name == '', True, out)


if __name__ == '__main__':
    unittest.main()
