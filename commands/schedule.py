import datetime
import json
import os.path
import pickle
from socket import socket, AF_INET, SOCK_DGRAM
from typing import Optional, Union
import arrow

from utils.discord import help_me, Broadcaster, DiscordInteractive, Question
from utils.utils import Log
import discord
from utils import DATE_FORM

interact = DiscordInteractive.interact

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
    usage = "<command> [any data required]"
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
            event = self.newEvent(message)
            if event is None:
                interact(message.delete)
                interact(message.channel.send, "Canceled")

            events.append(event)
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

    @staticmethod
    def pingServer(server, channel):
        with open("./serverSchedule.json", "wr") as serverList:
            srvs = json.load(serverList)
            srvs["pingPlace"][server] = channel
            json.dump(srvs, serverList, indent="  ", sort_keys=True)

    @staticmethod
    def newEvent(message: discord.Message):
        repeat_after_days = None
        end_on = None
        end_on_date_time = None
        m=discord.Embed(description="Say stop anytime to cancel")
        orig: discord.Message = interact(message.channel.send, "\u200b", embed=m)

        liss = socket(AF_INET, SOCK_DGRAM)
        liss.bind(('', 12345))
        listner = Broadcaster(liss)
        quiz = Question(listner, orig, message)

        description = quiz.get_string("What is the message of the event?", confirm=True)
        if isinstance(description, bool) and not description:
            return None

        time_of_event, timezone = quiz.get_date("What is the time of this event?", True)
        if isinstance(time_of_event, bool) and not time_of_event:
            return None
        time_of_event_date_time = time_of_event.datetime

        reocur = quiz.multiple_choice("Is the new event a:", ["one time event", "recurring event"])
        if isinstance(reocur, bool) and not reocur:
            return None

        if reocur:
            repeat_after_days = quiz.get_real_number(
                "What is the period of the repeating event in days", is_positive=True, minimum=1)
            if isinstance(repeat_after_days, bool) and not repeat_after_days:
                return None

            end_on, _ = quiz.get_date("When does this event end?", False, timezone)
            if isinstance(end_on, bool) and not end_on:
                return None

        if end_on is not None:
            end_on_date_time = end_on.datetime

        interact(orig.delete)
        new_event = Event(description, time_of_event_date_time, repeat_after_days, end_on_date_time)
        event_str = f"Creating event\n```\n{description}\n```\n"
        event_str += f"Will happen {time_of_event.humanize()} ({time_of_event.format(DATE_FORM)})\n"
        if repeat_after_days is not None:
            event_str += f"And will repeat every {repeat_after_days} day{'s' if repeat_after_days>1 else ''}\n"
        if end_on is not None:
            event_str += f"it will end {end_on.humanize()} ({end_on.format(DATE_FORM)})"
        else:
            event_str += "It will never end unless deleted"
        interact(message.channel.send, event_str)
        return new_event


class Event:
    def __init__(self, description: str, time_of_event: datetime.datetime,
                 repeat_after_days: Optional[Union[int, float]] = None, end_on: Optional[datetime.datetime] = None,
                 initial_time: Optional[datetime.datetime] = None):
        self.description: str = description
        self.time_of_event: datetime.datetime = time_of_event
        self.repeat_after_days: Optional[int] = repeat_after_days
        self.end_on: Optional[datetime.datetime] = end_on
        if initial_time is None:
            self.initial_time = time_of_event
        else:
            self.initial_time = initial_time

    def still_occurs(self, date: datetime.datetime):
        return date > self.time_of_event

    def make_next(self):
        if self.repeat_after_days is not None:
            new_date = self.time_of_event + datetime.timedelta(days=self.repeat_after_days)
            next_event = Event(self.description, new_date, self.repeat_after_days,
                               self.end_on, self.initial_time)
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
