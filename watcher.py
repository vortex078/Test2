import discord  # type: ignore
import asyncio
from discord.ext import commands  # type: ignore

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.presences = True

bot = commands.Bot(command_prefix=".", intents=intents)
watched_users = set()
online_users = set()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# Snipe Command (.s) - Retrieve last deleted message
@bot.command()
async def s(ctx):
    global sniped_message
    if sniped_message:
        await ctx.send(f"**Sniped Message:**\n👤 {sniped_message['author']}:\n📜 {sniped_message['content']}")
    else:
        await ctx.send("❌ No recently deleted messages found.")

# Clear Sniped Message (.cs)
@bot.command()
async def cs(ctx):
    global sniped_message
    sniped_message = None
    await ctx.send("✅ Cleared sniped message from memory.")

# Store Deleted Messages
@bot.event
async def on_message_delete(message):
    global sniped_message
    if not message.author.bot:  # Ignore bot messages
        sniped_message = {"author": message.author.name, "content": message.content}

# Purge Messages (.p <amount>)
@bot.command()
@commands.has_permissions(manage_messages=True)
async def p(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"✅ Deleted {amount} messages.", delete_after=3)

# Lock Channel (.l)
@bot.command()
@commands.has_permissions(manage_channels=True)
async def l(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.send("🔒 Channel locked!")

# Unlock Channel (.ul)
@bot.command()
@commands.has_permissions(manage_channels=True)
async def ul(ctx):
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
