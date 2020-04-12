
from datetime import datetime, timedelta
import unittest

import common.general
import object


class TestGeneral(unittest.TestCase):
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

    def testSplitCmd(self):
        inputs = ['use staff',
                  'use staff 1',
                  'use staff player',
                  'use staff 1 player',
                  'use staff player 2',
                  'use staff 1 player 2']
        outputs = [('use', ['staff']),
                   ('use', ['staff 1']),
                   ('use', ['staff', 'player']),
                   ('use', ['staff 1', 'player']),
                   ('use', ['staff', 'player 2']),
                   ('use', ['staff 1', 'player 2'])]

        for num, input in enumerate(inputs):
            inWords = input.split(' ')
            resultlist = common.general.splitCmd(inWords)
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

        inputs = ['use staff',
                  'use staff 1',
                  'use staff sword',
                  'use staff 2 sword',
                  'use staff sword 2',
                  'use staff 2 sword 2']
        outputs = [['staff1'],
                   ['staff1'],
                   ['staff1', 'sword1'],
                   ['staff2', 'sword1'],
                   ['staff1', 'sword2'],
                   ['staff2', 'sword2']]

        for num, input in enumerate(inputs):
            inWords = input.split(' ')
            cmd, targets = common.general.splitCmd(inWords)
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


if __name__ == '__main__':
    unittest.main()
