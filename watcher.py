import discord  # type: ignore
import asyncio
from discord.ext import commands  # type: ignore

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix="..", intents=intents)
watched_users = set()
online_users = set()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

@bot.command()
async def Help(ctx):
    embed = discord.Embed(
        title="Bot Commands",
        description="",
        color=discord.Color(0x000000)  # Black color for the embed
    )
    
    embed.add_field(name="**..ping**", value="Check bot latency.", inline=False)
    embed.add_field(name="**..s**", value="View last sniped message.", inline=False)
    embed.add_field(name="**..cs**", value="Clear last sniped message.", inline=False)
    embed.add_field(name="**..p <amount>**", value="Purge messages.", inline=False)
    embed.add_field(name="**..l**", value="Lock channel.", inline=False)
    embed.add_field(name="**..ul**", value="Unlock channel.", inline=False)

    await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_members=True)
async def t(ctx, member: discord.Member, duration: int):
    """
    Timeout a member for a given duration in seconds.
    """
    try:
        timeout_duration = discord.utils.utcnow() + timedelta(seconds=duration)  # Set timeout duration
        await member.timeout(timeout_duration)  # Apply timeout
        await ctx.send(f"✅ {member.mention} has been timed out for {duration} seconds.")

        # Add a check mark reaction to the message to indicate success
        await ctx.message.add_reaction("✅")

    except discord.Forbidden:
        await ctx.send("❌ I do not have permission to timeout members.")
        await ctx.message.add_reaction("❌")  # Add red X on failure
    except discord.HTTPException as e:
        await ctx.send(f"⚠️ Error while timing out: {e}")
        await ctx.message.add_reaction("❌")  # Add red X on failure

@bot.command()
@commands.has_permissions(manage_members=True)
async def ut(ctx, member: discord.Member):
    """
    Untimeout a member.
    """
    try:
        await member.timeout(None)  # Remove timeout
        await ctx.send(f"✅ {member.mention}'s timeout has been removed.")

        # Add a check mark reaction to the message to indicate success
        await ctx.message.add_reaction("✅")

    except discord.Forbidden:
        await ctx.send("❌ I do not have permission to untimeout members.")
        await ctx.message.add_reaction("❌")  # Add red X on failure
    except discord.HTTPException as e:
        await ctx.send(f"⚠️ Error while removing timeout: {e}")
        await ctx.message.add_reaction("❌")  # Add red X on failure

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
        await ctx.send("Cleared!")
    else:
        await ctx.send("There's nothing to clear!")

        
@bot.command()
@commands.has_permissions(manage_messages=True)
async def p(ctx, amount: int = None):
    if amount is None:
        await ctx.send("❌ State amount.", delete_after=5)
        return
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"✅", delete_after=3)


@bot.command()
@commands.has_permissions(manage_channels=True)
async def l(ctx):
    bot_member = ctx.guild.me  # Bot's member object
    owner1 = ctx.guild.get_member(707584409531842623)  # Your first ID
    owner2 = ctx.guild.get_member(1343671645637967975)  # Second ID

    # Check if the bot has the required permission
    if not ctx.channel.permissions_for(bot_member).manage_channels:
        await ctx.send("❌ I don't have permission to manage this channel!")
        return
    
    # Lock for @everyone
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)

    # Allow both users to send messages
    if owner1:
        await ctx.channel.set_permissions(owner1, send_messages=True)
    if owner2:
        await ctx.channel.set_permissions(owner2, send_messages=True)

    await ctx.send("🔒 Channel locked!")

@bot.command()
@commands.has_permissions(manage_channels=True)
async def ul(ctx):
    bot_member = ctx.guild.me

    if not ctx.channel.permissions_for(bot_member).manage_channels:
        await ctx.send("❌ I don't have permission to manage this channel!")
        return

    # Unlock for @everyone
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
    await ctx.send("🔓 Channel unlocked!")


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
