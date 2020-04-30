''' help sybsystem functions and data '''

from common.general import logger

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
         },
        'purse': {
             'alt': '',
             'shortdesc': 'show character\'s acquired skills',
             'detailed': ''
         },
        'identify': {
             'alt': '',
             'shortdesc': 'get full info about a player, object, or creature',
             'detailed': 'limited ability obtained through experience'
         },
        'file': {
             'alt': '',
             'shortdesc': 'show my list of characters',
             'detailed': ''
         },
        'clock': {
             'alt': 'now',
             'shortdesc': 'Get the real world time',
             'detailed': ''
         },
        'who': {
             'alt': '',
             'shortdesc': 'Show who else is in the game',
             'detailed': ''
         }
    },
    'combat': {
        'attack': {
            'alt': 'hit, strike',
            'shortdesc': 'standard attack',
            'detailed': ''
         },
        'backstab': {
            'alt': '',
            'shortdesc': 'A viscious attack that makes you vulnerable',
            'detailed': 'You must be hidden to backstab'
         },
        'block': {
            'alt': 'parry',
            'shortdesc': 'weak attack with a defensive block',
            'detailed': 'does less damage, receive less damage'
         },
        'kill': {
            'alt': '',
            'shortdesc': 'an aggressive attack',
            'detailed': 'an aggressive attack'
         },
        'circle': {
            'alt': '',
            'shortdesc': 'move around opponent for better attack',
            'detailed': 'move around opponent for better attack'
         },
        'feint': {
            'alt': '',
            'shortdesc': 'a mock attack to confuse your opponent',
            'detailed': 'a mock attack to confuse your opponent'
         },
        'thrust': {
            'alt': 'lunge',
            'shortdesc': 'powerful attack, making yourself vulnerable',
            'detailed': 'does more damage, receive more damage'
         },
        'panic': {
            'alt': 'run',
            'shortdesc': 'drop weapon and run away',
            'detailed': 'likely to escape, even when there are blockers'
         }
    },
    'magic': {
        'cast': {
            'alt': '',
            'shortdesc': 'cast a spell',
            'detailed': 'Usage: cast <spell> <target> [#]'
         },
        'study': {
            'alt': 'read',
            'shortdesc': 'study a scroll to learn a spell',
            'detailed': 'study a scroll to learn a spell'
         },
        'turn': {
            'alt': '',
            'shortdesc': 'turn an undead creature to dust',
            'detailed': 'turn an undead creature to dust'
         },
        'use': {
            'alt': '',
            'shortdesc': 'use a magic item or scroll',
            'detailed': ''
         }
      },
    'movement': {
        'n, s, e, w, u, d, o': {
            'alt': '',
            'shortdesc': 'directions that you can travel',
            'detailed': 'directions that you can travel'
         },
        'enter': {
            'alt': 'go',
            'shortdesc': 'enter a door or other object that can be entered',
            'detailed': 'enter a door or other object that can be entered'
         },
        'climb': {
            'alt': 'go',
            'shortdesc': 'climb a ladder or other object that can be climbed',
            'detailed': 'climb a ladder or other object that can be climbed'
         },
        'follow': {
            'alt': '',
            'shortdesc': 'follow another player',
            'detailed': 'move with another character, unless you get lost'
         },
        'lose': {
            'alt': '',
            'shortdesc': 'attempt to lose any players following you',
            'detailed': 'Usage: lose <name>'
         }
      },
    'transactions': {
        'catalog': {
            'alt': 'list',
            'shortdesc': 'view the catalog of items at a shop',
            'detailed': 'List of items that a shop has to sell'
        },
        'buy': {
            'alt': '',
            'shortdesc': 'buy an item.',
            'detailed': 'Usage: buy <item_number>'
        },
        'sell': {
            'alt': 'pawn',
            'shortdesc': 'sell an item.',
            'detailed': 'Usage: sell <item_number> [#]'
        },
        'balance': {
            'alt': '',
            'shortdesc': 'view your bank account balance',
            'detailed': 'see how many shillings you have in the bank'
        },
        'withdraw': {
            'alt': '',
            'shortdesc': 'take funds out of the bank',
            'detailed': 'Usage: withdraw <amount>'
        },
        'deposit': {
            'alt': '',
            'shortdesc': 'put funds into the bank',
            'detailed': 'Usage: deposit <amount>'
        },
        'repair': {
            'alt': '',
            'shortdesc': 'repair a used item',
            'detailed': 'Usage: repair <item>'
        },
        'offer': {
            'alt': '',
            'shortdesc': 'offer an item to another player',
            'detailed': 'Usage: offer <item> for <amount>'
        },
        'accept': {
            'alt': '',
            'shortdesc': 'repair a used item',
            'detailed': 'repair a used item.  Usage: replair <item>'
        }
    },
    'character_interaction': {
        'appeal': {
            'alt': '',
            'shortdesc': 'complain to the dm',
            'detailed': 'Usage: <appeal>'
        },
        'parley': {
            'alt': 'talk',
            'shortdesc': 'talk to a npc',
            'detailed': 'talk to a npc'
        },
        'bribe': {
            'alt': '',
            'shortdesc': 'offer a npc money to go away',
            'detailed': 'Usage: bribe <creature> [#]'
        },
        'say': {
            'alt': '',
            'shortdesc': 'say something to everyone in the room',
            'detailed': 'Usage: say <txt>'
        },
        'shout': {
            'alt': 'yell',
            'shortdesc': 'Yell something to nearby players',
            'detailed': 'Everyone in the room and ajoining rooms can hear you'
        },
        'laugh': {
            'alt': '',
            'shortdesc': 'React amusingly',
            'detailed': 'React amusingly'
        },
        'teach': {
            'alt': '',
            'shortdesc': 'teach someone else a spell that you know',
            'detailed': 'Usage: teach <spell> <name> [#]'
        },
        'whisper': {
            'alt': '',
            'shortdesc': 'talk to someone in particular, may be overheard',
            'detailed': 'Everyone in the room and ajoining rooms can hear you'
        }
    },
    'object_interaction': {
        'examine': {
            'alt': '',
            'shortdesc': 'look at a room, object, character, or creature',
            'detailed': 'Usage: look <object>'
        },
        'get': {
            'alt': 'take',
            'shortdesc': 'get an object',
            'detailed': 'Usage: get <object> [#] [from <container>] [#]'
        },
        'drop': {
            'alt': '',
            'shortdesc': 'drop an object',
            'detailed': 'Usage: drop <object> [#]'
        },
        'put': {
            'alt': '',
            'shortdesc': 'put an object in a container',
            'detailed': 'Usage: put <object> [#] in <container>'
        },
        'equip': {
            'alt': 'wear, weild, hold, draw',
            'shortdesc': 'equip armor, weapons, or gear',
            'detailed': 'equip armor, weapons, or gear'
        },
        'unequip': {
            'alt': 'remove, return',
            'shortdesc': 'unequip armor, weapons, or gear',
            'detailed': 'unequip armor, weapons, or gear'
        },
        'use': {
            'alt': 'drink',
            'shortdesc': 'use an object in your inventory',
            'detailed': 'Usage: use <object> [#] on [<target> [#]]'
        },
        'open': {
            'alt': '',
            'shortdesc': 'open a door, container, or similar object',
            'detailed': 'Usage: open <object> [#]'
        },
        'close': {
            'alt': '',
            'shortdesc': 'close a door, container, or similar object',
            'detailed': 'Usage: close <object> [#]'
        },
        'lock': {
            'alt': '',
            'shortdesc': 'lock a door or container with a key ',
            'detailed': 'Usage: lock <object> [#] with <key> [#]'
        },
        'unlock': {
            'alt': '',
            'shortdesc': 'unlock a door or container with a key',
            'detailed': 'Usage: lock <object> [#] with <key> [#]'
        },
        'picklock': {
            'alt': '',
            'shortdesc': 'unlock a door or container without a key',
            'detailed': 'Usage: picklock <object> [#]'
        },
        'steal': {
            'alt': '',
            'shortdesc': 'steal from a player',
            'detailed': 'Usage: steal <obj> [#] <name> [#]'
        }
    },
    'other': {
        'hide': {
            'alt': '',
            'shortdesc': 'hide in the shadows',
            'detailed': 'if hidden, plays, creatures, and npcs can\'t see you'
        },
        'search': {
            'alt': '',
            'shortdesc': 'search for hidden objects creatures, or characters',
            'detailed': 'Usage: search'
        },
        'track': {
            'alt': '',
            'shortdesc': 'look for tracks to find out where last player went',
            'detailed': 'Usage: track'
        },
        'train': {
            'alt': '',
            'shortdesc': 'train to increase your level',
            'detailed': 'Requires that you find the proper training area'
        },
        'prompt': {
            'alt': 'full, brief',
            'shortdesc': 'change the prompt and room messages',
            'detailed': 'Usage: prompt'
        },
        'suicide': {
            'alt': '',
            'shortdesc': 'quit and permanently delete character',
            'detailed': 'Usage: suicide'
        },
        'exit': {
            'alt': 'quit',
            'shortdesc': 'leave the game',
            'detailed': 'leave the game.  Inventory truncated to 12 items'
        }
    },
}


def enterHelp(client):
    client.spoolOut("Welcome to the help subsystem")
    contextMenu = ""
    while True:
        prompt = ("Menu:\n" +
                  contextMenu +
                  "--------------------------------------------\n" +
                  "  topics - show the top level list of topics\n" +
                  "  exit   - quit help and go back to the game\n" +
                  "What would you like help with? : ")
        helpIn = client.promptForInput(prompt)
        if helpIn == 'exit' or helpIn == 'quit':
            break
        elif helpIn == 'topics':
            contextMenu = ''
            for oneTopic in gameCommands.keys():
                logger.debug("topic: " + oneTopic)
                contextMenu = (contextMenu + "  " + oneTopic + " - " +
                               "info about " + oneTopic + "\n")
        elif helpIn in gameCommands.keys():
            contextMenu = ''
            for oneCommand in gameCommands[helpIn].keys():
                contextMenu = (contextMenu + "  " + oneCommand + " - " +
                               gameCommands[helpIn][oneCommand]['shortdesc'] +
                               "\n")
        else:
            client.spoolOut("Unknown help topic " + helpIn + '\n')

    return(None)
