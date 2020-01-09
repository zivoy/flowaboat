import commands
import administrating
from utils import Config, sanitize


def generate(server=0):
    Config().load()

    markdown = "# Table Of Contents\n"
    markdown += "### Commands"

    for command in commands.List:
        markdown += f"\n- [{Config.prefix}{command}](#{sanitize(Config.prefix)}{command.replace(' ', '-')})"
    
    markdown += "\n### Administrative functions"

    for adm in administrating.List:
        markdown += f"\n- [{adm.name}](#{sanitize(adm.name).replace(' ', '-')})"
        
    markdown += "\n---"

    for command in commands.List:
        command = getattr(commands, sanitize(command))()
        markdown +=\
            f"\n## {Config.prefix}{command.command}\n" \
            f"{command.description}\n\n" \
            f"**Required variables**: `{command.argsRequired}`\n\n" \
            f"**Usage**: `{Config.prefix}{command.command} {command.usage}`\n\n"

        if command.synonyms:
            markdown += "#### Synonyms:\n\n"
            markdown += ", ".join([f"`{Config.prefix}{i}`" for i in command.synonyms])
            markdown += "\n\n"

        markdown += f"### Example{'s' if len(command.examples) > 1 else ''}:\n\n"
        markdown += "\n\n".join([f"```\n{Config.prefix}{i['run']}\n```\n{i['result']}\n\n" for i in command.examples])

    markdown += "---\n"

    for adm in administrating.List:
        markdown += \
            f"\n## {adm.name}\n" \
            f"{adm.description}\n\n" \
            f"### Trigger:\n" \
            f"{adm.trigger_description}\n\n" \
            f"### Action:\n" \
            f"{adm.action_description}\n\n"

        markdown += f"### Example{'s' if len(adm.examples) > 1 else ''}:\n\n"
        markdown += "\n\n".join([f"```\n{i['trigger']}\n```\n"
                                 f"will result in\n```\n{i['action']}\n```\n\n" for i in adm.examples])

    with open("COMMANDS.md", "w") as command_file:
        command_file.write(markdown)
