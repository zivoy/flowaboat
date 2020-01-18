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
from discord.ext import tasks
from utils import DATE_FORM, SEPARATOR

interact = DiscordInteractive.interact

pickle_file = "./config/schedule.pickle"

ping_channels = "./config/schedule-ping.json"
if not os.path.isfile(ping_channels):
    with open(ping_channels, "w") as t:
        json.dump(dict(), t)


def load_events():
    global events
    if not os.path.isfile('filename.txt'):
        save_events()
    with open(pickle_file, "rb") as pkl:
        events_temp = pickle.load(pkl).sort()
        if events_temp is None:
            events_temp = list()
        for i in events_temp:  # todo make nicer use sets
            for j in events.copy():
                if not i != j:
                    break
            else:
                events.append(i)
        #events = list(set(events).union(events_temp))


def save_events():
    with open(pickle_file, "wb") as pkl:
        pickle.dump(events, pkl)


events = list()
load_events()


@tasks.loop(seconds=30.0)
async def check_events():
    global events
    new_events = list()
    tmp = events.copy()
    for j, i in list(enumerate(events))[::-1]:
        if i.still_occurs(arrow.utcnow()):
            continue  # still waiting
        else:
            nxt = i.make_next()
            if nxt is not None:
                new_events.append(nxt)
            # happening
            await execute_event(i)
            del events[j]
    events.extend(new_events)
    if tmp != events:
        save_events()


async def execute_event(event):
    ping_id = ping_server(event.guild)
    channel = DiscordInteractive.client.get_guild(event.guild).get_channel(ping_id)
    await channel.send(event.description)
    Log.log("event executed")


def ping_server(server, channel=None):
    with open(ping_channels, "r") as serverList:
        srvs = json.load(serverList)
    if channel is None:
        if str(server) in srvs:
            return srvs[str(server)]
        return None
    with open(ping_channels, "w") as serverList:
        srvs[str(server)] = channel
        json.dump(srvs, serverList, indent="  ", sort_keys=True)


class Command:
    command = "schedule"
    description = "Schedule events.\n```\nPossible Commands:" \
                  "\n\tinit -- Sets the current channel as ping channel." \
                  "\n\tnew  -- Walks you through setting up a new event." \
                  "\n\tlist -- Lists all events." \
                  "\n\tdel  -- Deletes event" \
                  "\n\tedit -- Walks you through the process of editing an event -- todo\n```"
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
        global events
        message, args, user_data = package["message_obj"], package["args"], package["user_obj"]
        DiscordInteractive.client = package["client"]

        if len(args) < 2:
            Log.error("No command provided")
            await help_me(message, self.command)
            return

        if args[1].lower() == "init":
            ping_server(message.guild.id, message.channel.id)
            interact(message.channel.send, f"{message.channel} is now the pin ping channel for {message.guild.name}")
            return

        if args[1].lower() in ["new", "add"]:
            if ping_server(message.guild.id) is None:
                interact(message.channel.send, "Please set a default ping channel")
                return

            event = self.new_event(message)
            if event is None:
                interact(message.channel.send, "Canceled")

            load_events()
            events.append(event)
            save_events()
            return

        if args[1].lower() == "list":
            load_events()
            events_str = "```\n"
            for i in events:
                events_str += f"{arrow.get(i.time_of_event).humanize()} - {i.description}"
                if i.initial_time != i.time_of_event:
                    events_str += f" {SEPARATOR} since {i.initial_time}"
                events_str+="\n"
            events_str += "```"
            interact(message.channel.send, events_str)
            return

        # if args[1].lower() == "edit":
        #     load_events() todo
        #     inx = self.pick_event(message)
        #     edit here
        #     save_events()
        #     return

        if args[1].lower() == "del":
            load_events()
            inx = self.pick_event(message)
            del events[inx]
            save_events()
            return

        await help_me(message, self.command)

    @staticmethod
    def pick_event(message):
        orig = interact(message.channel.send, "\u200b")
        liss = socket(AF_INET, SOCK_DGRAM)
        liss.bind(('', 12345))
        listner = Broadcaster(liss)
        quiz = Question(listner, orig, message)
        options = [f"created on {arrow.get(i.initial_time).format(DATE_FORM)} - `{i.description}`" for i in events]
        idx = quiz.multiple_choice("Pick an event", options)
        liss.close()
        interact(orig.delete)
        del quiz, liss, listner, message, orig
        return idx

    @staticmethod
    def new_event(message: discord.Message):
        repeat_after_days = None
        end_on = None
        end_on_date_time = None
        m = discord.Embed(description="Say stop anytime to cancel")
        orig: discord.Message = interact(message.channel.send, embed=m)

        liss = socket(AF_INET, SOCK_DGRAM)
        liss.bind(('', 12345))
        listner = Broadcaster(liss)
        quiz = Question(listner, orig, message)

        description = quiz.get_string("What is the message of the event?", confirm=True)
        if isinstance(description, bool) and not description:
            interact(orig.delete)
            return None

        time_of_event, timezone = quiz.get_date("What is the time of this event?", True)
        if isinstance(time_of_event, bool) and not time_of_event:
            interact(orig.delete)
            return None
        time_of_event_date_time = time_of_event.to("utc").datetime

        reocur = quiz.multiple_choice("Is the new event a:", ["one time event", "recurring event"])
        if isinstance(reocur, bool) and not reocur:
            interact(orig.delete)
            return None

        if reocur:
            repeat_after_days = quiz.get_real_number(
                "What is the period of the repeating event in days", is_positive=True, minimum=1)
            if isinstance(repeat_after_days, bool) and not repeat_after_days:
                interact(orig.delete)
                return None

            end_on, _ = quiz.get_date("When does this event end?", False, timezone)
            if isinstance(end_on, bool) and not end_on:
                interact(orig.delete)
                return None

        if end_on is not None:
            end_on_date_time = end_on.to("utc").datetime

        interact(orig.delete)
        new_event = Event(description, time_of_event_date_time, message.guild.id,
                          repeat_after_days, end_on_date_time)

        event_str = f"Creating event\n```\n{description}\n```\n"
        event_str += f"Will happen {time_of_event.humanize()} ({time_of_event.format(DATE_FORM)} " \
                     f"UTC{'+' if not timezone < 0 else ''}{timezone})"
        if time_of_event.isoformat() != time_of_event.to("utc").isoformat():
            event_str += f" {SEPARATOR} ({time_of_event.to('utc').format(DATE_FORM)} UTC)"
        event_str += "\n"
        if repeat_after_days is not None:
            event_str += f"And will repeat every {repeat_after_days} day{'s' if repeat_after_days>1 else ''}\n"
        if end_on is not None:
            event_str += f"it will end {end_on.humanize()} ({end_on.format(DATE_FORM)} " \
                         f"UTC{'+' if timezone >= 0 else ''}{timezone}))"
            if end_on.isoformat() != end_on.to("utc").isoformat():
                event_str += f" {SEPARATOR} ({end_on.to('utc').format(DATE_FORM)} UTC)"
        elif repeat_after_days is not None:
            event_str += "It will never end unless deleted"
        interact(message.channel.send, event_str)
        liss.close()
        del quiz, liss, listner, message, orig
        return new_event


class Event:
    def __init__(self, description: str, time_of_event: datetime.datetime, guild: int,
                 repeat_after_days: Optional[Union[int, float]] = None, end_on: Optional[datetime.datetime] = None,
                 initial_time: Optional[datetime.datetime] = None):
        self.description: str = description
        self.guild = guild
        self.time_of_event: datetime.datetime = time_of_event
        self.repeat_after_days: Optional[int] = repeat_after_days
        self.end_on: Optional[datetime.datetime] = end_on
        if initial_time is None:
            self.initial_time = time_of_event
        else:
            self.initial_time = initial_time

    def still_occurs(self, date: datetime.datetime):
        return date < self.time_of_event

    def make_next(self):
        if self.repeat_after_days is not None:
            new_date = self.time_of_event + datetime.timedelta(days=self.repeat_after_days)
            next_event = Event(self.description, new_date, self.guild, self.repeat_after_days,
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
        return self.time_of_event != other.time_of_event and self.description != other.description


check_events.start()
