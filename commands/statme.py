from utils import Log, SEPARATOR
import discord
from arrow import get
from typing import List
from skimage import io


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
                    if i.name == name:
                        user = i
                        username = i.id
                        break
                if username is None:
                    for i in message.guild.members:
                        if i.nick == name:
                            user = i
                            username = i.id
                            break
        if username:
            user = client.get_user(username)
            if user is None:
                user = await client.fetch_user(username)
                if user is None:
                    unknown_user = f"[{name}] user not found"
                    Log.error(unknown_user)
                    await message.channel.send(f"> {unknown_user}")
                    return

        picture = await user.avatar_url_as(format="png", static_format='png', size=64).read()
        img = io.imread(picture, plugin='imageio')[:, :, :-1]
        average = img.mean(axis=0).mean(axis=0)
        avgInt = list(map(int, map(round, average)))
        color = "0x{0:02x}{1:02x}{2:02x}".format(*avgInt)

        embed = discord.Embed().from_dict({
            "color": int(color, 16),
            "thumbnail": {
                "url": str(user.avatar_url)
            },
            "author": {
                "name": str(user),#f"{user.name}#{user.discriminator}",
                "icon_url": str(user.avatar_url)
            },
            "footer": {
                "text": f"On Discord since {get(user.created_at).humanize()} "
                f"{SEPARATOR} Joined on {get(user.created_at).format('dddd[,] MMMM Do YYYY [@] h:mm:ss A [UTC]')}"
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
                title = "Nickname"
                if message.guild.id != member.guild.id:
                    title = f"Nickname in {member.guild.name}"
                embed.add_field(name=title, value=member.nick, inline=True)

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
                                value=", ".join([f"<@&{i}>" for i in rls]), inline=True)

            if member.activity.state:
                embed.add_field(name="Message",
                                value=member.activity.state, inline=True)

        Log.log(f"stating {user.name}")
        await message.channel.send(embed=embed)
