import datetime
import json
import os.path
import pickle
from socket import socket, AF_INET, SOCK_DGRAM
from typing import Optional

from utils.discord import help_me, Broadcaster, DiscordInteractive
from utils.utils import Log

interact = DiscordInteractive().interact

pickle_file = "./config/schedule.pickle"


def load_events():
    global events
    if not os.path.isfile('filename.txt'):
        save_events()
    with open(pickle_file, "rb") as pkl:
        events = pickle.load(pkl).sort()


def save_events():
    with open(pickle_file, "wb") as pkl:
        pickle.dump(events, pkl)


events = list()
load_events()


class Command:
    command = "schedule"
    description = "Schedule events.\n```\nPossible Commands:" \
                  "\n\tinit -- Sets the current channel as ping channel." \
                  "\n\tnew  -- Walks you through setting up a new event." \
                  "\n\tlist -- Lists all events." \
                  "\n\tdel  -- Deletes event" \
                  "\n\tedit -- Walks you through the process of editing an event\n```"
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

        if args[1].lower() == "init":
            self.pingServer(message.guild.id, message.channel.id)
            interact(message.channel.send, f"{message.channel} is now the pin ping channel for {message.guild.name}")
            return

        if args[1].lower() == "new":
            self.newEvent(message)
            return

        if args[1].lower() == "list":
            # todo
            return

        if args[1].lower() == "edit":
            # todo
            return

        if args[1].lower() == "del":
            # todo
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
                break


class Event:
    def __init__(self, description: str, time_of_event: datetime.datetime,
                 repeat_after_days: Optional[int] = None, end_on: Optional[datetime.datetime] = None):
        self.description: str = description
        self.time_of_event: datetime.datetime = time_of_event
        self.repeat_after_days: Optional[int] = repeat_after_days
        self.end_on: Optional[datetime.datetime] = end_on

    def still_occurs(self, date: datetime.datetime):
        return date > self.time_of_event

    def make_next(self):
        if self.repeat_after_days is not None:
            new_date = self.time_of_event + datetime.timedelta(days=self.repeat_after_days)
            next_event = Event(self.description, new_date,
                               self.repeat_after_days, self.end_on)
            if self.end_on is not None:
                if new_date <= self.end_on:
                    return next_event
                return None
            return next_event
        return None

    def __lt__(self, other):
        return self.time_of_event < other.time_of_event

    def __ne__(self, other):
        return self.time_of_event != other.time_of_event
