# pytest cheat sheet

Full test suite:
```
pytest
```

Run all tests that are in a file:
```
pytest <file>
pytest sog/test/test_game.py
```

Run specific tests:
```
pytest <file> -k 'test1 or test2'
pytest sog/test/test_game.py -k 'testFollowLose'
```
