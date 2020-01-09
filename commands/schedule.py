from socket import socket, AF_INET, SOCK_DGRAM

from utils import Log, help_me, json, Broadcaster, DiscordInteractive

interact = DiscordInteractive().interact


class Command:
    command = "schedule"
    description = "Schedule events."
    argsRequired = 1
    usage = "<command>"
    examples = [{
        'run': "sched init",
        'result': "Sets the current channel as ping channel."
    },
        {
            'run': "event new",
            'result': "Walks you through setting up a new event"
        }]
    synonyms = ["sched", "event"]

    async def call(self, package):
        message, args, user_data = package["message_obj"], package["args"], package["user_obj"]

        if len(args) < 2:
            Log.error("No command provided")
            await help_me(message, self.command)
            return

        elif args[1] == "init":
            self.pingServer(message.guild.id, message.channel.id)
            interact(message.channel.send, f"{message.channel} is now the pin ping channel for {message.guild.name}")
            return

        elif args[1] == "new":
            self.newEvent(message)
            return

    def pingServer(self, server, channel):
        with open("./serverSchedule.json", "wr") as serverList:
            srvs = json.load(serverList)
            srvs["pingPlace"][server] = channel
            json.dump(srvs, serverList, indent="  ", sort_keys=True)

    def newEvent(self, message):
        repeats = None
        start = None
        end = None

        liss = socket(AF_INET, SOCK_DGRAM)
        liss.bind(('', 12345))
        listner = Broadcaster(liss)
        interact(message.channel.send, "is the new event a:\n>>> `(1)` one time event\n`(2)` recurring event")
        while True:
            uInput = listner.receive()
            Log.log("input is", uInput)
            if Broadcaster.is_by_author(message, uInput):
                if uInput["content"].isnumeric():
                    num = int(uInput["content"])
                    if num == 1:
                        repeats = 0
                        break
                    elif num == 2:
                        repeats = True
                        break
                    else:
                        interact(message.channel.send, "`1` or `2`")
                        continue
                else:
                    interact(message.channel.send, "Please choose a number")
                    continue

        interact(message.channel.send, "The")
        while True:
            uInput = listner.receive()
            if Broadcaster.is_by_author(message, uInput):
                interact(message.channel.send, "bye")
