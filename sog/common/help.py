''' help sybsystem functions and data '''

import logging

# Original commands:
#
# accept, appeal, attack, backstab, block, break, bribe, brief, buy, cast,
# catalog, circle, climb, clock, close, d (down), down, draw, drink, drop,
# e, east, echo, end, enter, examine, exit, experience, feint, file, follow,
# get, go, health, help, hide, hint, hit, hold, identify, information,
# inventory, kill, leave, list, lock, look, lose, n, north, offer, open, out,
# panic, parley, parry, pawn, picklock, put, quit, read, repair, return, run,
# s, save, say, search, sell, send, smash, south, status, steal, strike,
# suicide, take, talk, teach, thrust, track, train, turn, u, unlock, up, use,
# w, wear, west, where, who, wield, yell.


lobbyCmds = {
    'info': 'Get account information',
    'game': 'Play the SoG game',
    'alt': 'Set the lobby prompts to alt mode'
  }

gameCommands = {
    'information': {
        'attributes': {
            'alt': 'attr',
            'shortdesc': 'show character\'s attributes',
            'detailed': ''
         },
        'experience': {
            'alt': 'exp',
            'shortdesc': 'show character\'s level and experience',
            'detailed': ''
         },
        'health': {
            'alt': 'hea',
            'shortdesc': 'show character\'s health and magic',
            'detailed': ''
         },
        'info': {
            'alt': 'info',
            'shortdesc': 'Get full character information',
            'detailed': ''
        },
        'skills': {
            'alt': '',
            'shortdesc': 'show character\'s acquired skills',
            'detailed': ''
         }
    },
    'combat': {
        'attack': {
            'alt': 'att',
            'shortdesc': 'standard attack',
            'detailed': ''
         },
        'parry': {
            'alt': 'par',
            'shortdesc': 'weak attack with a block',
            'detailed': 'does less damage, receive less damage'
         },
        'lunge': {
            'alt': 'lun',
            'shortdesc': 'powerful attack, making yourself vulnerable',
            'detailed': 'does more damage, receive more damage'
         }
    },
    'magic': {
        'cast': {
            'alt': '',
            'shortdesc': 'cast a spell',
            'detailed': ''
         },
        'study': {
            'alt': '',
            'shortdesc': 'study a scroll to learn a spell',
            'detailed': ''
         },
        'use': {
            'alt': '',
            'shortdesc': 'use a magic item or scroll',
            'detailed': ''
         }
      },
    'other': {
        'hide': {
            'alt': '',
            'shortdesc': 'hide in the shadows',
            'detailed': 'if hidden, plays, creatures, and npcs can\'t see you'
        },
        'equip': {
            'alt': 'wear',
            'shortdesc': 'equip armor, weapons, or gear',
            'detailed': ''
        },
        'talk': {
            'alt': '',
            'shortdesc': 'talk to a npc',
            'detailed': ''
        }
    },
}


def enterHelp(svrObj):
    svrObj.spoolOut("Welcome to the help subsystem")
    contextMenu = ""
    while True:
        prompt = ("Menu:\n" +
                  contextMenu +
                  "  topics - show the top level list of topics\n" +
                  "  exit   - quit help and go back to the game\n" +
                  "What would you like help with? : ")
        helpIn = svrObj.promptForInput(prompt)
        if helpIn == 'exit' or helpIn == 'quit':
            break
        elif helpIn == 'topics':
            contextMenu = ''
            for oneTopic in gameCommands.keys():
                logging.debug("topic: " + oneTopic)
                contextMenu = (contextMenu + "  " + oneTopic + " - " +
                               "info about " + oneTopic + "\n")
        elif helpIn in gameCommands.keys():
            contextMenu = ''
            for oneCommand in gameCommands[helpIn].keys():
                contextMenu = (contextMenu + "  " + oneCommand + " - " +
                               gameCommands[helpIn][oneCommand]['shortdesc'] +
                               "\n")
        else:
            svrObj.spoolOut("Unknown help topic " + helpIn)

    return(None)
