''' test_general '''
from datetime import datetime, timedelta
import unittest

import common.general
from common.testLib import InitTestLog
import object


class TestGeneral(unittest.TestCase, InitTestLog):
    def testDifferentDay(self):
        now = datetime.now()
        yd = now - timedelta(days=1)
        inputs = [[now, now],
                  [yd, yd],
                  [now, yd],
                  [yd, common.general.getNeverDate()],
                  [common.general.getNeverDate(), common.general.getNeverDate()],  # noqa: E501
                  [now, common.general.getNeverDate()]]
        outputs = [False,
                   False,
                   True,
                   True,
                   False,
                   True]
        for num, input in enumerate(inputs):
            result = common.general.differentDay(inputs[num][0],
                                                 inputs[num][1])
            out = ("Input: " + str(input) + " - Output: " + str(result) +
                   " - Expected: " + str(outputs[num]))
            status = bool(result == outputs[num])
            self.assertEqual(status, True, out)

    def testIsIntStr(self):
        inputs = ['apple',
                  'apple 1',
                  'apple #1',
                  'apple #11',
                  '1',
                  '33',
                  '#33',
                  '33x',
                  '@33']
        outputs = [False,
                   False,
                   False,
                   False,
                   True,
                   True,
                   False,
                   False,
                   False]
        for num, input in enumerate(inputs):
            result = common.general.isIntStr(input)
            out = ("Input: " + str(input) + " - Output: " + str(result) +
                   " - Expected: " + str(outputs[num]))
            status = bool(result == outputs[num])
            self.assertEqual(status, True, out)

    def testIsCountStr(self):
        inputs = ['apple',
                  'apple 1',
                  'apple #1',
                  'apple #11',
                  '1',
                  '33',
                  '#33',
                  '33x',
                  '@33']
        outputs = [False,
                   False,
                   False,
                   False,
                   True,
                   True,
                   True,
                   False,
                   False]
        for num, input in enumerate(inputs):
            result = common.general.isCountStr(input)
            out = ("Input: " + str(input) + " - Output: " + str(result) +
                   " - Expected: " + str(outputs[num]))
            status = bool(result == outputs[num])
            self.assertEqual(status, True, out)

    def testSplitTarget(self):
        inputs = ['staff',
                  'staff 1',
                  'staff player',
                  'staff 1 player',
                  'staff player 2',
                  'staff 1 player 2']
        outputs = [['staff'],
                   ['staff 1'],
                   ['staff', 'player'],
                   ['staff 1', 'player'],
                   ['staff', 'player 2'],
                   ['staff 1', 'player 2']]

        for num, input in enumerate(inputs):
            resultlist = common.general.splitTargets(input)
            out = ("Input: " + str(input) + " - Output: " + str(resultlist) +
                   " - Expected: " + str(outputs[num]))
            status = bool(resultlist == outputs[num])
            self.assertEqual(status, True, out)

    def testTargetSearch(self):
        itemList = []

        # Create a list of objects with names corresponding to ids.
        obj1 = object.Object(1)
        obj1.setName("staff1")
        itemList.append(obj1)
        obj2 = object.Object(2)
        obj2.setName("sword1")
        itemList.append(obj2)
        obj3 = object.Object(3)
        obj3.setName("armor1")
        itemList.append(obj3)
        obj4 = object.Object(4)
        obj4.setName("staff2")
        itemList.append(obj4)
        obj5 = object.Object(5)
        obj5.setName("sword2")
        itemList.append(obj5)

        inputs = ['staff',
                  'staff 1',
                  'staff sword',
                  'staff 2 sword',
                  'staff sword 2',
                  'staff 2 sword 2']
        outputs = [['staff1'],
                   ['staff1'],
                   ['staff1', 'sword1'],
                   ['staff2', 'sword1'],
                   ['staff1', 'sword2'],
                   ['staff2', 'sword2']]

        for num, input in enumerate(inputs):
            targets = common.general.splitTargets(input)
            for num2, target in enumerate(targets):
                obj = common.general.targetSearch(itemList, target)
                if obj:
                    out = ("Input: " + str(input) + " - Output: (" +
                           str(obj.getName()) +
                           ") - Expected: (" + str(outputs[num][num2]) + ')')
                    status = bool(obj.getName() == outputs[num][num2])
                else:
                    out = "Could not retrieve item for input: " + str(input)
                    status = False
                self.assertEqual(status, True, out)

    def testGetRandomItemFromList(self):
        inputs = [['bacon', 'eggs', 'toast'],
                  ['toast'],
                  [1, 2, 3, 4, 5],
                  ]
        for num, input in enumerate(inputs):
            resultlist = common.general.getRandomItemFromList(input)
            out = ("Input: " + str(input) + " - Output: " + str(resultlist))
            status = bool(str(resultlist) != '')
            self.assertEqual(status, True, out)


if __name__ == '__main__':
    unittest.main()
