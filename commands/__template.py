class Command:
    command = "template"  # command name must be the same as the file name but can have spacial characters
    description = "description of command"
    argsRequired = 1  # number of arguments needed for command
    usage = "<command>"  # a usage example of required arguments
    examples = [{
        'run': "template",  # what user runs
        'result': "a template"  # the response of the bot
    }]
    synonyms = ["tmp"]  # any synonyms that will also trigger command [accepts regular expressions]

    async def call(self, package):
        # what happens once the command is executed
        pass
