
import unittest

import object


class TestObject(unittest.TestCase):

    testObjNumber = 99999

    def testObjectInstanciation(self):
        objObj = object.Door(self.testObjNumber)
        out = "Could not instanciate the object object"
        self.assertEqual(objObj.isPermanent(), True, out)

    def testTrapTxt(self):
        inputs = [(1, False, 150),
                  (22, False, 150),
                  (69, False, 150),
                  (135, False, 150),
                  (135, False, 50),
                  (9, True, 150),
                  (21, True, 150),
                  (80, True, 150),
                  ]
        outputs = ["Splinters on your hand!",
                   "Putrid dust sprays in your eyes!",
                   "Blam!  Explosion in your face!",
                   "Boooooom!",
                   "Tons of rocks tumble down upon you!",
                   "Poison dart!",
                   "Cobra lunges at you!",
                   "Gas spores explode!"
                   ]
        for num, input in enumerate(inputs):
            obj1 = object.Door(self.testObjNumber)
            result = obj1.trapTxt(inputs[num][0], inputs[num][1],
                                  inputs[num][2])
            out = ("Input: " + str(inputs[num]) + " - Output: " + str(result) +
                   " - Expected: " + str(outputs[num]))
            status = bool(result == outputs[num])
            self.assertEqual(status, True, out)


if __name__ == '__main__':
    unittest.main()
