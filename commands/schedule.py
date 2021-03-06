import datetime
import json
import os.path
from socket import socket, AF_INET, SOCK_DGRAM
from typing import Optional, Union
import arrow

from utils.discord import help_me, Broadcaster, DiscordInteractive, Question
from utils.utils import Log, PickeledServerDict
import discord
from discord.ext import tasks
from utils import DATE_FORM, SEPARATOR

interact = DiscordInteractive.interact

pickle_file = "./config/schedule.pickle"

ping_channels = "./config/schedule-ping.json"
if not os.path.isfile(ping_channels):
    with open(ping_channels, "w") as t:
        json.dump(dict(), t)


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
        return date < self.time_of_event

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

    def __ne__(self, other):
        return self.time_of_event != other.time_of_event and self.description != other.description

    def __hash__(self):
        return hash((self.description, self.time_of_event, self.repeat_after_days, self.end_on, self.initial_time))

    def __str__(self):
        string = f"{arrow.get(self.time_of_event).humanize()} - {self.description}"
        if self.initial_time != self.time_of_event:
            string += f" {SEPARATOR} since {self.initial_time}"
        if self.repeat_after_days is not None:
            string += f" every {self.repeat_after_days} days"
        if self.end_on is not None:
            string += f" for another {arrow.get(self.end_on).humanize(only_distance=True)}"
        return string


eventsq: PickeledServerDict = PickeledServerDict(pickle_file)
eventsq.load()


@tasks.loop(seconds=30.0)
async def check_events():
    global eventsq
    eventsq.load()
    change = False
    for server in eventsq.dictionary:
        for i in eventsq.dictionary[server].copy():
            evnt = eventsq.dictionary[server][i]
            if evnt is None:
                del eventsq.dictionary[server][i]
                change = True
                continue
            if evnt.still_occurs(arrow.utcnow()):
                continue  # still waiting
            nxt = evnt.make_next()
            if nxt is not None:
                eventsq.dictionary[server][hash(nxt)] = nxt
                change = True
            # happening
            happened = await execute_event(evnt, server)
            if happened:
                del eventsq.dictionary[server][i]
                change = True
    if change:
        eventsq.save()


async def execute_event(event, guild_id):
    ping_id = ping_server(guild_id)
    if DiscordInteractive.client is None:
        Log.error("No client cant execute event")
        return False
    channel = DiscordInteractive.client.get_guild(guild_id).get_channel(ping_id)
    await channel.send(event.description)
    Log.log("event executed")
    return True


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
                  "\n\tskip -- Skips event once" \
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
    synonyms = ["sched", "events?"]

    async def call(self, package):
        global eventsq
        message, args, user_data = package["message_obj"], package["args"], package["user_obj"]
        DiscordInteractive.client = package["client"]

        if message.guild.id not in eventsq.dictionary:
            eventsq.dictionary[message.guild.id] = dict()

        if len(args) < 2:
            Log.error("No command provided")
            await help_me(message, self.command)
            return

        if args[1].lower() == "init":
            ping_server(message.guild.id, message.channel.id)
            interact(message.channel.send, f"{message.channel} is now the alert channel for {message.guild.name}")
            return

        if args[1].lower() in ["new", "add"]:  # todo make it so you can add event in one command
            if ping_server(message.guild.id) is None:
                interact(message.channel.send, "Please set a default ping channel")
                return

            event = self.new_event(message)
            if event is None:
                interact(message.channel.send, "Canceled")

            eventsq.load()
            eventsq.dictionary[message.guild.id][hash(event)] = event
            eventsq.save()
            return

        if args[1].lower() == "list":
            eventsq.load()
            if not eventsq.dictionary[message.guild.id]:
                interact(message.channel.send, "No events in this server")
                return
            events_str = "```\n"
            for i in eventsq.dictionary[message.guild.id].values():
                events_str += f"> {str(i)}"
                events_str += "\n\n"
            events_str += "```"
            interact(message.channel.send, events_str)
            return

        # if args[1].lower() == "edit":
        #     load_events() todo
        #     inx = self.pick_event(message)
        #     edit here
        #     save_events()
        #     return

        if args[1].lower() == "skip":
            eventsq.load()
            if not eventsq.dictionary[message.guild.id]:
                interact(message.channel.send, "No events in this server")
                return
            inx = self.pick_event(message)
            nxt = eventsq.dictionary[message.guild.id][inx].make_next()
            change = False
            if nxt is not None:
                eventsq.dictionary[message.guild.id][hash(nxt)] = nxt
                change = True
            del eventsq.dictionary[message.guild.id][inx]
            interact(message.channel.send, "Event skipped")
            if change:
                eventsq.save()
            return

        if args[1].lower() == "del":
            eventsq.load()
            if not eventsq.dictionary[message.guild.id]:
                interact(message.channel.send, "No events in this server")
                return
            inx = self.pick_event(message)
            del eventsq.dictionary[message.guild.id][inx]
            eventsq.save()
            interact(message.channel.send, "Event deleted")
            return

        await help_me(message, self.command)

    @staticmethod
    def pick_event(message):
        if message.guild.id not in eventsq.dictionary or not eventsq.dictionary[message.guild.id]:
            return None
        orig = interact(message.channel.send, "\u200b")
        liss = socket(AF_INET, SOCK_DGRAM)
        liss.bind(('', 12345))
        listner = Broadcaster(liss)
        quiz = Question(listner, orig, message)
        evn = eventsq.dictionary[message.guild.id]
        hashs = list(evn.keys())
        options = [f"created on {arrow.get(evn[i].initial_time).format(DATE_FORM)} - "
                   f"`{evn[i].description}`" for i in hashs]
        idx = quiz.multiple_choice("Pick an event", options)
        liss.close()
        interact(orig.delete)
        del quiz, liss, listner, message, orig
        return hashs[idx]

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
        new_event = Event(description, time_of_event_date_time, repeat_after_days, end_on_date_time)

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


check_events.start()
