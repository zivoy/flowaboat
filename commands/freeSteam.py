import json
import os.path

import arrow
import cloudscraper
import discord
import regex
import requests
from bs4 import BeautifulSoup
from discord.ext import tasks

from utils.discord import DiscordInteractive, help_me
from utils.utils import Log, PickeledServerDict

scraper = cloudscraper.create_scraper()

interact = DiscordInteractive.interact

pickle_file = "./config/notified.pickle"

ping_channels = "./config/free-ping.json"
if not os.path.isfile(ping_channels):
    with open(ping_channels, "w") as t:
        json.dump(dict(), t)


class steamItem:
    def __init__(self, name, steamId, promoType, promoStart, promoEnd, databaseUrl):
        self.name = name
        self.steamId = str(steamId)
        self.promoType = promoType
        self.promoStart = promoStart
        self.promoEnd = promoEnd
        self.databaseUrl = databaseUrl

    def getApp(self):
        return "https://store.steampowered.com/app/" + self.steamId

    def getAppInfo(self):
        return requests.get("https://store.steampowered.com/api/appdetails?appids=" + self.steamId).json()[self.steamId]

    def getImgUrl(self, small=False):
        aug = ""
        if small:
            aug = "_292x136"

        return f"http://cdn.akamai.steamstatic.com/steam/apps/{self.steamId}" \
               f"/header{aug}.jpg?t={arrow.utcnow().timestamp}"

    def __str__(self):
        txt = self.name.replace("\n", "\\n")
        return f"{self.steamId} - {txt} - {self.promoType} deal started " \
               f"{self.promoStart.humanize()} and ends {self.promoEnd.humanize()}"

    def __hash__(self):
        return hash((self.steamId, self.promoType,
                     self.promoStart, self.promoEnd))

    def __eq__(self, other):
        if not isinstance(other, steamItem):
            return False

        return (self.steamId == other.steamId) and \
               (self.promoType == other.promoType) and \
               (self.promoStart == other.promoStart) and \
               (self.promoEnd == other.promoEnd)

    def embed(self):
        gameData = self.getAppInfo()

        title = "Free Game!"
        desc = self.name

        if gameData["success"]:
            title = self.name
            desc = gameData["data"]["short_description"]

        embed = discord.Embed(title=title, description=desc,
                              url=self.getApp(), color=0x1b2838,
                              timestamp=arrow.utcnow().datetime)

        embed.set_thumbnail(url="https://steamcommunity-a.akamaihd.net/public/shared/images/header/"
                                f"globalheader_logo.png?t={arrow.utcnow().timestamp}")

        embed.set_image(url=self.getImgUrl())

        if gameData["success"]:
            embed.add_field(name="**Normally priced at**",
                            value=gameData["data"]["price_overview"]["initial_formatted"], inline=True)
        embed.set_author(name="SteamDB", icon_url="https://steamdb.info/static/logos/512px.png",
                         url=f"https://steamdb.info{self.databaseUrl}")

        embed.add_field(name="**Promotion Started**", value=self.promoStart.humanize(), inline=True)
        embed.add_field(name="**Promotion ends**", value=self.promoEnd.humanize(), inline=True)

        return embed


notified: PickeledServerDict = PickeledServerDict(pickle_file)
notified.load()


@tasks.loop(hours=10)  # not making it 12 for some variety
async def check_sales():
    await notify_sales()
    removeOutstanding()


def removeOutstanding():
    global notified
    notified.load()
    if "notified" not in notified.dictionary:
        notified.dictionary["notified"] = dict()
    change = False
    for server in notified.dictionary["notified"]:
        for i in notified.dictionary["notified"][server].copy():
            if i.promoEnd < arrow.utcnow():
                notified.dictionary["notified"][server].remove(i)
                change = True
    if change:
        notified.save()


async def notify_sales():
    url = "https://steamdb.info/upcoming/free/"
    page = scraper.get(url)
    # page = requests.get(url, headers={'user-agent': 'Mozilla/5.0 ()'})
    soup = BeautifulSoup(page.content, 'html.parser')

    table = soup.find("tbody")
    elements = table.findAll("tr")

    available = list()

    for i in elements:
        steamid = i.attrs["data-appid"]
        dbloc = i.findAll("a")[1].attrs["href"]
        tablePart = i.findAll("td")
        name = tablePart[1].text.replace("\n\n", "")
        promoType = tablePart[3].text.strip(" ").lower()
        start = tablePart[4].attrs["data-sort"]
        end = tablePart[5].attrs["data-sort"]
        start = arrow.get(start, "X")
        end = arrow.get(end, "X")
        r = steamItem(name, steamid, promoType, start, end, dbloc)

        available.append(r)
    keepable = [i for i in available if i.promoType == "keep"]
    await notify(keepable)


async def notify(items):
    global notified
    notified.load()
    change = False
    with open(ping_channels, "r") as serverList:
        srvs = json.load(serverList)
    for server in srvs:
        if server not in notified.dictionary["notified"]:
            notified.dictionary["notified"][server] = set()
        for i in [i for i in items if i not in notified.dictionary["notified"][server]]:
            ping_stats = ping_server(server)
            if DiscordInteractive.client is None:
                Log.error("No client cant notify users")
                continue
            channel = DiscordInteractive.client.get_guild(int(server)).get_channel(ping_stats["channel"])
            await channel.send(content=ping_stats["role"], embed=i.embed())
            notified.dictionary["notified"][server].add(i)
            change = True
    if change:
        notified.save()


def ping_server(server, channel=None, pingRole=None):
    with open(ping_channels, "r") as serverList:
        srvs = json.load(serverList)
    if channel is None:
        if str(server) in srvs:
            return srvs[str(server)]
        return None
    with open(ping_channels, "w") as serverList:
        srvs[str(server)] = {"channel": channel, "role": pingRole}
        json.dump(srvs, serverList, indent="  ", sort_keys=True)


class Command:
    command = "freeSteam"
    description = "Notify of free steam games"
    argsRequired = 1
    usage = "<pingrole>"
    examples = [{
        'run': "freeSteam pingrole",
        'result': "Sets the current channel as ping channel."
    }]
    synonyms = ["free-?now"]

    async def call(self, package):
        message, args = package["message_obj"], package["args"]
        DiscordInteractive.client = package["client"]

        if regex.match("free-?now", args[0]):
            if str(message.guild.id) not in notified.dictionary["notified"]:
                interact(message.channel.send, "Please first run `freeSteam <pingrole>` in the "
                                               "channel you want pinging to happen")
                return

            removeOutstanding()
            embed = discord.Embed(title="Games Available Now!", color=0x1b2838,
                                  timestamp=arrow.utcnow().datetime)

            embed.set_thumbnail(url="https://steamcommunity-a.akamaihd.net/public/shared/images/header/"
                                    f"globalheader_logo.png?t={arrow.utcnow().timestamp}")

            for i in sorted(notified.dictionary["notified"][str(message.guild.id)], key=lambda x: x.promoEnd):
                embed.add_field(name=i.name, value=f"{i.getApp()}\noffer ends {i.promoEnd.humanize()}", inline=False)

            interact(message.channel.send, embed=embed)
            return

        if len(args) < 2:
            Log.error("No command provided")
            await help_me(message, self.command)
            return

        role = " ".join(args[1:])
        role_obj = None
        role_id = None
        if role.startswith("<@&") and role.endswith(">"):
            role_id = int(role[3:-1])
        elif role.isnumeric():
            role_id = int(role)
        else:
            for i in message.guild.roles:
                if i.name.lower() == role.lower():
                    role_obj = i
                    break

        if role_id is not None:
            role_obj = message.guild.get_role(role_id)

        if role_obj is None:
            unknown_user = f"[{role}] role was not found"
            Log.error(unknown_user)
            interact(message.channel.send, f"> {unknown_user}")
            return

        ping_server(message.guild.id, message.channel.id, role_obj.mention)
        interact(message.channel.send, f"{message.channel} is now the alert channel for {message.guild.name} "
                                       f"pinging {role_obj.name}")
        interact(notify_sales)


check_sales.start()
