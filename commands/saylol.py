from time import time

from random import choice

from utils.discord import DiscordInteractive
from utils.utils import Log

timeOut = 0  # 15  # in seconds
lolFile = "./config/lol.list"
users = dict()
lols = list()

with open(lolFile, "r", encoding="utf8") as lolList:
    for i in lolList:
        j = i.replace("\n", "")
        if not j:
            continue
        lols.append(j)

interact = DiscordInteractive.interact


class Command:
    command = "saylol"
    description = "the famous saylol command of redstoner\n" \
                  "https://git.redstoner.com/modules/tree/src/main/java/com/redstoner/modules/saylol\n" \
                  "https://web.archive.org/web/20190620184102/https://redstoner.com/forums/threads/4505-list-of-lols"
    argsRequired = 0
    usage = ""
    examples = [{
        'run': "lol",
        'result': "a random lol"
    }]
    synonyms = ["kek", "lol"]

    async def call(self, package):
        message_obj = package["message_obj"]
        string, sender, server, channel = str(message_obj.content), str(message_obj.author.id), \
                                          str(message_obj.guild.id), str(message_obj.channel.id)
        if server is None:
            server = "DM"

        if server not in users:
            users[server] = dict()

        if not lols:
            # no lols available
            return

        if sender in users[server]:
            if self.warnTime(users[server][sender], message_obj):
                return

        users[server][sender] = {"time": time(), "warned": False}

        name = message_obj.author.nick
        if name is None:
            name = message_obj.author.name

        interact(message_obj.channel.send, "`[lol] {0}`: {1}".format(name, choice(lols)
                                                                     .replace("\\", "\\\\")
                                                                     .replace("_", "\\_")
                                                                     .replace("*", "\\*")
                                                                     .replace("`", "\\`")
                                                                     .replace("|", "\\|")))

    def warnTime(self, user, message):
        lastLol = user["time"]
        if time() - lastLol < timeOut:
            secs = (timeOut - round((time() - lastLol) + .5))
            nextIn = f"You can't use saylol for another {secs}s."
            if not user["warned"]:
                interact(message.channel.send, nextIn)
            Log.log(nextIn)
            user["warned"] = True
            return True
        return False
