import commands
from utils import Config, sanitize
Config().load()

markdown = "# Commands\n"
markdown += "### Table Of Contents"

for command in commands.List:
    markdown += f"\n- [{Config.prefix}{command}](#{command})"

markdown += "\n---"

for command in commands.List:
    command = getattr(commands, sanitize(command))()
    markdown +=\
        f"\n## {Config.prefix}{command.command}\n" \
        f"{command.description}\n\n" \
        f"**Required variables**: `{command.argsRequired}`\n\n" \
        f"**Usage**: `{Config.prefix}{command.command} {command.usage}`\n\n" \

    if command.synonyms:
        markdown += "#### Synonyms:\n\n"
        markdown += ", ".join([f"`{Config.prefix}{i}`" for i in command.synonyms])
        markdown += "\n\n"

    markdown += f"### Example{'s' if len(command.examples) > 1 else ''}:\n\n"
    markdown += "\n\n".join([f"```\n{Config.prefix}{i['run']}\n```\n{i['result']}\n\n" for i in command.examples])

with open("COMMANDS.md", "w") as command_file:
    command_file.write(markdown)
