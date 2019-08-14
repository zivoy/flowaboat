from utils import *
import osu


class Command:
    command = "top"
    description = "Show a specific top play."
    argsRequired = 0
    usage = "[username]"
    examples = [
        {
            "run": "top",
            "result": "Returns your #1 top play."
        },
        {
            "run": "top5 vaxei",
            "result": "Returns Vaxei's #5 top play."
        }]
    synonyms = [r"top\d+"]

    async def call(self, package):
        message, args, user_data, client = package["message_obj"], package["args"], \
                                           package["user_obj"], package["client"]

        if len(args) < 2 and user_data["osu_ign"] == "":
            Log.error("No User provided provided")
            await help_me(message, "ign-set")
            return

        user = get_user(args, user_data["osu_ign"], "osu")

        index = digits.match(args[0])

        if index is None:
            index = 1
        else:
            index = int(index.captures(1)[0])

        osu.get_top(user, index)
