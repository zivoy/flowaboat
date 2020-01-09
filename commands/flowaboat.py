import discord

from utils import Config, DiscordInteractive

interact = DiscordInteractive().interact


class Command:
    command = "flowaboat"
    description = "Show information about this bot."
    argsRequired = 0
    usage = ""
    examples = [{
        "run": "flowaboat",
        "result": "Tells you about flowaboat."
    }]
    synonyms = []

    async def call(self, package):
        message = package["message_obj"]

        embed = discord.Embed(description="Modular Discord bot with advanced osu! commands.",
                              url="https://github.com/zivoy/flowaboat", color=0xcf660a)
        embed.set_footer(icon_url="https://avatars1.githubusercontent.com/u/16857861?s=64&v=2", text="zivoy")
        embed.set_thumbnail(
            url="https://yt3.ggpht.com/a/AGF-l78A7VJcEml4nmoU7xP7bXRbnukYxDy0t1UiKQ=s288-c-k-c0xffffffff-no-rj-mo")
        embed.set_author(name="flowaboat", url="https://github.com/zivoy/flowaboat")
        embed.add_field(name="GitHub Repo", value="https://github.com/zivoy/flowaboat")
        embed.add_field(name="Commands", value="https://github.com/zivoy/flowaboat/blob/pythonized/COMMANDS.md \n"
                                               "more commands to be added")
        embed.add_field(name="Prefix", value=f"The command prefix on this bot is `{Config.prefix}`.")
        interact(message.channel.send, embed=embed)
