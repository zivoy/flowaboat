class Command:
    command = "ign-set"
    description = "Sets your username for platform."
    argsRequired = 2
    usage = "[osu|steam] <username>"
    example = {
        "run": "ign-set osu nathan on osu",
        "result": "Sets your osu! username to nathan on osu."
    }
    synonyms = ["set-ign", "set"]

    async def call(self, package):
        pass