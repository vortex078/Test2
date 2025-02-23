import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio


intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

afk_file = "afk.json"
afk_message = {}
afk_message_count = {}
afk_reset_time = 60

async def reset_afk_message_count(user_id):
    await asyncio.sleep(afk_reset_time)
    if str(user_id) in afk_message_count:
        afk_message_count[str(user_id)] = 0
        print(f"AFK message count reset for user {user_id}")

if not os.path.exists(afk_file):
    with open(afk_file, "w") as f:
        json.dump({}, f)

try:
    with open(afk_file, "r") as f:
        afk_message = json.load(f)
except FileNotFoundError:
    afk_message = {}

def load_logging_config():
    try:
        with open('loggingconfig.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_logging_config(config):
    with open('loggingconfig.json', 'w') as f:
        json.dump(config, f, indent=4)

logging_config = load_logging_config()

async def log_event(guild, log_message, event_type, color):
    """Logs an event to the specified logging channel with an embed."""
    guild_id = str(guild.id)
    channel_id = logging_config.get(guild_id)
    if channel_id:
        channel = bot.get_channel(int(channel_id))
        if channel:
            embed = discord.Embed(title=event_type, description=log_message, color=color)
            embed.set_author(name=guild.name, icon_url=guild.icon.url if guild.icon else None)
            await channel.send(embed=embed)
        else:
            print(f"Error: Logging channel not found in guild {guild.name}({guild.id})")
    else:
        print(f"Error: Logging channel not set for guild {guild.name}({guild.id})")

@bot.hybrid_command(name="setloggingchannel", help="Sets the logging channel for the guild")
@commands.has_permissions(manage_guild=True)
async def set_logging_channel(ctx, channel: discord.TextChannel):
    """Sets the logging channel for the guild."""
    guild_id = str(ctx.guild.id)
    logging_config[guild_id] = str(channel.id)
    save_logging_config(logging_config)
    await ctx.send(f"Logging channel set to {channel.mention} for this server.")

@bot.event
async def on_message(message):
    global afk_message
    global afk_message_count

    if message.author != bot.user:
        for mention in message.mentions:
            mentioned_user_id = str(mention.id)
            if mentioned_user_id in afk_message:
                afk_reason = afk_message[mentioned_user_id]
                await message.channel.send(f"`{mention.name}` Is AFK: {afk_reason}")

    user_id = str(message.author.id)

    if user_id in afk_message and not message.content.startswith(bot.command_prefix):
        if user_id not in afk_message_count:
            afk_message_count[user_id] = 0

    if afk_message_count[user_id] ~= nil and afk_message_count[user_id] < 3:
        afk_message_count[user_id] += 1
        print(f"AFK message count: {afk_message_count[user_id]}")
        await asyncio.sleep(delay=None)
    else:
        await message.channel.send(f"Welcome back, {message.author.mention}! I've removed your AFK status.")
        del afk_message[user_id]
        with open(afk_file, "w") as f:
            json.dump(afk_message, f)
            del afk_message_count[user_id]
            await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    jump_url = f"[Jump to Message]({before.jump_url})"
    if before.guild and not before.author.bot:
        log_message = f"""Message Edited by {before.author.mention} in {before.channel.mention}

**Before:**
{before.content}

**After:**
{after.content}
{jump_url}"""
        await log_event(before.guild, log_message, "Message Edit", discord.Color.yellow())

@bot.event
async def on_message_delete(message):
    if message.author == bot.user or "messages purged by" in message.content:
        log_message = f"""Purge Command Detected:
         Message Deleted by the Purge Command:
         **Content:** {message.content}
         **Channel:** {message.channel.mention}"""
        await log_event(message.guild, log_message, "Automated Purge Log", discord.Color.dark_purple())
        
    else:
        if message.guild:
            log_message = f"""Message Deleted by {message.author.mention} in {message.channel.mention}

**Content:**
{message.content}"""
            embed_color = discord.Color.red()
            ghost_ping_detected = False

            if message.mentions or message.role_mentions:
                ghost_ping_detected = True
                log_message += """

**ALERT: GHOST PING DETECTED!!!**"""
                embed_color = discord.Color.dark_red()

            await log_event(message.guild, log_message, "Message Delete", embed_color)

@bot.event
async def on_reaction_add(reaction, user):
    log_message = f"""Reaction Added: {reaction.emoji} by {user.mention} in {reaction.message.channel.mention}
[Jump to Message]({reaction.message.jump_url})"""
    await log_event(reaction.message.guild, log_message, "Reaction Added", discord.Color.green())

@bot.event
async def on_reaction_remove(reaction, user):
    log_message = f"""Reaction Removed: {reaction.emoji} by {user.mention} in {reaction.message.channel.mention}
[Jump to Message]({reaction.message.jump_url})"""
    await log_event(reaction.message.guild, log_message, "Reaction Removed", discord.Color.orange())

@bot.event
async def on_member_update(before, after):
    if before.guild and not before.bot:
        if before.guild:
            if before.nick != after.nick:
                log_message = f"Nickname Change: {before.mention} changed nickname from **{before.nick}** to **{after.nick}**"
                await log_event(before.guild, log_message, "Nickname Change", discord.Color.blue())
            elif before.status != after.status:
                log_message = f"{before.mention} status changed to **{before.status}**"
                await log_event(before.guild, log_message, "Status Change", discord.Color.green())
            elif before.display_name != after.display_name:
                log_message = f"{before.mention} display name changed to **{before.display_name}**"
                await log_event(before.guild, log_message, "Display name Change", discord.Color.purple())

@bot.event
async def on_guild_channel_create(channel):
    if channel.guild:
        log_message = f"Channel Created: {channel.mention} created"
        await log_event(channel.guild, log_message, "Channel Created", discord.Color.green())

@bot.event
async def on_guild_channel_delete(channel):
    if channel.guild:
        log_message = f"Channel Deleted: Channel **{channel.name}** deleted"
        await log_event(channel.guild, log_message, "Channel Delete", discord.Color.red())

@bot.event
async def on_member_ban(guild, user):
    log_message = f"User Banned: {user.mention} banned from the server"
    await log_event(guild, log_message, "User Banned", discord.Color.dark_red())

@bot.event
async def on_member_unban(guild, user):
    log_message = f"User Unbanned: {user.mention} unbanned from the server"
    await log_event(guild, log_message, "User Unbanned", discord.Color.green())

@bot.event
async def on_member_remove(member):
    if member.guild:
        log_message = f"User Left/Kicked: {member.mention} left or was kicked from the server"
        await log_event(member.guild, log_message, "User Left/Kicked", discord.Color.orange())

@bot.event
async def on_member_join(member):
    if member.guild:
        log_message = f"User Joined: {member.mention} joined the server"
        await log_event(member.guild, log_message, "User Joined", discord.Color.blue())

@bot.event
async def on_guild_channel_update(before, after):
    if before:
        if before.name != after.name:
            log_message = f"Channel Name Changed: Channel **{before.name}** changed to **{after.name}**\n[Go to Channel](https://discord.com/channels/{after.guild.id}/{after.id})"
            await log_event(before.guild, log_message, "Channel Name Change", discord.Color.blue())

@bot.event
async def on_guild_audit_log_entry_create(entry):
    log_message = ""

    if entry.action == discord.AuditLogAction.guild_update:
        if entry.target.name != entry.before.name:
            log_message += f"Server Name Changed by {entry.user.mention}: From **{entry.before.name}** to **{entry.target.name}**"
        if entry.target.icon != entry.before.icon:
            log_message += f"Server Icon Changed by {entry.user.mention}: New icon: {entry.target.icon_url}"
        if entry.target.splash != entry.before.splash:
            log_message += f"Server Splash Changed by {entry.user.mention}: New splash: {entry.target.splash_url}"
        if entry.target.banner != entry.before.banner:
            log_message += f"Server Banner Changed by {entry.user.mention}: New banner: {entry.target.banner_url}"
        if entry.target.region != entry.before.region:
            log_message += f"Server Region Changed by {entry.user.mention}: From **{entry.before.region}** to **{entry.target.region}**"
        if entry.target.afk_timeout != entry.before.afk_timeout:
            log_message += f"AFK Timeout Changed by {entry.user.mention}: From **{entry.before.afk_timeout}** to **{entry.target.afk_timeout}**"
        if entry.target.default_notifications != entry.before.default_notifications:
            log_message += f"Default Notifications Changed by {entry.user.mention}: From **{entry.before.default_notifications}** to **{entry.target.default_notifications}**"
        if entry.target.explicit_content_filter != entry.before.explicit_content_filter:
            log_message += f"Explicit Content Filter Changed by {entry.user.mention}: From **{entry.before.explicit_content_filter}** to **{entry.target.explicit_content_filter}**"
        if entry.target.mfa_level != entry.before.mfa_level:
            log_message += f"MFA Level Changed by {entry.user.mention}: From **{entry.before.mfa_level}** to **{entry.target.mfa_level}**"
        if entry.target.verification_level != entry.before.verification_level:
            log_message += f"Verification Level Changed by {entry.user.mention}: From **{entry.before.verification_level}** to **{entry.target.verification_level}**"
        if entry.target.premium_tier != entry.before.premium_tier:
            log_message += f"Premium Tier Changed by {entry.user.mention}: From **{entry.before.premium_tier}** to **{entry.target.premium_tier}**"
        if entry.target.premium_subscription_count != entry.before.premium_subscription_count:
            log_message += f"Server Boosts Changed by {entry.user.mention}: From **{entry.before.premium_subscription_count}** to **{entry.target.premium_subscription_count}**"

        if log_message:
            await log_event(entry.guild, log_message, "Server Update", discord.Color.purple())

@bot.event
async def on_integration_create(integration):
    if integration.guild:
        log_message = f"Integration Added: Integration **{integration.name}** added"
        await log_event(integration.guild, log_message, "Integration Added", discord.Color.green())

@bot.event
async def on_integration_remove(integration):
    if integration.guild:
        log_message = f"Integration Removed: Integration **{integration.name}** removed"
        await log_event(integration.guild, log_message, "Integration Removed", discord.Color.red())

@bot.event
async def on_guild_role_create(role):
    log_message = f"Role created: {role.name}"
    await log_event(role.guild,log_message, "Role Created", discord.Color.green())

@bot.event
async def on_guild_role_delete(role):
    log_message = f"Role deleted: {role.name}"
    await log_event(role.guild,log_message, "Role Deleted", discord.Color.red())

@bot.event
async def on_guild_role_update(before, after):
    log_message = f"Role update: Role {before.name} Updated to {after.name}"
    await log_event(before.guild,log_message, "Role Update", discord.Color.purple())

@bot.event
async def on_invite_create(invite):
    log_message = f"Invite Created: Invite {invite.url} created by{invite.inviter}"
    await log_event(invite.guild,log_message, "Invite Created", discord.Color.purple())

@bot.event
async def on_invite_delete(invite):
    log_message = f"Invite deleted: Invite {invite.guild} created by{invite.inviter}"
    await log_event(invite.guild,log_message, "Invite Deleted", discord.Color.dark_red())

@bot.event
async def on_guild_emojis_udpate(guild, before, after):
    log_message = f"Emojis Updated:"
    await log_event(guild,log_message, "Emojis Updated", discord.Color.blue())

@bot.event
async def on_voice_state_update(member, before, after):
    log_message = f"{member.mention} is being updated"
    await log_event(member.guild,log_message, "Voice Channel Updated", discord.Color.blue())

@bot.hybrid_command(name="act", help="Moderation commands")
@commands.has_permissions(kick_members=True, ban_members=True)
@app_commands.choices(action=[
    app_commands.Choice(name="Kick", value="kick"),
    app_commands.Choice(name="Ban", value="ban"),
    app_commands.Choice(name="Unban", value="unban")
])
async def moderation(ctx, action: app_commands.Choice[str], member: discord.Member, *, reason: str = None):
    """Performs moderation actions."""
    log_message = f"{member.mention} was {action.value} for {reason}"
    color = ""
    if action.value == "kick":
        await member.kick(reason=reason)
        color = discord.Color.dark_red()
    elif action.value == "ban":
        await member.ban(reason=reason)
        color = discord.Color.dark_red()
    elif action.value == "unban":
        await ctx.guild.unban(user=discord.Object(id=member.id), reason=reason)
        color = discord.Color.green()

@bot.hybrid_command(name="afk_hybrid", description="Sets your AFK status.")
async def afk_hybrid(ctx, *, reason="Away from keyboard"):
    global afk_message
    afk_message[str(ctx.author.id)] = reason
    with open(afk_file, "w") as f:
        json.dump(afk_message, f)
    await ctx.send(f"{ctx.author.mention} is now AFK: {reason}")

@bot.command(name="afk", description="Sets your AFK status.")
async def afk(ctx, *, reason="Away from keyboard"):
    global afk_message
    afk_message[str(ctx.author.id)] = reason
    with open(afk_file, "w") as f:
        json.dump(afk_message, f)
    await ctx.send(f"{ctx.author.mention} is now AFK: {reason}")

@bot.hybrid_command(name="purge_hybrid", description="Purges a specified number of messages.")
@commands.has_permissions(manage_messages=True)
async def purge_hybrid(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.channel.send(f"{amount} messages purged by {ctx.author.mention}.", delete_after=5)

@bot.command(name="purge", description="Purges a specified number of messages.")
@commands.has_permissions(manage_messages=True)
async def purge(ctx, amount: int):
  await ctx.channel.purge(limit=amount + 1)
  await ctx.channel.send(f"{amount} messages purged by {ctx.author.mention}.", delete_after=5)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.MissingPermissions):
        await ctx.send("You do not have the required permissions to execute this command.")
    pass

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
##    bot.loop.create_task(update_stats())

server_status = {"status": "🔴"}

@bot.hybrid_command(name="togglestatus", description="Toggles the server status emoji")
@commands.has_permissions(administrator=True)
async def togglestatus(ctx):
    global server_status

    status_channel = discord.utils.get(ctx.guild.voice_channels, name="Server Status: 🔴") or discord.utils.get(ctx.guild.voice_channels, name="Server Status: 🟢")
    if not status_channel:
        await ctx.send("Server Status channel not found. Please run `!setupstats` first.")
        return

    category = status_channel.category if status_channel else None

    valid_emojis = ["🔴", "🟢"]
    current_name = status_channel.name
    emoji_used = current_name.split(":")[-1].strip()  

    if emoji_used not in valid_emojis:
        server_status["status"] = "🔴"
        new_name = "Server Status: 🔴"
        await ctx.send("Unrecognized emoji. Resetting to red.")
    else:
        server_status["status"] = "🟢" if emoji_used == "🔴" else "🔴"
        new_name = f"Server Status: {'🟢' if emoji_used == '🔴' else '🔴'}"

    await status_channel.edit(name=new_name, category=category)
    await ctx.send(f"Server status toggled to {server_status['status']}!")


TOKEN = os.getenv("BOTTOKEN")
bot.run(TOKEN)
