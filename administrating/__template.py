class Watcher:
    name = "administrating function name"
    description = "description of function"

    trigger_description = "explanation on what will trigger it"

    action_description = "explanation on what will happen once triggered"

    examples = [{
        'trigger': "user action",
        'action': "bot action"
    }]

    def trigger(self, message_obj, client):
        # trigger function will get a message object and a client object as input
        # and must return something in the format of bool, payload
        # the bool is if the function triggered and the payload will be used in the function
        pass

    async def action(self, message_obj, payload):
        # action that the bot will take once triggered the input is a message object
        # and a payload with this the bot can carry out the admin function
        pass
