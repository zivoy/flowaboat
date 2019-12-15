import os, json
from utils import Log

mudaId = "627115852944375808"
mudaCommand = "$"
mudaWatchlist = dict()

if os.path.exists("./mudaSafe"):
    with open("./mudaSafe", "r") as serverList:
        allServers = json.load(serverList)
else:
    open("./mudaSafe", "w").close()
    allServers = dict()


class Watcher:
    name = "badmuda"
    description = "Warns Users if they use the Muda bot in the wrong channel."

    def trigger(self, message_obj):
        string, sender, server, channel = str(message_obj.content), str(message_obj.author.id), \
                                          str(message_obj.guild.id), str(message_obj.channel.id)

        if server not in mudaWatchlist:
            mudaWatchlist[server] = dict()

        if string.startswith(mudaCommand) or sender == mudaId:
            if server in allServers:
                if channel == allServers[server]:
                    return False, ""
                else:
                    if string.startswith(mudaCommand) and sender not in mudaWatchlist[server]:
                        mudaWatchlist[server][channel] = sender
                        Log.log("adding {} to watchlist".format(sender))
                        return False, ""
                    else:
                        if channel in mudaWatchlist[server]:
                            return True, [mudaWatchlist[server][channel], allServers[server]]
                        else:
                            return False, ""
        return False, ""

    async def action(self, message_obj, payload):
        msg = '**!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!**\n' \
              '<@{0}> this is a warning. you are in the wrong channel go to <#{1}>\n' \
              '**!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!**'.format(*payload)
        Log.log("{0} is in the wrong chat".format(payload[0]))
        await message_obj.channel.send(msg)
        try:
            await message_obj.delete()
        except:
            pass
