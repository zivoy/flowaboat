import discord

from commands import flowaboat


class Watcher:
    name = "when pinged"
    description = "bot gives information on itself when its pinged"

    trigger_description = "taging the bot in message"

    action_description = "will return information on the bot"

    examples = [{
        'trigger': "@bot_name",
        'action': "returns flowaboat page"
    }]

    def trigger(self, message_obj: discord.Message, client: discord.Client):
        return message_obj.content in [f"<@!{client.user.id}>", client.user.mention], ""

    async def action(self, message_obj, _):
        await flowaboat().call({"message_obj": message_obj})
