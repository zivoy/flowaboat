import json
import os

from utils.utils import Log

mudaWatchlist = dict()

muda_file = "./config/mudaSafe"

if os.path.exists(muda_file):
    with open(muda_file, "r") as serverList:
        allServers = json.load(serverList)
else:
    open(muda_file, "w").close()
    allServers = dict()


class Watcher:
    name = "badmuda"
    description = "Warns users if they use the Muda bot in the wrong channel."

    mudaId = "627115852944375808"
    mudaCommand = "$"

    trigger_description = f"if a user posts anything starting with a `{mudaCommand}` they will be put on a " \
                          f"watchlist and if muda ({mudaId}) responds it will trigger admin function"

    action_description = "once triggered the message by muda will be deleted and replaced with a warning"

    lengthMes = "@{0} this is a warning. you are in the wrong channel go to #{1}"

    warn = '**{2}**\n' \
           '<@!{0}> this is a warning. you are in the wrong channel go to <#{1}>\n' \
           '**{2}**'

    examples = [{
        'trigger': f"{mudaCommand}w",
        'action': warn.format("userID", "mudaHomeChannelID", "!" * 84)
    }]

    def trigger(self, message_obj, _, d):
        string, sender, server, channel = str(message_obj.content), str(message_obj.author.id), \
                                          str(message_obj.guild.id), str(message_obj.channel.id)

        if server not in mudaWatchlist:
            mudaWatchlist[server] = dict()

        if string.startswith(self.mudaCommand) or sender == self.mudaId:
            if server in allServers:
                if channel == allServers[server]:
                    return False, ""

                if string.startswith(self.mudaCommand) and sender not in mudaWatchlist[server]:
                    mudaWatchlist[server][channel] = sender
                    Log.log("adding {} to watchlist".format(sender))
                    return False, ""

                if channel in mudaWatchlist[server]:
                    length = len(self.lengthMes.format(message_obj.author.name, message_obj.channel.name))
                    return True, [mudaWatchlist[server][channel], allServers[server], "!" * int(length * 1.5)]

                return False, ""
        return False, ""

    async def action(self, message_obj, payload):
        msg = self.warn.format(*payload)
        Log.log("{0} is in the wrong chat".format(payload[0]))
        await message_obj.channel.send(msg)
        await message_obj.delete()
