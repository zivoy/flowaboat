from typing import Optional, List

import discord
from arrow import get

from utils import SEPARATOR
from utils.discord import DiscordInteractive, help_me
from utils.utils import Log

interact = DiscordInteractive.interact


class Command:
    command = "statrole"
    description = "Show data on your user"
    argsRequired = 1
    usage = "<role identifier>"
    examples = [{
        "run": "role guild master",
        "result": "Returns information in guild master role."
    },
        {
            'run': "statrole 415349826578808842",
            'result': "Returns information on role."
        }]
    synonyms = ["role"]

    async def call(self, package):
        message: discord.Message = package["message_obj"]
        args: List[str] = package["args"]

        if len(args) < 2:
            Log.error("No Role provided")
            await help_me(message, "statrole")
            return

        role = " ".join(args[1:])
        role_obj: Optional[discord.Role] = None
        role_id = None
        if role.startswith("<@&") and role.endswith(">"):
            role_id = int(role[3:-1])
        elif role.startswith("<@") and role.endswith(">"):
            role_id = int(role[2:-1])
        elif role.isnumeric():
            role_id = int(role)
        else:
            for i in message.guild.roles:
                if i.name.lower() == role.lower():
                    role_obj = i
                    break

        if role_id is not None:
            role_obj = message.guild.get_role(role_id)

        if role_obj is None:
            unknown_user = f"[{role}] role was not found"
            Log.error(unknown_user)
            interact(message.channel.send, f"> {unknown_user}")
            return

        embed = discord.Embed(color=role_obj.color, title=role_obj.name, description=role_obj.mention)
        created = f"Role was created on " \
                  f"{get(role_obj.created_at).format('dddd[,] MMMM Do YYYY [@] h:mm:ss A [UTC]')} " \
                  f"{SEPARATOR} " \
                  f"{get(role_obj.created_at).humanize()}"
        embed.set_footer(text=created)

        embed.add_field(name="ID", value=str(role_obj.id), inline=True)

        nRoles = len(message.guild.roles)

        embed.add_field(name="Position in Guild:", value=str(nRoles-role_obj.position), inline=True)

        embed.add_field(name="Can be mentioned:", value=str(role_obj.mentionable), inline=True)
        embed.add_field(name="Will display separately:", value=str(role_obj.hoist), inline=True)

        aud = role_obj.guild.audit_logs(action=discord.AuditLogAction.role_update)
        entries = interact(aud.flatten)

        for i in entries:
            if i.target.id == role_obj.id:
                embed.add_field(inline=True, name="Last Updated:",
                                value=f"{get(i.created_at).format('dddd[,] MMMM Do YYYY [@] h:mm:ss A [UTC]')} "
                                      f"{SEPARATOR} "
                                      f"{get(i.created_at).humanize()}")
                break

        if role_obj.members:
            embed.add_field(inline=False, name="Owners:",
                            value=", ".join([i.mention for i in role_obj.members]))

        perms = {"add_reactions": "Add reactions",
                 "administrator": "Administrator",
                 "attach_files": "Attach files",
                 "ban_members": "Ban members",
                 "change_nickname": "Change nickname",
                 "connect": "Connect",
                 "create_instant_invite": "Create instant invite",
                 "deafen_members": "Deafen members",
                 "embed_links": "Embed links",
                 "external_emojis": "External emojis",
                 "kick_members": "Kick members",
                 "manage_channels": "Manage channels",
                 "manage_emojis": "Manage emojis",
                 "manage_guild": "Manage guild",
                 "manage_messages": "Manage messages",
                 "manage_nicknames": "Manage nicknames",
                 "manage_roles": "manage roles",
                 "manage_webhooks": "Manage webhooks",
                 "mention_everyone": "Mention everyone",
                 "move_members": "Move members",
                 "mute_members": "Mute members",
                 "priority_speaker": "Priority speaker",
                 "read_message_history": "Read message history",
                 "read_messages": "Read messages",
                 "send_messages": "Send messages",
                 "send_tts_messages": "Send tts messages",
                 "speak": "Speak",
                 "stream": "Stream",
                 "use_voice_activation": "Use voice activation",
                 "view_audit_log": "View audit log"
                 }

        embed.add_field(inline=False, name="Permissions:",
                        value="```diff\n"+"\n"
                        .join([f"{'+' if i[1] else '-'} {perms[i[0]]}: {i[1]}" for i in role_obj.permissions])+"\n```")

        Log.log(f"stating {role_obj.name}")
        interact(message.channel.send, embed=embed)
