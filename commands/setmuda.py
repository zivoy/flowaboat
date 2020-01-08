import json
from utils import Log


class Command:
    command = "set-muda"
    description = "set safe place for muda"
    argsRequired = 0
    usage = ""
    examples = [{
        'run': "set-muda",
        'result': "set as muda dump"
    }]
    synonyms = ["setmuda", "mudainit", "muda-init"]

    async def call(self, package):
        message = package["message_obj"]
        server = message.guild.id
        channel = message.channel.id
        with open("./mudaSafe", "r") as serverList:  # will change
            try:
                allServers = json.load(serverList)
            except:
                allServers = dict()
            allServers[server] = str(channel)
        with open("./mudaSafe", "w") as serverList:
            json.dump(allServers, serverList, indent="  ", sort_keys=True)
        msg = "<#{0}> is now the default channel for {1}".format(channel, server)
        Log.log(msg)
        await message.channel.send(msg)
