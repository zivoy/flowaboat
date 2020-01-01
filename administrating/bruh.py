from utils import Log, fetch_emote


class Watcher:
    name = "bruh"
    description = "Reacts with the Bruh emoji when user types /bruh"

    trigger_description = f"if a user says /bruh it will trigger the function"

    action_description = "once triggered the bot will react with Bruh emoji"

    examples = [{
        'trigger': f"/bruh",
        'action': "reacts with bruh"
    }]

    def trigger(self, message_obj, client):
        string = str(message_obj.content)

        if string.lower() == "/bruh":
            return True, fetch_emote("bruh", None, client)

        return False, ""

    async def action(self, message_obj, payload):
        Log.log("{0} says bruh".format(str(message_obj.author.name)))
        await message_obj.add_reaction(payload)
