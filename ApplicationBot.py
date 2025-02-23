import discord # type: ignore
from discord.ext import commands # type: ignore
from discord import app_commands
import asyncio
from datetime import datetime, timedelta
import json
import os

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), help_command=None)

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

    if afk_message_count[user_id] != nil and afk_message_count[user_id] < 3:
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

async def check_new_members():
    while True:
        for guild in bot.guilds:
            if guild.id == 1188506068079345744:
                continue
            for member in guild.members:
                if member.bot or member.top_role.position > guild.me.top_role.position:
                    continue
                join_date = member.joined_at
                if join_date is not None:
                    now = datetime.utcnow().replace(tzinfo=join_date.tzinfo)
                    time_diff = now - join_date
                    print(f"Member: {member.name}")
                    print(f"Time Difference: {time_diff}")
                    role = guild.get_role(1304536780757794909)
                    if role:
                        if time_diff > timedelta(weeks=1):
                            if role in member.roles:
                                try:
                                    await member.remove_roles(role)
                                    print(f"Removed role from {member.name}")
                                except Exception as e:
                                    if e.status!= 403:
                                        print(f"No perms removing role from {member.name}: {e}")
                                    else:
                                        print(f"Error removing role from {member.name}: {e}")
                            else:
                                print(f"Member {member.name} has been in the server for more than a week and does not have the role.")
                        else:
                            if role not in member.roles:
                                try:
                                    await member.add_roles(role)
                                    print(f"Added role to {member.name}")
                                except Exception as e:
                                    if e.status!= 403:
                                        print(f"No perms adding role to {member.name}: {e}")
                                    else:
                                        print(f"Error adding role to {member.name}: {e}")
                            else:
                                print(f"Member {member.name} has been in the server for less than a week and already has the role.")
                    else:
                        print("Could not find the specified role")
                    print("------------------------")
        await asyncio.sleep(10)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'{bot.user} has connected to Discord!')
    permissions = discord.Permissions()
    permissions.send_messages = True
    permissions.manage_channels = True
    permissions.read_messages = True
    permissions.add_reactions = True
    permissions.embed_links = True
    permissions.attach_files = True
    permissions.read_message_history = True
    permissions.use_application_commands = True    
    permissions.manage_threads = True
    permissions.create_public_threads = True
    permissions.send_messages_in_threads = True

    invite_link = discord.utils.oauth_url(bot.user.id, permissions=permissions)
    print(f"Bot invite link (with necessary permissions): {invite_link}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="your applications"))
    asyncio.create_task(check_new_members())

@bot.event
async def on_guild_join(guild):
    try:
        if guild.system_channel:
            await guild.system_channel.send('''Border RP US Application System v1.0 by twangymoney, type /help for a list of commands''')
    except Exception as e:
        print(f"Exception tryna get system_channel: {e}")
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                await channel.send('''Border RP US Application System v1.0 by twangymoney, type /help for a list of commands''')
                break

@bot.hybrid_command(name='help', help='Show help for commands')
async def help(ctx, command=None):
    if command == 'setup':
        embed = discord.Embed(title='Setup Help', color=0x00ff00)
        embed.add_field(name='Usage', value='/setup <arg>', inline=False)
        embed.add_field(name='Available args', value='app, channel, logging', inline=False)
        embed.add_field(name='Example', value='/setup app - Sets up the application system', inline=False)
        embed.add_field(name='Steps', value='do /setup app first, then /setup channel then /setup logging', inline=False)
        await ctx.send(embed=embed)
    elif command == 'button':
        embed = discord.Embed(title='Button Help', color=0x00ff00)
        embed.add_field(name='Usage', value='/button <arg>', inline=False)
        embed.add_field(name='Available args', value='add, remove', inline=False)
        embed.add_field(name='Example', value='/button add - Adds a button to a channel', inline=False)
        await ctx.send(embed=embed)
    else:
        embed = discord.Embed(title='Help', color=0x00ff00)
        embed.add_field(name='/setup', value='Used to setup the application system. Type /help setup for more info', inline=False)
        embed.add_field(name='/button', value='Used to add or remove buttons from a channel. Type /help button for more info', inline=False)
        await ctx.send(embed=embed)

@bot.hybrid_command(name='setup', help='Setup the application system')
async def setup(ctx, arg=None):
    if arg == 'app':
        await ctx.send('Please check your DMs to setup the application.', ephemeral=True)
        def check(m):
            return m.author == ctx.author and m.channel.type == discord.ChannelType.private
        await ctx.author.send('What is the application name?')
        app_name = await bot.wait_for('message', check=check)
        app_name = app_name.content
        apps = {}
        try:
            with open('Apps.json', 'r') as f:
                apps = json.load(f)
        except FileNotFoundError:
            with open('Apps.json', 'w') as f:
                json.dump({}, f)
                apps = {}
        
        if app_name not in apps:
            apps[app_name] = []
        await ctx.author.send('Please enter your questions. Type END to finish.')
        questions = []
        while True:
            await ctx.author.send('Please enter your next question. Type END to finish.')
            question = await bot.wait_for('message', check=check)
            question = question.content
            if question.upper() == 'END':
                break
            questions.append(question)
        apps[app_name] = questions
        with open('Apps.json', 'w') as f:
            json.dump(apps, f)
        await ctx.author.send('Application setup complete.')
    elif arg == 'channel':
        await ctx.send('Please enter the channel ID where you want to send the embed.')
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        channel_id = await bot.wait_for('message', check=check)
        channel_id = int(channel_id.content)
        channel = bot.get_channel(channel_id)
        await ctx.channel.send('What would you like the embed message to say?')
        embed_message = await bot.wait_for('message', check=check)
        embed_message = embed_message.content
        if os.path.exists('Apps.json'):
            with open('Apps.json', 'r') as f:
                apps = json.load(f)
            await ctx.channel.send('Available applications:')
            for app in apps:
                await ctx.channel.send(app)
        else:
            await ctx.channel.send('No applications available.')
        await ctx.channel.send('Which applications would you like to show in this channel? Type END to finish.')
        shown_apps = []
        while True:
            app = await bot.wait_for('message', check=check)
            app = app.content
            if app.upper() == 'END':
                break
            if app in apps:
                shown_apps.append(app)
                await ctx.channel.send(f'Application "{app}" added successfully. Type END to finish')
            else:
                await ctx.channel.send(f'Application "{app}" not found.')
        embed = discord.Embed(title='Applications', description=embed_message)
        view = discord.ui.View()
        for app in shown_apps:
            button = discord.ui.Button(label=app, style=discord.ButtonStyle.blurple, custom_id=app)
            view.add_item(button)
            embed.add_field(name=app, value=' ', inline=False)
        await channel.send(embed=embed, view=view)
        await ctx.channel.send('Channel setup complete.')
    elif arg == 'logging':
      await ctx.send('Please enter the channel ID where you want to send the application logs.')
      def check(m):
          return m.author == ctx.author and m.channel == ctx.channel
      logging_channel_id = await bot.wait_for('message', check=check)
      logging_channel_id = int(logging_channel_id.content)
      logging_channel = bot.get_channel(logging_channel_id)
      with open('logging_channel.txt', 'w') as f:
          f.write(str(logging_channel_id))
      await ctx.send('Logging channel setup complete.')
    else:
        await ctx.send('Invalid argument. Please use /setup app, /setup channel or /setup logging')

@bot.hybrid_command(name='button', help='Add or remove buttons from a channel')
async def button(ctx, arg=None):
    if arg == 'add':
        await ctx.send('Please enter the channel ID where you want to add the button.')
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        channel_id = await bot.wait_for('message', check=check)
        channel_id = int(channel_id.content)
        channel = bot.get_channel(channel_id)
        await ctx.send('Which application would you like to add?')
        apps = []
        if os.path.exists('Apps.json'):
            with open('Apps.json', 'r') as f:
                apps = json.load(f)
            for app in apps:
                await ctx.send(app)
            app = await bot.wait_for('message', check=check)
            app = app.content
            if app in apps:
                embed = discord.Embed(title='Applications')
                view = discord.ui.View()
                button = discord.ui.Button(label=app, style=discord.ButtonStyle.blurple, custom_id='apply')
                view.add_item(button)
                await channel.send(embed=embed, view=view)
            else:
                await ctx.send('Application not found.')
    elif arg == 'remove':
        await ctx.send('Please enter the channel ID where you want to remove the button.')
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        channel_id = await bot.wait_for('message', check=check)
        channel_id = int(channel_id.content)
        channel = bot.get_channel(channel_id)
        messages = await channel.history().flatten()
        for message in messages:
            if message.author == bot.user and message.embeds:
                embed = message.embeds[0]
                view = message.views[0]
                buttons = []
                for child in view.children:
                    buttons.append(child.label)
                await ctx.send(f'Buttons in channel: {buttons}')
                app = await bot.wait_for('message', check=check)
                app = app.content
                if app in buttons:
                    for child in view.children:
                        if child.label == app:
                            view.remove_item(child)
                            await message.edit(view=view)
                            await ctx.send('Button removed.')
                            return
                else:
                    await ctx.send('Button not found in channel.')
    else:
        await ctx.send('Invalid argument. Please use /button add or /button remove')
                    
@bot.hybrid_command(name='perm', help='Setup permissions for the application system')
async def perm(ctx, arg=None):
    if arg == 'set':
        await ctx.send('Please enter the role ID you want to give permission to.')
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel
        role_id = await bot.wait_for('message', check=check)
        role_id = int(role_id.content)
        role = ctx.guild.get_role(role_id)
        with open('perms.txt', 'a') as f:
            f.write(str(role_id) + f'\n')
        await ctx.send('Permission setup complete.')
    else:
        await ctx.send('Invalid argument. Please use /perm set')

async def send_acceptance_embed(applicant, acceptor):
  if os.path.exists('logging_channel.txt'):
    with open('logging_channel.txt', 'r') as f:
        logging_channel_id = int(f.read())
  logging_channel = bot.get_channel(logging_channel_id)
  if logging_channel:
    embed = discord.Embed(
    title=f"{applicant.name} Application ACCEPTED",
    description=f"{applicant.mention}'s application has been accepted by {acceptor.name}"
    )
    await logging_channel.send(embed=embed)
  else:
    print(f"Error: Could not find logging channel with ID: {logging_channel_id}")

async def send_decline_embed(applicant, acceptor):
  if os.path.exists('logging_channel.txt'):
    with open('logging_channel.txt', 'r') as f:
        logging_channel_id = int(f.read())
  logging_channel = bot.get_channel(logging_channel_id)
  if logging_channel:
    embed = discord.Embed(
    title=f"{applicant.name} Application DECLINED",
    description=f"{applicant.mention}'s application has been declined by {acceptor.name}"
    )
    await logging_channel.send(embed=embed)
  else:
    print(f"Error: Could not find logging channel with ID: {logging_channel_id}")
    
async def has_role(interaction, role_id):
    guild = interaction.guild
    member = guild.get_member(interaction.user.id)
    if member:
        role = guild.get_role(role_id)
        return role in member.roles
    else:
        return False

async def has_role_or_higher(interaction, role_id):
    guild = interaction.guild
    member = guild.get_member(interaction.user.id)
    if member:
        role = guild.get_role(role_id)
        member_roles = member.roles
        role_position = None
        if role:
            role_position = role.position
        for r in member_roles:
            if r.position > role_position:
                return True
        return role in member.roles
    else:
        return False

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        userid2 = interaction.user.id
        user = bot.get_user(interaction.user.id)
        print(f"USERID: {interaction.user.id}")
        if interaction.data.get('custom_id').startswith('upvote'):
            userid = int(interaction.data.get('custom_id').split('_')[-1])
            try:
                with open(f'votes_{interaction.channel.id}.json', 'r') as f:
                    votes = json.load(f)
            except FileNotFoundError:
                votes = {'upvote': 0, 'downvote': 0, 'voted_users': []}
                with open(f'votes_{interaction.channel.id}.json', 'w') as f:
                    json.dump(votes, f)
            if interaction.user.id not in votes['voted_users']:
                votes['voted_users'].append(interaction.user.id)
                votes['upvote'] += 1
                with open(f'votes_{interaction.channel.id}.json', 'w') as f:
                    json.dump(votes, f)
                    
                if votes['upvote'] == "3":
                    await interaction.channel.send('Application accepted!')
                    await interaction.channel.send('Application accepted!')
                    thread = interaction.channel
                    await thread.edit(name=f'✅ {thread.name} 🛂{interaction.user.name}')
                    ## await thread.archive()
                    os.remove(f'votes_{interaction.channel.id}.json')
                    async for message in interaction.channel.history():
                        if message.author == bot.user and message.embeds:
                            embed = message.embeds[0]
                            title = embed.title
                            fields = embed.fields
                            new_embed = discord.Embed(title=title)
                            for field in fields:
                                new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
                            await message.edit(embed=new_embed, view=None)
                            await bot.get_user(userid).send('Congratulations, your application has been accepted! You will be ranked shortly.')
                            await send_acceptance_embed(bot.get_user(userid), bot.get_user(interaction.user.id))
                            break
                    
                view = discord.ui.View()
                upvote_button = discord.ui.Button(label=f'{votes["upvote"]}/3 Upvote', style=discord.ButtonStyle.blurple, custom_id=f'upvote_{userid}')
                downvote_button = discord.ui.Button(label=f'{votes["downvote"]}/3 Downvote', style=discord.ButtonStyle.blurple, custom_id=f'downvote_{userid}')
                accept_button = discord.ui.Button(label='Accept', style=discord.ButtonStyle.green, custom_id=f'accept_{userid}')
                decline_button = discord.ui.Button(label='Decline', style=discord.ButtonStyle.red, custom_id=f'decline_{userid}')
                send_dm_button = discord.ui.Button(label='Send DM', style=discord.ButtonStyle.blurple, custom_id=f'senddm_{userid}')
                view.add_item(upvote_button)
                view.add_item(downvote_button)
                view.add_item(accept_button)
                view.add_item(decline_button)
                view.add_item(send_dm_button)
                embed = interaction.message.embeds[0]
                await interaction.response.edit_message(view=view, embed=embed)
                await interaction.response.send_message("Your upvote has been registered.")
            else:
                await interaction.response.send_message('You have already voted!', ephemeral=True)
        elif interaction.data.get('custom_id').startswith('downvote'):
            userid = int(interaction.data.get('custom_id').split('_')[-1])
            try:
                with open(f'votes_{interaction.channel.id}.json', 'r') as f:
                    votes = json.load(f)
            except FileNotFoundError:
                votes = {'upvote': 0, 'downvote': 0, 'voted_users': []}
                with open(f'votes_{interaction.channel.id}.json', 'w') as f:
                    json.dump(votes, f)
            if interaction.user.id not in votes['voted_users']:
                votes['voted_users'].append(interaction.user.id)
                votes['downvote'] += 1
                with open(f'votes_{interaction.channel.id}.json', 'w') as f:
                    json.dump(votes, f)
                    
                if votes["downvote"] == "3":
                    await interaction.channel.send('Application declined!')
                    thread = interaction.channel
                    await thread.edit(name=f'⛔ {thread.name} 🛂{interaction.user.name}')
                    os.remove(f'votes_{interaction.channel.id}.json')
                    messages = await interaction.channel.history().flatten()
                    for message in messages:
                        if message.author == bot.user and message.embeds:
                            embed = message.embeds[0]
                            title = embed.title
                            fields = embed.fields
                            new_embed = discord.Embed(title=title)
                            for field in fields:
                                new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
                            await message.edit(embed=new_embed, view=None)
                            await bot.get_user(userid).send('Sorry, your application was declined. Be sure to try again next friday.')
                            await send_decline_embed(bot.get_user(userid), bot.get_user(interaction.user.id))
                            break
                    
                view = discord.ui.View()
                upvote_button = discord.ui.Button(label=f'{votes["upvote"]}/3 Upvote', style=discord.ButtonStyle.blurple, custom_id=f'upvote_{userid}')
                downvote_button = discord.ui.Button(label=f'{votes["downvote"]}/3 Downvote', style=discord.ButtonStyle.blurple, custom_id=f'downvote_{userid}')
                accept_button = discord.ui.Button(label='Accept', style=discord.ButtonStyle.green, custom_id=f'accept_{userid}')
                decline_button = discord.ui.Button(label='Decline', style=discord.ButtonStyle.red, custom_id=f'decline_{userid}')
                send_dm_button = discord.ui.Button(label='Send DM', style=discord.ButtonStyle.blurple, custom_id=f'senddm_{userid}')
                view.add_item(upvote_button)
                view.add_item(downvote_button)
                view.add_item(accept_button)
                view.add_item(decline_button)
                view.add_item(send_dm_button)
                embed = interaction.message.embeds[0]
                await interaction.response.edit_message(view=view, embed=embed)
                await interaction.response.send_message("Your downvote has been registered.")
            else:
                await interaction.response.send_message('You have already voted!', ephemeral=True)
        elif interaction.data.get('custom_id').startswith('accept'):
            print(f"Accept custom_id: {interaction.data.get('custom_id')}")
            userid = int(interaction.data.get('custom_id').split('_')[-1])
            try:
                with open(f'votes_{interaction.channel.id}.json', 'r') as f:
                    votes = json.load(f)
            except FileNotFoundError:
                votes = {'upvote': 0, 'downvote': 0, 'voted_users': []}
                with open(f'votes_{interaction.channel.id}.json', 'w') as f:
                    json.dump(votes, f)
            if votes['upvote'] >= votes['downvote']:
                await interaction.channel.send('Application accepted!')
                thread = interaction.channel
                await thread.edit(name=f'✅ {thread.name} 🛂{interaction.user.name}')
                os.remove(f'votes_{interaction.channel.id}.json')
                async for message in interaction.channel.history():
                        if message.author == bot.user and message.embeds:
                            embed = message.embeds[0]
                            title = embed.title
                            fields = embed.fields
                            new_embed = discord.Embed(title=title)
                            for field in fields:
                                new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
                            await message.edit(embed=new_embed, view=None)
                ## await thread.archive()
                await bot.get_user(userid).send(f'Congratulations, your application has been accepted! You will be ranked shortly.')
                await send_acceptance_embed(bot.get_user(userid), bot.get_user(interaction.user.id))
            else:
                await interaction.response.send_message('Cannot accept application, downvotes outweigh upvotes!', ephemeral=True)
        elif interaction.data.get('custom_id').startswith('decline'):
            userid = int(interaction.data.get('custom_id').split('_')[-1])
            try:
                with open(f'votes_{interaction.channel.id}.json', 'r') as f:
                    votes = json.load(f)
            except FileNotFoundError:
                votes = {'upvote': 0, 'downvote': 0, 'voted_users': []}
                with open(f'votes_{interaction.channel.id}.json', 'w') as f:
                    json.dump(votes, f)
            if votes['downvote'] >= votes['upvote']:
                await interaction.channel.send('Application declined!')
                thread = interaction.channel
                await thread.edit(name=f'⛔ {thread.name} 🛂{interaction.user.name}')
                ## await thread.archive()
                os.remove(f'votes_{interaction.channel.id}.json')
                async for message in interaction.channel.history():
                        if message.author == bot.user and message.embeds:
                            embed = message.embeds[0]
                            title = embed.title
                            fields = embed.fields
                            new_embed = discord.Embed(title=title)
                            for field in fields:
                                new_embed.add_field(name=field.name, value=field.value, inline=field.inline)
                            await message.edit(embed=new_embed, view=None)
                await bot.get_user(userid).send(f'Sorry, your application was declined. Be sure to try again next friday.')
                await send_decline_embed(bot.get_user(userid), bot.get_user(interaction.user.id))
            else:
                await interaction.response.send_message('Cannot decline application, upvotes outweigh downvotes!', ephemeral=True)
        elif interaction.data.get('custom_id').startswith('senddm'):
            print(f"custom_id: {interaction.data.get('custom_id')}")
            userid20 = int(interaction.data.get('custom_id').split('_')[-1])
            class QuestionModal(discord.ui.Modal, title='Ask a Question'):
                question = discord.ui.TextInput(
                    label='Question',
                    style=discord.TextStyle.long,
                    placeholder='Type your question here...',
                    required=True,
                    max_length=1024,
                )

                async def on_submit(self, interaction: discord.Interaction):
                    ## userid20 = interaction.data.get('custom_id').split('_')[-1]
                    question = self.question.value
                    print(f"userid20: {userid20}")
                    await bot.get_user(userid20).send(f'You have been asked a question by the staff. Please respond to this message with your answer to the question: \n\n## {question}')
                    await interaction.response.send_message(f"Question sent to the user.\nQuestion: {question}")
                    def check(m):
                        return m.author == user and m.channel.type == discord.ChannelType.private
                    answer = await bot.wait_for('message', check=check)
                    await bot.get_user(userid20).send("Response received.")
                    await interaction.channel.send(f'User responded with: \n{answer.content}')

                async def on_error(self, interaction: discord.Interaction, error: Exception):
                    await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
                    traceback.print_exception(type(error), error, error.__traceback__)

            modal = QuestionModal()
            await interaction.response.send_modal(modal)
        else:
            if await has_role(interaction, 1304536780757794909):
                await interaction.response.send_message("You can't apply in this server with the <&1304536780757794909> role", ephemeral=True)
                return
            custom_id = interaction.data.get('custom_id')
            await interaction.response.send_message('Please check your DMs to fill out the application.', ephemeral=True)
            def check(m):
                return m.author == interaction.user and m.channel.type == discord.ChannelType.private
            await interaction.user.send('You have started the application process. Please answer the following questions, type cancel to cancel the process.')
            questions = []
            if os.path.exists('Apps.json'):
                with open('Apps.json', 'r') as f:
                    apps = json.load(f)
                if custom_id in apps:
                    questions = apps[custom_id]
                    answers = []
                    for i, question in enumerate(questions, start=1):
                        await interaction.user.send(f'{i}. {question}')
                        answer = await bot.wait_for('message', check=check)
                        if answer.content.lower() == "cancel":
                            await interaction.user.send('Application process cancelled.')
                            break
                        else:
                            answers.append(answer.content)
                    embed = discord.Embed(title=f'{custom_id} Application - {interaction.user.name} ({interaction.user.id})')
                    for i, (question, answer) in enumerate(zip(questions, answers), start=1):
                        embed.add_field(name=f'{i}. {question}', value=f"```\n{answer}\n```", inline=False)
                    view = discord.ui.View()
                    upvote_button = discord.ui.Button(label='0/3 Upvote', style=discord.ButtonStyle.blurple, custom_id=f'upvote_{interaction.user.id}')
                    downvote_button = discord.ui.Button(label='0/3 Downvote', style=discord.ButtonStyle.blurple, custom_id=f'downvote_{interaction.user.id}')
                    accept_button = discord.ui.Button(label='Accept', style=discord.ButtonStyle.green, custom_id=f'accept_{interaction.user.id}')
                    decline_button = discord.ui.Button(label='Decline', style=discord.ButtonStyle.red, custom_id=f'decline_{interaction.user.id}')
                    send_dm_button = discord.ui.Button(label='Send DM', style=discord.ButtonStyle.blurple, custom_id=f'senddm_{interaction.user.id}')
                    view.add_item(upvote_button)
                    view.add_item(downvote_button)
                    view.add_item(accept_button)
                    view.add_item(decline_button)
                    view.add_item(send_dm_button)
                    await interaction.user.send('Please confirm your answers.')
                    await interaction.user.send(embed=embed)
                    await interaction.user.send('Type confirm to submit your application.')
                    confirm = await bot.wait_for('message', check=check)
                    if confirm.content.lower() == 'confirm':
                        await interaction.user.send('Application submitted.')
                        if os.path.exists('logging_channel.txt'):
                            with open('logging_channel.txt', 'r') as f:
                                logging_channel_id = int(f.read())
                            logging_channel = bot.get_channel(logging_channel_id)
                            thread = await logging_channel.create_thread(name=interaction.user.name)
                            await thread.send(embed=embed, view=view)
                            await thread.send("<@&1313913035932307487>")
                        else:
                            await interaction.user.send('Logging channel not setup.')
                    else:
                        await interaction.user.send('Application not submitted.')
                        
import os
TOKEN = os.getenv("BOTTOKEN")
bot.run(TOKEN)
