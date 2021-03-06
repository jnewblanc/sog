# sog

A creative recreation of the late 80's MUD, written in Python

### Background ###

In the late 80's, I used my 300 baud modem to dial into a Teleplay 12-line modem bank to play [Scepter of Goth](https://dwheeler.com/scepter-of-goth/scepter-of-goth.html), a txt based fantasy role playing (RPG) multi-user dungeon (MUD).  It was cutting edge at the time, was super fun, and I met a lot of great people, some of whom I still keep in contact with today.

Fast forward 30 years.  I'm a build/release/devops engineer who was looking to learn python, object oriented scripting, and a new IDE when I came across some old printouts for Teleplay and Scepter of Goth.  This prompted me to embark on a creative remake of the SoG MUD.  I opted to stick with the original gameplay where it made sense, but to creatively alter it, or expand it, as desired.

While I'm working to make this a playable game in the end, my primary goal is to obtain a decent grasp of the Python language, as well as having my own code project to use for practicing my release engineering skills.  Starting from a place of not knowing Python, never having written a game, and not having any serious object oriented design experience, I expect that the code will start out ugly.  As I learn more, it will, hopefully, improve and become more pythonic.  At some point, I hope to make this project public and/or open it up to like-minded contributors.

### Installation ###
1. Install docker
2. Install python
3. Clone sog repo
4. For multiplayer, adjust firewall to allow external connections to port 8888
   1. Windows: https://www.tomshardware.com/news/how-to-open-firewall-ports-in-windows-10,36451.html

### To play ###
1. Run the server
   - Windows: Run the server script
```
 sog --> sog --> bin --> docker_server_start.bat
```
OR
   - Mac/Linux: Open a command shell and run:
```
cd sog/sog
docker-compose up
```
2. Run the client
   1. Run the client script in sob/bin OR
   2. Open a command shell and run:
```
cd sog/sog
python client.py
```
   3. For remote clients, provide server ip address
```
client.py --host <local-network-server-ip-address>)
```
3. Tips for first timers:
  - Get familiar with commands by using the "help" command
  - New activity is only displayed when you press [enter]
  - The farther you get from Town Square, the more dangerous it gets


### Admin/DM Info ###
* At present, all persistent storage is on disk in the sog/.data directory.
  - All account/character info only exists locally (ignored via .gitignore)
* logs are in sog/.logs .  Some windows logfile tailing scripts are in sog/bin
* town map is at: https://docs.google.com/drawings/d/1SDAjL62DRsWta3vgfGLerKsn49e5wzywlQregGmKTbk/edit
* Game balance spreadsheets: https://docs.google.com/spreadsheets/d/1A9xDUhb6tH_dD-rPEm43a6ojthbCDpA9_RNiBZouvTg/edit#gid=214718106
* To become an admin, create an account and then create an empty isAdmin.txt file in your account directory: sog\sog\.data\Account\<your_email>
  - Having an admin account allows you to:
    1. Create DM characters
    2. Turn dm mode on in-game by running the dm_on command
  - In game DM mode allows you to:
    1. See additional debug info
    2. Use the "debug <obj>" command to see object data
    3. Use some additional DM-only commands
      4. Not die, even when health gets to 0

### Basic Design ###
1. client connects to server
   1. connection is persistent
   2. communication is series of send/receives
   3. server output is spooled
   4. client prompts user for input and displays output from server
   5. Single instance of game is spun up in the background
   6. aSync thread, for non-user activity, is spun up in the background
2. User enters 'serverLoop' which prompts for authentication
   1. email/password for auth
   2. Account has login/logout stats and several character "slots"
3. User enters the main "lobby" loop
  1. lobby has a "help" command
  3. lobby has a "play" command, which launches the game loop
  4. lobby has some inter-user communication
  2. lobby has some "admin" commands, if admin.txt exists in account directory
  5. exiting the lobby unauthenticates and dumps you back to the serverLoop
5. When user enters the gameLoop
  1. Game contains Rooms, Objects, Characters, Spells, Creatures, etc
  2. User selects character or can create a new one.  Character is saved
  3. User is placed in the starting room
  4. Game area has a "help" command, some features of the game are only learned through interation
  5. Characters are saved with every command
  6. User can 'quit' to go back to the lobby

### Developer Info ###
* Install Runtime and Dev packages
```
pip install -r requirements.txt
pip install -r requirements_dev.txt
```
* set up the git hooks
```
pre-commit install
```
* Run pytest to test
* While designed to be a centralized server, at present, everything is run locally and content is checked in via github.  This means that you can run your own server, make your own changes and make modifications without fear of breaking anything or affecting anyone else.
* Contributions can be made via pull requests in github.
