import discord # type: ignore
from discord.ext import commands # type: ignore
from datetime import timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required for role and moderation actions
bot = commands.Bot(command_prefix="..", intents=intents)

rules_storage = {}
OWNER_ID = 707584409531842623
admins = {OWNER_ID}

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

@bot.command(name="addadmin")
async def add_admin(ctx, member: discord.Member):
    """Allows the OWNER to add a new admin."""
    if ctx.author.id != OWNER_ID:
        await ctx.send("⛔ Only the **bot owner** can add admins!")
        return

    admins.add(member.id)
    await ctx.send(f"✅ **{member.name}** has been added as an admin!")

@bot.command(name="removeadmin")
async def remove_admin(ctx, member: discord.Member):
    """Allows the OWNER to remove an admin."""
    if ctx.author.id != OWNER_ID:
        await ctx.send("⛔ Only the **bot owner** can remove admins!")
        return

    if member.id == OWNER_ID:
        await ctx.send("⚠ You cannot remove yourself as an admin!")
        return

    if member.id in admins:
        admins.remove(member.id)
        await ctx.send(f"❌ **{member.name}** has been removed as an admin.")
    else:
        await ctx.send("⚠ This user is **not an admin**!")

@bot.command(name="set")
@is_admin()
async def set_rules(ctx, *, rules_text: str):
    """Allows an admin to set the server rules."""
    rules_storage[ctx.guild.id] = rules_text
    await ctx.send("✅ Rules have been set successfully!")

@bot.command(name="edit")
@is_admin()
async def edit_rules(ctx, *, new_rules: str = None):
    """Edits the existing rules."""
    if ctx.guild.id not in rules_storage:
        await ctx.send("⚠ No rules found. Use `..set (rules)` first.")
        return

    if not new_rules:
        await ctx.send("⚠ Please provide new rules. Example:\n`..edit Be nice to everyone.`")
        return

    rules_storage[ctx.guild.id] = new_rules
    await ctx.send("✅ Rules have been updated successfully!")

@bot.command(name="del")
@is_admin()
async def delete_rules(ctx):
    """Deletes the stored server rules."""
    if ctx.guild.id in rules_storage:
        del rules_storage[ctx.guild.id]
        await ctx.send("🗑 Rules have been **deleted** successfully!")
    else:
        await ctx.send("⚠ No rules are set to delete.")

@bot.command(name="rules")
async def show_rules(ctx):
    """Displays the stored server rules."""
    rules_text = rules_storage.get(ctx.guild.id, "⚠ No rules have been set yet. Use `..set (rules)` to set them.")

    embed = discord.Embed(
        title="📜 Server Rules",
        description=rules_text,
        color=discord.Color.from_rgb(0, 0, 0)
    )

    await ctx.send(embed=embed)

@bot.command(name="Help")
async def help_command(ctx):
    """Displays all available bot commands."""
    description = "Here are the available commands:\n"

    # General commands
    description += "\n`..rules`: Displays the current server rules."

    # Admin commands (for admins)
    if ctx.author.id in admins:
        description += "\n`..set <text>`: Sets the server rules."
        description += "\n`..edit <text>`: Edits the existing rules."
        description += "\n`..del`: Deletes the stored server rules."
        description += "\n`..kick @user <reason>`: Kicks user with reason."
        description += "\n`..ban @user <reason>`: Bans user with reason."
        description += "\n`..time @user <length>`: Times-out member."
        description += "\n`..notime @user <length>`: Removes time-out from member."
        description += "\n`..add @user <role>`: Gives role."
        description += "\n`..rem @user <role>`: Removes role."

    # Owner-specific commands (for the bot owner)
    if ctx.author.id == OWNER_ID:
        description += "\n`..addadmin @user`: Adds a new admin."
        description += "\n`..removeadmin @user`: Removes an admin."

    embed = discord.Embed(
        title="🤖 Bot Commands",
        description=description,
        color=discord.Color.from_rgb(0, 0, 0)
    )

    await ctx.send(embed=embed)


@bot.command(name="kick")
@is_admin()
async def kick(ctx, member: discord.Member = None, *, reason: str = None):
    """Kicks a member from the server, requiring a reason."""
    if not member or not reason:
        await ctx.send("⚠ **Usage:** `..kick @user [reason]`\nExample: `..kick @user Spamming`")
        return

    await member.kick(reason=reason)
    await ctx.send(f"🔨 **{member.name}** has been kicked. Reason: {reason}")


@bot.command(name="ban")
@is_admin()
async def ban(ctx, member: discord.Member = None, *, reason: str = None):
    """Bans a member from the server, requiring a reason."""
    if not member or not reason:
        await ctx.send("⚠ **Usage:** `..ban @user [reason]`\nExample: `..ban @user Harassment`")
        return

    await member.ban(reason=reason)
    await ctx.send(f"🔨 **{member.name}** has been banned. Reason: {reason}")

@bot.command(name="time")
@is_admin()
async def timeout(ctx, member: discord.Member = None, length: str = None):
    """Times out a member for a given length (m for minutes, h for hours)."""
    if not member or not length:
        await ctx.send("⚠ **Usage:** `..time @user (length) m/h`\nExample: `..time @user 10m` or `..time @user 2h`")
        return
    
    try:
        unit = length[-1].lower()
        value = int(length[:-1])
        
        if unit == "m":
            duration = timedelta(minutes=value)
        elif unit == "h":
            duration = timedelta(hours=value)
        else:
            await ctx.send("⚠ Invalid time format! Use `m` for minutes or `h` for hours.")
            return
        
        await member.timeout(duration, reason="Admin-issued timeout")
        await ctx.send(f"⏳ **{member.name}** has been timed out for {value}{unit}.")
    except ValueError:
        await ctx.send("⚠ Invalid number format! Use `..time @member (length)m/h`")

@bot.command(name="notime")
@is_admin()
async def remove_timeout(ctx, member: discord.Member = None):
    """Removes timeout from a user."""
    if not member:
        await ctx.send("⚠ **Usage:** `..notime @user`")
        return
    
    await member.edit(timed_out_until=None)
    await ctx.send(f"❌ **{member.name}**'s timeout has been removed.")

@bot.command(name="ping")
async def ping(ctx):
    """Responds with the bot's latency to check if the bot is working."""
    latency = round(bot.latency * 1000)  # Latency in milliseconds
    await ctx.send(f"🏓 Pong! Latency is {latency}ms")

@bot.command(name="add")
@is_admin()
async def add_role(ctx, member: discord.Member = None, *, role_name: str = None):
    """Adds a role to a member using a keyword search."""
    if not member or not role_name:
        await ctx.send("⚠ **Usage:** `..add @user <role>`\nExample: `..add @user Member`")
        return

    # Find roles that match the keyword (case-insensitive)
    matching_roles = [role for role in ctx.guild.roles if role_name.lower() in role.name.lower()]

    if not matching_roles:
        await ctx.send(f"⚠ No roles found with the keyword `{role_name}`.")
        return

    if len(matching_roles) > 1:
        roles_list = "\n".join([role.name for role in matching_roles])
        await ctx.send(f"⚠ Multiple roles found with the keyword `{role_name}`:\n{roles_list}\nPlease be more specific.")
        return

    role = matching_roles[0]
    
    # Check if the bot has permission to assign the role
    if role.position >= ctx.author.top_role.position:
        await ctx.send(f"⚠ You cannot assign the role `{role.name}` as it is higher than your top role.")
        return
    
    await member.add_roles(role)
    await ctx.send(f"✅ **{member.name}** has been given the role `{role.name}`.")

@bot.command(name="rem")
@is_admin()
async def remove_role(ctx, member: discord.Member = None, *, role_name: str = None):
    """Removes a role from a member using a keyword search."""
    if not member or not role_name:
        await ctx.send("⚠ **Usage:** `..rem @user <role>`\nExample: `..rem @user Member`")
        return

    # Find roles that match the keyword (case-insensitive)
    matching_roles = [role for role in ctx.guild.roles if role_name.lower() in role.name.lower()]

    if not matching_roles:
        await ctx.send(f"⚠ No roles found with the keyword `{role_name}`.")
        return

    if len(matching_roles) > 1:
        roles_list = "\n".join([role.name for role in matching_roles])
        await ctx.send(f"⚠ Multiple roles found with the keyword `{role_name}`:\n{roles_list}\nPlease be more specific.")
        return

    role = matching_roles[0]
    
    # Check if the bot has permission to remove the role
    if role.position >= ctx.author.top_role.position:
        await ctx.send(f"⚠ You cannot remove the role `{role.name}` as it is higher than your top role.")
        return
    
    await member.remove_roles(role)
    await ctx.send(f"✅ **{member.name}** has been removed from the role `{role.name}`.")

import os
TOKEN = os.getenv("DISCORD_TOKEN")  # Get token from environment
bot.run(TOKEN)
