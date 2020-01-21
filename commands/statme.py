from typing import List

import discord
from arrow import get
from skimage import io

from utils import SEPARATOR
from utils.discord import DiscordInteractive
from utils.utils import Log
from utils.errors import UserNonexistent

interact = DiscordInteractive.interact


class Command:
    command = "statme"
    description = "Show data on your user"
    argsRequired = 0
    usage = "[username]"
    examples = [{
        "run": "me",
        "result": "Returns your information and stats."
    },
        {
            'run': "info tmanti",
            'result': "Returns tmanti's stats."
        }]
    synonyms = ["me", "info", "stat"]

    async def call(self, package):
        message: discord.Message = package["message_obj"]
        args: List[str] = package["args"]
        client: discord.Client = package["client"]

        username = None
        user: discord.User = message.author
        name = " ".join(args[1:])
        if len(args) >= 2:
            if name.startswith("<@!") and name.endswith(">"):
                username = int(name[3:-1])
            elif name.startswith("<@") and name.endswith(">"):
                username = int(name[2:-1])
            elif name.isnumeric():
                username = int(name)
            else:
                for i in client.users:
                    if i.name.lower() == name.lower():
                        user = i
                        break
                else:
                    for i in message.guild.members:
                        if i.nick is not None and i.nick.lower() == name.lower():
                            user = i
                            break
                    else:
                        unknown_user = f"[{name}] user not found"
                        Log.error(unknown_user)
                        interact(message.channel.send, f"> {unknown_user}")
                        raise UserNonexistent(name)

        if username:
            user = client.get_user(username)
            if user is None:
                user = interact(client.fetch_user, username)
                if user is None:
                    unknown_user = f"[{name}] user not found"
                    Log.error(unknown_user)
                    interact(message.channel.send, f"> {unknown_user}")
                    raise UserNonexistent(name)

        logo = user.avatar_url_as(format="png", static_format='png', size=64)
        picture = interact(logo.read)
        img = io.imread(picture, plugin='imageio')
        if img.shape[2] < 3:
            img = img[:, :, :-1]
        average = img.mean(axis=0).mean(axis=0)
        avgInt = list(map(int, map(round, average)))
        color = "0x{0:02x}{1:02x}{2:02x}".format(*avgInt)

        embed = discord.Embed().from_dict(
            {
                "color": int(color, 16),
                "thumbnail":
                    {
                        "url": str(user.avatar_url)
                    },
                "footer":
                    {
                        "text": f"On Discord since {get(user.created_at).humanize()} "
                                f"{SEPARATOR} Joined on "
                                f"{get(user.created_at).format('dddd[,] MMMM Do YYYY [@] h:mm:ss A [UTC]')}"
                    }
            })
        embed.add_field(name="ID", value=user.id, inline=True)

        stat_names = {
            "online": "Online",
            "offline": "Offline",
            "idle": "Idle",
            "dnd": "Do Not Disturb",
            "do_not_disturb": "Do Not Disturb",
            "invisible": "Offline"
        }

        member: discord.Member = message.guild.get_member(user.id)
        if member is None:
            member = discord.utils.find(lambda m: m.id == user.id, client.get_all_members())

        if member is not None:
            embed.add_field(name="Status", value=stat_names[member.status.name], inline=True)
            if member.nick:
                if message.guild.id != member.guild.id:
                    title = f"Nickname in {member.guild.name}"
                    embed.add_field(name=title, value=member.nick, inline=True)
                else:
                    embed.set_author(name=f"{str(user)} {SEPARATOR} {member.nick}", icon_url=str(user.avatar_url))

            if member.joined_at:
                embed.add_field(name=f"Joined {member.guild.name} on",
                                value=f"{get(member.joined_at).format('dddd[,] MMMM Do YYYY [@] h:mm:ss A [UTC]')} "
                                      f"{SEPARATOR} {get(member.joined_at).humanize()}",
                                inline=False)

            if member.premium_since:
                embed.add_field(name=f"Nitro boosting {member.guild.name} since",
                                value=f"{get(member.premium_since).format('dddd[,] MMMM Do YYYY [@] h:mm:ss A [UTC]')} "
                                      f"{SEPARATOR} {get(member.joined_at).humanize()}",
                                inline=False)

            if member.guild.id == message.guild.id:
                roles = member.roles[1:]
                rls = map(lambda x: x.id, roles)
                embed.add_field(name=f"Roles [{len(roles)}]",
                                value=", ".join([f"<@&{i}>" for i in rls][::-1]), inline=True)

            if member.activity is not None and member.activity.state:
                embed.add_field(name="Message",
                                value=member.activity.state, inline=True)

        if not embed.author:
            embed.set_author(name=str(user), icon_url=str(user.avatar_url))

        Log.log(f"stating {user.name}")
        interact(message.channel.send, embed=embed)
