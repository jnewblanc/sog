''' test_general '''
from datetime import datetime, timedelta
import re
import unittest

import common.general
# from common.general import logger
import object


class TestGeneral(unittest.TestCase):
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
        # This test verifies that item selected is from the input list
        inputs = [['bacon', 'eggs', 'toast'],
                  ['toast'],
                  [1, 2, 3, 4, 5],
                  ]
        for num, input in enumerate(inputs):
            result = common.general.getRandomItemFromList(input)
            assert result in input   # result is one of the items in list

        # This test asserts that, given X tries, each of the X inputs will be
        # selected at least once.  There's a small chance that this could fail,
        # but it seems unlikely
        inputs = ['a', 'b', 'c', 'd']
        itemCount = {}
        for i in inputs:
            itemCount[i] = 0  # initialize counts
        for i in range(0, 1000):
            item = common.general.getRandomItemFromList(inputs)
            itemCount[item] += 1  # increment counter
        for i in inputs:
            assert itemCount[i]  # fail if count for item is 0

    def testDates(self):
        invalidInputs = [None, '', 1, 'None', [1, 2, 3]]
        neverInputs = [common.general.getNeverDate()]
        dayInputs = [datetime.now(),
                     datetime.now() - timedelta(seconds=30),
                     datetime.now() + timedelta(minutes=30),
                     datetime.now() - timedelta(hours=23)]
        longInputs = [datetime.now() - timedelta(hours=26),
                      datetime.now() - timedelta(days=3),
                      datetime.now() - timedelta(days=400)]

        validDateRegex = '^[0-9]+/[0-9]+/[0-9]+ [0-9]+:[0-9]+$'
        for num, input in enumerate(neverInputs + dayInputs + longInputs):
            aMsg = "input = " + str(input)
            secsSince = common.general.secsSinceDate(input)
            dateStr = common.general.dateStr(input)
            diffDay = common.general.differentDay(datetime.now(), input)

            if input in invalidInputs:
                assert secsSince == 0, aMsg
                assert dateStr == 'Never', aMsg
                assert diffDay is False, aMsg
            if input in neverInputs:
                assert secsSince == 0, aMsg
                assert dateStr == 'Never', aMsg
                assert diffDay is True, aMsg
            if input in dayInputs:
                assert secsSince < 86400, aMsg
                assert re.match(validDateRegex, dateStr), aMsg
                todaysDate = datetime.now().strftime("%Y/%m/%d")
                if re.match(todaysDate, input.strftime("%Y/%m/%d")):
                    assert diffDay is False, aMsg
                else:
                    assert diffDay is True, aMsg
            if input in longInputs:
                assert secsSince >= 86400, aMsg
                assert re.match(validDateRegex, dateStr), aMsg
                assert diffDay is True, aMsg

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

    def testTruncateWithInt(self):
        invalidInputs = [None, '', 'None', [1, 2, 3], datetime.now()]
        validInputs = [1.23456789, 1, 1.234, 123456789, 0.123456789, 0]
        invalidRegex = '\\.\\d{4}'
        for input in invalidInputs + validInputs:
            result = common.general.truncateWithInt(input)
            assert not re.search(invalidRegex, str(result))
            if input in validInputs and input != 0:
                assert result != 0


if __name__ == '__main__':
    unittest.main()
