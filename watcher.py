import discord  # type: ignore
import asyncio
from discord.ext import commands  # type: ignore
from datetime import timedelta
import random
import time
import re

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="..", intents=intents, help_command=None)
watched_users = set()
online_users = set()

rules_storage = {}
OWNER_ID = 707584409531842623
# Hardcoded admins (cannot be removed)
HARD_CODED_ADMINS = {OWNER_ID, 1041268209011138660, 620200699300413442, 1324836606812623011}  # Replace with actual IDs

# Set containing both hardcoded and dynamically added admins
admins = set(HARD_CODED_ADMINS)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

def is_admin():
    async def predicate(ctx):
        if ctx.author.id in admins:
            return True
        await ctx.send("⛔ You **do not** have permission to use this command!")
        return False
    return commands.check(predicate)

def get_all_admins():
    return HARD_CODED_ADMINS | admins

@bot.command(name="addadmin")
async def add_admin(ctx, member: discord.Member):
    if ctx.author.id != OWNER_ID:
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(1)
        await ctx.message.delete()
        return

    admins.add(member.id)  # Add to admin list
    await ctx.message.add_reaction("✅")
    await asyncio.sleep(1)
    await ctx.message.delete()

@bot.command(name="removeadmin")
async def remove_admin(ctx, member: discord.Member):
    if ctx.author.id != OWNER_ID:
        await ctx.message.add_reaction("❌")
        return

    if member.id in admins:
        admins.remove(member.id)
        await ctx.message.add_reaction("✅")
        await asyncio.sleep(1)
        await ctx.message.delete()
    else:
        await ctx.send("⚠ This user is **not an admin**!")
        await asyncio.sleep(2)
        await ctx.message.delete()

@bot.command(name="listadmins")
async def list_admins(ctx):
    if not admins:
        await ctx.send("⚠ No admins found!")
        await asyncio.sleep(1)
        await ctx.message.delete()
        return

    hardcoded_admins = []
    added_admins = []

    for admin_id in admins:
        member = ctx.guild.get_member(admin_id)
        admin_name = member.name if member else f"Unknown User ({admin_id})"

        if admin_id in HARD_CODED_ADMINS:
            hardcoded_admins.append(admin_name)
        else:
            added_admins.append(admin_name)

    hardcoded_text = "\n".join(hardcoded_admins) if hardcoded_admins else "None"
    added_text = "\n".join(added_admins) if added_admins else "None"

    embed = discord.Embed(title="👑 Admin List", color=discord.Color.gold())
    embed.description = f"🔸 **Hardcoded Admins**\n{hardcoded_text}\n\n🔹 **Added Admins**\n{added_text}"

    await ctx.send(embed=embed)

afk_users = {}

@bot.command()
async def afk(ctx, *, reason: str = "AFK"):
    # Store the time when AFK is set
    afk_users[ctx.author.id] = {"reason": reason, "time": time.time()}

    embed = discord.Embed(
        description=f"✅ {ctx.author.mention}: You're now AFK with the status: **{reason}**",
        color=discord.Color.from_rgb(0, 0, 0)
    )
    await ctx.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author.id in afk_users:
        # Calculate how long ago the user set their AFK status
        afk_time = afk_users[message.author.id]["time"]
        time_ago = time.time() - afk_time
        minutes = int(time_ago // 60)
        seconds = int(time_ago % 60)
        
        # Remove the AFK status when the user sends a message
        del afk_users[message.author.id]
        
        embed = discord.Embed(
            description=f"✅ {message.author.mention}, you're no longer AFK.",
            color=discord.Color.from_rgb(0, 0, 0)
        )
        await message.channel.send(embed=embed)

    for mention in message.mentions:
        if mention.id in afk_users:
            reason = afk_users[mention.id]["reason"]
            # Calculate how long ago the AFK was set for the mentioned user
            afk_time = afk_users[mention.id]["time"]
            time_ago = time.time() - afk_time
            minutes = int(time_ago // 60)
            seconds = int(time_ago % 60)
            time_display = f"{minutes} minutes and {seconds} seconds ago"

            embed = discord.Embed(
                description=f":warning: {mention.mention} is AFK: **{reason}** - ({time_display})",
                color=discord.Color.from_rgb(0, 0, 0)
            )
            await message.channel.send(embed=embed)

    await bot.process_commands(message)


@bot.command(name="i")
@is_admin()  # Admins only
async def set_or_show_rules(ctx, *, rules_text: str = None):
    if rules_text:
        # If there is rules_text, we are setting it
        rules_storage[ctx.guild.id] = rules_text
        
        # Delete the original message that invoked the command
        await ctx.message.delete()

        # Check if the command is a reply to another message
        if ctx.message.reference:
            # Get the original message being replied to
            original_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

            # Create and send the embed as a reply to the original message
            embed = discord.Embed(
                description=rules_text,
                color=discord.Color.from_rgb(0, 0, 0)
            )
            await original_message.reply(embed=embed)
        else:
            # If the command isn't a reply, just send the embed normally
            embed = discord.Embed(
                description=rules_text,
                color=discord.Color.from_rgb(0, 0, 0)
            )
            await ctx.send(embed=embed)
    else:
        # If no rules_text is provided, show the current stored info
        stored_rules = rules_storage.get(ctx.guild.id, "⚠ No information has been set yet. Use `..info (text)` to set them.")

        embed = discord.Embed(
            description=stored_rules,
            color=discord.Color.from_rgb(0, 0, 0)
        )

        # Check if the command is a reply to another message
        if ctx.message.reference:
            # Get the original message being replied to
            original_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

            # Create and send the embed as a reply to the original message
            await original_message.reply(embed=embed)
        else:
            # If the command isn't a reply, just send the embed normally
            await ctx.send(embed=embed)

        await asyncio.sleep(0)
        await ctx.message.delete()


@bot.command(name="kick")
@is_admin()
async def kick(ctx, member: discord.Member = None, *, reason: str = None):
    if not member or not reason:
        await ctx.send("⚠ **Usage:** `..kick @user <reason>`\nExample: `..kick @user Spamming`")
        await asyncio.sleep(3)
        await ctx.message.delete() 
        return

    try:
        # Send DM to the user before kicking them
        await member.send(f"You have been kicked from **{ctx.guild.name}**\nReason: {reason}")
    except discord.Forbidden:
        # If we can't DM the user, notify the admin
        await ctx.send("⚠ Could not DM the user about their kick.")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except Exception as e:
        await ctx.send(f"⚠ Error sending DM: {str(e)}")
        await asyncio.sleep(3)
        await ctx.message.delete() 

    try:
        # Kick the member
        await member.kick(reason=reason)
        await ctx.message.add_reaction("✅")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except discord.Forbidden:
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except Exception as e:
        await ctx.send(f"❌ Error kicking member: {str(e)}")
        await asyncio.sleep(3)
        await ctx.message.delete() 

@bot.command(name="ban")
@is_admin()
async def ban(ctx, member: discord.Member = None, *, reason: str = None):
    if not member or not reason:
        await ctx.send("⚠ **Usage:** `..ban @user <reason>`\nExample: `..ban @user Harassment`")
        await asyncio.sleep(3)
        await ctx.message.delete() 
        return

    try:
        # Send DM to the user before banning them
        await member.send(f"You have been banned from **{ctx.guild.name}**\nReason: {reason}")
    except discord.Forbidden:
        # If we can't DM the user, notify the admin
        await ctx.send("⚠ Could not DM the user about their ban.")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except Exception as e:
        await ctx.send(f"⚠ Error sending DM: {str(e)}")
        await asyncio.sleep(3)
        await ctx.message.delete() 

    try:
        # Ban the member
        await member.ban(reason=reason)
        await ctx.message.add_reaction("✅")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except discord.Forbidden:
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except Exception as e:
        await ctx.send(f"❌ Error banning member: {str(e)}")
        await asyncio.sleep(3)
        await ctx.message.delete() 

@bot.command(name="unban")
@is_admin()
async def unban(ctx, user: discord.User = None):
    if not user:
        await ctx.send("⚠ **Usage:** `..unban @user` or `..unban <user_id>`")
        await asyncio.sleep(3)
        await ctx.message.delete() 
        return

    try:
        # Unban the user
        await ctx.guild.unban(user)
        await ctx.message.add_reaction("✅")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except discord.NotFound:
        await ctx.send("⚠ This user is not banned.")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except discord.Forbidden:
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except Exception as e:
        await ctx.send(f"⚠ An error occurred: {str(e)}")
        await asyncio.sleep(3)
        await ctx.message.delete() 

@bot.command()
@is_admin()
async def w(ctx, member: discord.Member = None, *, reason: str = None):
    if member is None:
        await ctx.send("❌ Provide member.")
        await asyncio.sleep(3)
        await ctx.message.delete() 
        return
    if reason is None:
        await ctx.send("❌ Provide reason.")
        await asyncio.sleep(3)
        await ctx.message.delete() 
        return

    try:
        # Send a DM to the member with the warning reason
        await member.send(f"You have been warned in {ctx.guild.name}.\nReason: {reason}")
        await ctx.message.delete()
        await ctx.send(f"✅ {member.mention} Warned! Reason: {reason}")

    except discord.Forbidden:
        # If the bot cannot DM the user, inform the command executor
        await ctx.send(f"❌ Cannot DM {member.mention}")
        await asyncio.sleep(3)
        await ctx.message.delete() 

@bot.command()
async def coin(ctx):
    # Define the possible outcomes
    outcomes = ['Heads', 'Tails']
    result = random.choice(outcomes)  # Randomly pick either Heads or Tails
    
    # Send the result to the channel, mentioning the user who invoked the command
    await ctx.message.delete() 
    await ctx.send(f'{ctx.author.mention} It\'s {result}!')

@bot.command()
@is_admin()
async def d(ctx):
    if not ctx.message.reference:
        await ctx.send("❌ You need to reply to a message to delete it.")
        await asyncio.sleep(3)
        await ctx.message.delete() 
        return

    # Get the message that is being replied to
    message_to_delete = ctx.message.reference.resolved

    try:
        # Delete the message
        await message_to_delete.delete()
        
        # React with ✅ on the original message
        await ctx.message.add_reaction("✅")
        await asyncio.sleep(0.5)
        await ctx.message.delete() 
    except discord.Forbidden:
        await ctx.send("❌ I do not have permission to delete messages.")
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except discord.HTTPException as e:
        await ctx.send(f"❌ Error deleting message: {e}")
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(3)
        await ctx.message.delete() 


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command(name="help")
async def help_command(ctx):
    await ctx.message.delete() 
    description = ""

    # General commands
    description += "\n`..info`: Displays info."
    description += "\n`..ping`: Latency check"

    # Admin commands (for admins)
    if ctx.author.id in admins:
        description += "\n`..kick @user <reason>`: Kicks user with reason."
        description += "\n`..ban @user <reason>`: Bans user with reason."
        description += "\n`..unban @user`: Un-bans user."
        description += "\n`..t @user <length>`: Times-out member."
        description += "\n`..ut @user`: Removes time-out from member."
        description += "\n`..l `: Locks current channel"
        description += "\n`..ul `: Unlocks current channel"
        description += "\n`..d `: Deletes message"
        description += "\n`..w @user <reason>`: Warns user."
        description += "\n`..p `: Purges messages"
        description += "\n`..s `: Snipes message"
        description += "\n`..cs `: Clears sniped message"
        description += "\n`..r `: Lists roles"
        description += "\n`..afk <reason>`: Sets AFK status."
        description += "\n`..coin `: Either heads or tails"
        description += "\n`..listadmins`: Lists all current admins."

    # Owner-specific commands (for the bot owner)
    if ctx.author.id == OWNER_ID:
        description += "\n`..addadmin @user`: Adds a new admin."
        description += "\n`..removeadmin @user`: Removes an admin."

    embed = discord.Embed(
        title="Bot Commands",
        description=description,
        color=discord.Color.from_rgb(0, 0, 0)
    )

    await ctx.send(embed=embed)

@bot.command()
@is_admin()
async def r(ctx, action: str = None, role_name: str = None, member: discord.Member = None):

    if action is None:
        # Display all roles in separate sections
        roles = ctx.guild.roles
        embed = discord.Embed(title="Roles in the server", color=discord.Color.blue())

        # Grouping roles into sections (e.g., Admin roles, Member roles)
        admin_roles = [role for role in roles if "admin" in role.name.lower()]
        member_roles = [role for role in roles if "member" in role.name.lower()]
        other_roles = [role for role in roles if role not in admin_roles and role not in member_roles]

        if admin_roles:
            embed.add_field(name="Admin Roles", value="\n".join([role.name for role in admin_roles]), inline=False)
        if member_roles:
            embed.add_field(name="Member Roles", value="\n".join([role.name for role in member_roles]), inline=False)
        if other_roles:
            embed.add_field(name="Other Roles", value="\n".join([role.name for role in other_roles]), inline=False)

        await ctx.send(embed=embed)

@bot.command()
@is_admin()
async def t(ctx, member: discord.Member, duration: str):

    try:
        # Check if the member is the bot owner
        if member.id == OWNER_ID:
            await ctx.message.add_reaction("⚠️")
            await asyncio.sleep(1)
            await ctx.message.delete()
            return
        
        # Parse the duration
        match = re.match(r"(\d+)([smh])", duration.lower())  # Match digits followed by s/m/h
        if not match:
            await ctx.send("⚠️ Invalid duration format. Please use `1s` for seconds, `1m` for minutes, or `1h` for hours.")
            return

        time_value = int(match.group(1))  # Get the numeric part
        time_unit = match.group(2)  # Get the unit (s, m, h)

        # Convert the duration to seconds
        if time_unit == "s":
            timeout_duration = timedelta(seconds=time_value)
        elif time_unit == "m":
            timeout_duration = timedelta(minutes=time_value)
        elif time_unit == "h":
            timeout_duration = timedelta(hours=time_value)

        # Apply the timeout
        timeout_end = discord.utils.utcnow() + timeout_duration  # Set timeout end time
        await member.timeout(timeout_end)  # Apply timeout

        # Add a check mark reaction to the message to indicate success
        await ctx.message.add_reaction("✅")
        await asyncio.sleep(3)
        await ctx.message.delete()

    except discord.Forbidden:
        await ctx.message.add_reaction("❌")  # Add red X on failure (if bot doesn't have permission)
        await asyncio.sleep(3)
        await ctx.message.delete()
    except discord.HTTPException as e:
        await ctx.send(f"⚠️ Error while timing out: {e}")
        await ctx.message.add_reaction("❌")  # Add red X on failure
        await asyncio.sleep(3)
        await ctx.message.delete()

@bot.command()
@is_admin()
async def ut(ctx, member: discord.Member):

    try:
        await member.timeout(None)  # Remove timeout

        # Add a check mark reaction to the message to indicate success
        await ctx.message.add_reaction("✅")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except discord.Forbidden:
        await ctx.message.add_reaction("❌")  # Add red X on failure
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except discord.HTTPException as e:
        await ctx.send(f"⚠️ Error while removing timeout: {e}")
        await ctx.message.add_reaction("❌")  # Add red X on failure
        await asyncio.sleep(3)
        await ctx.message.delete() 

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)  # Convert from seconds to milliseconds
    await ctx.send(f"{latency}ms")

sniped_messages = {}  # Global variable to store deleted messages per channel

@bot.event
async def on_message_delete(message):
    if message.author.bot:  # Ignore bot messages
        return
    sniped_messages[message.channel.id] = message  # Save the deleted message for the channel
    print(f"Deleted message in {message.channel.name}: {message.content}")  # Debugging line to confirm deletion is detected

@bot.command()
async def s(ctx):
    if ctx.channel.id in sniped_messages:
        sniped_message = sniped_messages[ctx.channel.id]

        # Create embed to display the sniped message
        embed = discord.Embed(
            title="Sniped Message",
            description=sniped_message.content if sniped_message.content else "*[No Text]*",
            color=discord.Color(0x000000),
            timestamp=sniped_message.created_at
        )
        embed.set_author(name=sniped_message.author, icon_url=sniped_message.author.avatar.url if sniped_message.author.avatar else None)
        embed.set_footer(text=f"Deleted in #{sniped_message.channel.name}")

        # Check if there are attachments, and if so, add them to the embed
        if sniped_message.attachments:
            attachment = sniped_message.attachments[0]  # Get the first attachment
            embed.set_image(url=attachment.url)  # Display the attachment image in the embed

        await ctx.send(embed=embed)
    else:
        await ctx.send("Nothing found.")

@bot.command()
async def cs(ctx):
    if ctx.channel.id in sniped_messages:
        del sniped_messages[ctx.channel.id]  # Clear the message for that channel
        await ctx.message.add_reaction("✅")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    else:
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(3)
        await ctx.message.delete() 

        
@bot.command()
@is_admin()
async def p(ctx, amount: int = None):

    if ctx.message.reference:  # Check if the command was used as a reply
        try:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            messages = []
            async for msg in ctx.channel.history(limit=200):  # Scan last 200 messages
                messages.append(msg)
                if msg.id == ref_msg.id:
                    break  # Stop at the replied message

            if messages:
                await ctx.channel.delete_messages(messages)
                confirm_msg = await ctx.send("✅.")
                await asyncio.sleep(3)
                await confirm_msg.delete()
            else:
                error_msg = await ctx.send("❌ Couldn't find the message.")
                await asyncio.sleep(3)
                await error_msg.delete()
        except discord.Forbidden:
            error_msg = await ctx.send("❌ No permission.")
            await asyncio.sleep(3)
            await error_msg.delete()
        except discord.HTTPException as e:
            error_msg = await ctx.send(f"❌ Error: {str(e)}")
            await asyncio.sleep(3)
            await error_msg.delete()

    else:  # Normal purge behavior
        if amount is None:
            await ctx.message.delete()
            message = await ctx.send("❌ State amount.")
            await asyncio.sleep(3)
            await message.delete()
            return

        try:
            deleted = await ctx.channel.purge(limit=amount + 1)
            confirm_msg = await ctx.send("✅.")
            await asyncio.sleep(3)
            await confirm_msg.delete()
        except discord.Forbidden:
            error_msg = await ctx.send("❌.")
            await asyncio.sleep(3)
            await error_msg.delete()
        except discord.HTTPException as e:
            error_msg = await ctx.send(f"❌ Error: {str(e)}")
            await asyncio.sleep(3)
            await error_msg.delete()



@bot.command()
@is_admin()
async def l(ctx):
    bot_member = ctx.guild.me  # Bot's member object
    owner1 = ctx.guild.get_member(707584409531842623)  # Your first ID
    owner2 = ctx.guild.get_member(1343671645637967975)  # Second ID

    # Check if the bot has the required permission
    if not ctx.channel.permissions_for(bot_member).manage_channels:
        await ctx.message.add_reaction("❌")
        return
    
    # Lock for @everyone
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)

    # Allow both users to send messages
    if owner1:
        await ctx.channel.set_permissions(owner1, send_messages=True)
    if owner2:
        await ctx.channel.set_permissions(owner2, send_messages=True)

    await ctx.message.add_reaction("🔒")

@bot.command()
@is_admin()
async def ul(ctx):
    bot_member = ctx.guild.me

    if not ctx.channel.permissions_for(bot_member).manage_channels:
        await ctx.message.add_reaction("❌")
        return

    # Unlock for @everyone
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.message.add_reaction("🔓")


@bot.command()
async def add(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Please mention a member to add.")
        return
    watched_users.add(member.id)
    await ctx.send(f'Added {member.name} to the watchlist!')

@bot.command()
async def rem(ctx, member: discord.Member = None):
    if member is None:
        await ctx.send("Please mention a member to remove.")
        return
    watched_users.discard(member.id)
    online_users.discard(member.id)
    await ctx.send(f'Removed {member.name} from the watchlist!')

@bot.command()
async def test(ctx):
    user = bot.get_user(707584409531842623)
    if user:
        await user.send("Test message: Bot is working!")
        await ctx.send("Test DM sent!")
    else:
        await ctx.send("Failed to find user.")

@bot.event
async def on_presence_update(before, after):
    if after.id in watched_users:
        print(f"on_presence_update triggered for {after.name}: {before.status} -> {after.status}")

        try:
            # Fetch the bot owner (YOU) to ensure the DM is sent correctly
            user = await bot.fetch_user(707584409531842623)  # Replace with your Discord ID

            # Debugging: Check if we are detecting the transition correctly
            if before.status == after.status:
                print(f"🔹 Status didn't change: {after.name} remains {after.status}")
                return  # No need to send a duplicate DM

            # Build the DM message
            message = f"<@707584409531842623> **{after.name}: {before.status} → {after.status}!** "

            # Send DM
            await user.send(message)
            print(f"📩 Sent DM: {message}")

        except discord.Forbidden:
            print(f"❌ Cannot send DM to owner (Forbidden). Check Discord DM settings.")
        except discord.HTTPException as e:
            print(f"⚠️ Error sending DM: {e}")


import os
TOKEN = os.getenv("watch")
bot.run(TOKEN)
