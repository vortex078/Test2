import discord  # type: ignore
import asyncio
from discord.ext import commands  # type: ignore
from datetime import timedelta
import random
import time
import re
import json
from datetime import datetime
from collections import deque


intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
intents.presences = True
intents.guilds = True

bot = commands.Bot(command_prefix="..", intents=intents, help_command=None)
watched_users = set()
online_users = set()

rules_storage = {}

OWNER_ID = 707584409531842623

ADMIN_FILE = "admins.json"

active_games = {}

class Card:
    def __init__(self, rank, color):
        self.rank = rank
        self.color = color
    
    def __str__(self):
        return f"{self.rank} of {self.color}"

class Deck:
    def __init__(self):
        colors = ['Red', 'Blue', 'Green', 'Yellow']
        ranks = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'Skip', 'Reverse', 'Draw2']
        self.cards = [Card(rank, color) for color in colors for rank in ranks] * 2  # Two sets of each card
        self.cards += [Card('Wild', 'Wild'), Card('WildDraw4', 'Wild')] * 4  # Add wild cards
        random.shuffle(self.cards)

    def draw(self):
        return self.cards.pop() if self.cards else None

class Player:
    def __init__(self, user):
        self.user = user
        self.hand = []

    def draw_card(self, deck):
        card = deck.draw()
        if card:
            self.hand.append(card)
        return card

    def play_card(self, card):
        self.hand.remove(card)
        return card

class Game:
    def __init__(self, host):
        self.players = [Player(host)]
        self.deck = Deck()
        self.discard_pile = deque([self.deck.draw()])  # Start with one card in the discard pile
        self.turn_order = deque([host])
        self.current_player = host
        self.direction = 1  # 1 for clockwise, -1 for counter-clockwise
        self.game_over = False

    def add_player(self, user):
        if len(self.players) < 10:  # Limit number of players to 10
            self.players.append(Player(user))
            self.turn_order.append(user)
            return True
        return False

    def next_turn(self):
        if self.direction == 1:
            self.turn_order.rotate(-1)
        else:
            self.turn_order.rotate(1)
        self.current_player = self.turn_order[0]

    def get_valid_moves(self, player):
        valid_moves = []
        top_card = self.discard_pile[0]
        for card in player.hand:
            if card.color == top_card.color or card.rank == top_card.rank or card.color == 'Wild':
                valid_moves.append(card)
        return valid_moves

    def play_card(self, player, card):
        self.discard_pile.appendleft(card)
        if card.rank == 'Skip':
            self.next_turn()  # Skip the next player's turn
        elif card.rank == 'Reverse':
            self.direction *= -1  # Reverse the direction of play
        elif card.rank == 'Draw2':
            next_player = self.turn_order[1] if self.direction == 1 else self.turn_order[-1]
            next_player.draw_card(self.deck)
            next_player.draw_card(self.deck)
            self.next_turn()
        elif card.rank == 'Wild':
            pass  # Wild card can be played, no special effect yet
        elif card.rank == 'WildDraw4':
            next_player = self.turn_order[1] if self.direction == 1 else self.turn_order[-1]
            next_player.draw_card(self.deck)
            next_player.draw_card(self.deck)
            next_player.draw_card(self.deck)
            next_player.draw_card(self.deck)
            self.next_turn()

        player.play_card(card)
        self.next_turn()

    def check_game_over(self):
        for player in self.players:
            if len(player.hand) == 0:
                self.game_over = True
                return player
        return None

def load_hardcoded_admins():
    try:
        with open(ADMIN_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()

def save_hardcoded_admins():
    with open(ADMIN_FILE, "w") as f:
        json.dump(list(HARD_CODED_ADMINS), f)


HARD_CODED_ADMINS = load_hardcoded_admins()
HARD_CODED_ADMINS.add(OWNER_ID)

temporary_admins = set()

def is_admin():
    async def predicate(ctx):
        return ctx.author.id in HARD_CODED_ADMINS or ctx.author.id in temporary_admins
    return commands.check(predicate)

@bot.command(name="aa")
async def add_temp_admin(ctx, member: discord.Member):
    if ctx.author.id != OWNER_ID:
        await ctx.message.add_reaction("❌")
        return

    if member.id in HARD_CODED_ADMINS or member.id in temporary_admins:
        await ctx.send("⚠ This user is already a temporary admin!")
        await asyncio.sleep(1)
        await ctx.message.delete()
        return

    temporary_admins.add(member.id)
    await ctx.message.add_reaction("✅")
    await asyncio.sleep(1)
    await ctx.message.delete()

@bot.command(name="ra")
async def remove_temp_admin(ctx, member: discord.Member):
    if ctx.author.id != OWNER_ID:
        await ctx.message.add_reaction("❌")
        return

    if member.id in temporary_admins:
        temporary_admins.remove(member.id)
        await ctx.message.add_reaction("✅")
        await asyncio.sleep(1)
        await ctx.message.delete()
    else:
        await ctx.send("⚠ This user is **not a temporary admin**!")
        await asyncio.sleep(1)
        await ctx.message.delete()

@bot.command(name="ha")
async def add_hardcoded_admin(ctx, member: discord.Member):
    if ctx.author.id != OWNER_ID:
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(1)
        await ctx.message.delete()
        return

    if member.id in HARD_CODED_ADMINS:
        await ctx.send("⚠ This user is **already a hardcoded admin**!")
        return

    HARD_CODED_ADMINS.add(member.id)
    save_hardcoded_admins()
    await ctx.message.add_reaction("✅")
    await asyncio.sleep(1)
    await ctx.message.delete()

@bot.command(name="hr")
async def remove_hardcoded_admin(ctx, member: discord.Member):
    if ctx.author.id != OWNER_ID:
        await ctx.message.add_reaction("❌")
        return

    if member.id not in HARD_CODED_ADMINS:
        await ctx.send("⚠ This user is **not a hardcoded admin**!")
        return

    HARD_CODED_ADMINS.remove(member.id)
    save_hardcoded_admins()
    await ctx.message.add_reaction("✅")
    await asyncio.sleep(1)
    await ctx.message.delete()

@bot.command(name="la")
async def list_admins(ctx):
    if not HARD_CODED_ADMINS and not temporary_admins:
        await ctx.send("⚠ No admins found!")
        await asyncio.sleep(1)
        await ctx.message.delete()
        return

    hardcoded_admins = []
    temp_admins = []

    async def get_username(user_id):
        member = ctx.guild.get_member(user_id)
        if member:
            return member.name
        try:
            user = await bot.fetch_user(user_id)
            return user.name
        except discord.NotFound:
            return f"Unknown ({user_id})"

    for admin_id in HARD_CODED_ADMINS:
        username = await get_username(admin_id)
        hardcoded_admins.append(username)

    for admin_id in temporary_admins:
        username = await get_username(admin_id)
        temp_admins.append(username)

    hardcoded_text = "\n".join(hardcoded_admins) if hardcoded_admins else "None"
    temp_text = "\n".join(temp_admins) if temp_admins else "None"

    embed = discord.Embed(title="👑 Admin List", color=discord.Color.gold())
    embed.description = f"🔸 **Hardcoded Admins**\n{hardcoded_text}\n\n🔹 **Temporary Admins**\n{temp_text}"

    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command(name="start_game")
async def start_game(ctx):
    if ctx.guild.id in active_games:
        await ctx.send("A game is already running!")
        return
    game = Game(ctx.author)
    active_games[ctx.guild.id] = game
    await ctx.send(f"Game started by {ctx.author.mention}! Type `..join` to join the game.")

@bot.command(name="join")
async def join_game(ctx):
    game = active_games.get(ctx.guild.id)
    if not game:
        await ctx.send("No game is running!")
        return
    if game.add_player(ctx.author):
        await ctx.send(f"{ctx.author.mention} has joined the game!")
    else:
        await ctx.send("The game is full!")

@bot.command(name="play")
async def play_card(ctx, card_name: str):
    game = active_games.get(ctx.guild.id)
    if not game:
        await ctx.send("No game is running!")
        return

    player = next((p for p in game.players if p.user == ctx.author), None)
    if player is None:
        await ctx.send("You are not in the game!")
        return

    # Simplified validation: check if the card is in the player's hand
    card = next((c for c in player.hand if str(c).lower() == card_name.lower()), None)
    if not card:
        await ctx.send("❌ Invalid card!")
        return
    
    # Check if the card is valid to play
    valid_moves = game.get_valid_moves(player)
    if card not in valid_moves:
        await ctx.send("❌ This card cannot be played!")
        return

    game.play_card(player, card)
    await ctx.send(f"{ctx.author.mention} played {card_name}.")
    winner = game.check_game_over()
    if winner:
        await ctx.send(f"🎉 {winner.user.mention} wins the game!")
        del active_games[ctx.guild.id]  # End the game

@bot.command(name="draw")
async def draw_card(ctx):
    game = active_games.get(ctx.guild.id)
    if not game:
        await ctx.send("No game is running!")
        return

    player = next((p for p in game.players if p.user == ctx.author), None)
    if player is None:
        await ctx.send("You are not in the game!")
        return

    card = player.draw_card(game.deck)
    await ctx.send(f"{ctx.author.mention} drew {card}.")
    if card:
        await ctx.send(f"{ctx.author.mention}'s hand: " + ", ".join(str(c) for c in player.hand))

@bot.command(name="rules")
async def rules(ctx):
    rules_text = """
    **UNO Game Rules:**
    - **Goal**: Be the first player to get rid of all your cards.
    - **Card Types**:
      - **Number cards (0-9)**: Played if the color or number matches the card on top of the discard pile.
      - **Skip**: Skips the next player's turn.
      - **Reverse**: Reverses the direction of play.
      - **Draw2**: The next player must draw 2 cards and skip their turn.
      - **Wild**: Allows the player to change the color in play.
      - **WildDraw4**: Allows the player to change the color and forces the next player to draw 4 cards and skip their turn.
    - **How to Play**:
      1. Players take turns in the order of the turn list.
      2. On your turn, play a card that matches the color or rank of the top card on the discard pile or play a wild card.
      3. If you can't play any cards, you must draw one from the deck.
      4. The first player to have no cards left wins the game.
    - **Special Notes**:
      - You can play a wild card at any time.
      - The game ends when a player has no cards left in their hand.
    """
    await ctx.send(rules_text)

@bot.command(name="hand")
async def show_hand(ctx):
    game = active_games.get(ctx.guild.id)
    if not game:
        await ctx.send("No game is running!")
        return

    player = next((p for p in game.players if p.user == ctx.author), None)
    if player is None:
        await ctx.send("You are not in the game!")
        return

    if not player.hand:
        await ctx.send(f"{ctx.author.mention}, you have no cards left!")
        return

    hand_cards = [f"{i+1}. {str(card)}" for i, card in enumerate(player.hand)]
    await ctx.send(f"{ctx.author.mention}, your hand: \n" + "\n".join(hand_cards))

AFK_FILE = "afk_data.json"

def load_afk_data():
    try:
        with open(AFK_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_afk_data(data):
    with open(AFK_FILE, "w") as f:
        json.dump(data, f, indent=4)

afk_users = load_afk_data()

@bot.command()
async def afk(ctx, *, reason: str = "AFK"):
    """Marks the user as AFK with an optional reason."""
    afk_users[str(ctx.author.id)] = {"reason": reason, "time": time.time()}
    save_afk_data(afk_users)

    embed = discord.Embed(
        description=f"✅ {ctx.author.mention}: You're now AFK with the status: **{reason}**",
        color=discord.Color.dark_gray()
    )
    await ctx.send(embed=embed)


@bot.command(name="i")
@is_admin()
async def set_or_show_rules(ctx, *, rules_text: str = None):
    if rules_text:

        rules_storage[ctx.guild.id] = rules_text
        
        await ctx.message.delete()

        if ctx.message.reference:

            original_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

            embed = discord.Embed(
                description=rules_text,
                color=discord.Color.from_rgb(0, 0, 0)
            )
            await original_message.reply(embed=embed)
        else:
            embed = discord.Embed(
                description=rules_text,
                color=discord.Color.from_rgb(0, 0, 0)
            )
            await ctx.send(embed=embed)
    else:
        stored_rules = rules_storage.get(ctx.guild.id, "⚠ No information has been set yet. Use `..info (text)` to set them.")

        embed = discord.Embed(
            description=stored_rules,
            color=discord.Color.from_rgb(0, 0, 0)
        )

        if ctx.message.reference:

            original_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)

            await original_message.reply(embed=embed)
        else:
            await ctx.send(embed=embed)

        await asyncio.sleep(0)
        await ctx.message.delete()


@bot.command(name="kick")
@is_admin()
async def kick(ctx, member: discord.Member = None, *, reason: str = None):
    if not member or not reason:
        msg = await ctx.send("⚠ **Usage:** `..kick @user <reason>`\nExample: `..kick @user Spamming`")
        await asyncio.sleep(3)
        await msg.delete()
        await ctx.message.delete() 
        return

    try:
        await member.send(f"You have been kicked from **{ctx.guild.name}**\nReason: {reason}")
    except discord.Forbidden:
        msg = await ctx.send("⚠ Could not DM the user about their kick.")
        await asyncio.sleep(3)
        await msg.delete()
        await ctx.message.delete() 
    except Exception as e:
        msg = await ctx.send(f"⚠ Error sending DM: {str(e)}")
        await asyncio.sleep(3)
        await msg.delete()
        await ctx.message.delete() 

    try:
        await member.kick(reason=reason)
        await ctx.message.add_reaction("✅")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except discord.Forbidden:
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except Exception as e:
        msg = await ctx.send(f"❌ Error kicking member: {str(e)}")
        await asyncio.sleep(3)
        await msg.delete()
        await ctx.message.delete() 

@bot.command(name="ban")
@is_admin()
async def ban(ctx, user: discord.User = None, *, reason: str = "No reason provided"):
    if not user:
        msg = await ctx.send("⚠ **Usage:** ..ban @user or ..ban <user_id> <reason>")
        await asyncio.sleep(3)
        await msg.delete()
        await ctx.message.delete()
        return
    
    guild = ctx.guild
    try:
        member = await guild.fetch_member(user.id)
    except discord.NotFound:
        member = None

    try:
        await user.send(f"You have been banned from **{guild.name}**\nReason: {reason}")
    except discord.Forbidden:
        msg = await ctx.send("⚠ Could not DM the user about their ban.")
        await asyncio.sleep(3)
        await msg.delete()
    try:
        await guild.ban(user, reason=reason)
        await ctx.message.add_reaction("✅")
    except discord.Forbidden:
        await ctx.message.add_reaction("❌")
    except Exception as e:
        msg = await ctx.send(f"❌ Error banning user: {str(e)}")
        await asyncio.sleep(3)
        await msg.delete()
    await asyncio.sleep(3)
    await ctx.message.delete()

@bot.command(name="unban")
@is_admin()
async def unban(ctx, user_id: int = None):
    if not user_id:
        msg = await ctx.send("⚠ **Usage:** ..unban <user_id>")
        await asyncio.sleep(3)
        await msg.delete()
        await ctx.message.delete()
        return
    
    guild = ctx.guild
    banned_user = None
    async for entry in guild.bans():
        if entry.user.id == user_id:
            banned_user = entry.user
            break

    if not banned_user:
        msg = await ctx.send("⚠ This user is not banned.")
        await asyncio.sleep(3)
        await msg.delete()
        await ctx.message.delete()
        return

    try:
        await guild.unban(banned_user)
        await ctx.message.add_reaction("✅")
    except discord.Forbidden:
        await ctx.message.add_reaction("❌")
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
        await member.send(f"You have been warned in {ctx.guild.name}.\nReason: {reason}")
        await ctx.message.delete()
        await ctx.send(f"✅ {member.mention} Warned! Reason: {reason}")

    except discord.Forbidden:
        await ctx.send(f"❌ Cannot DM {member.mention}")
        await asyncio.sleep(3)
        await ctx.message.delete() 

@bot.command()
async def cf(ctx):
    thinking_embed = discord.Embed(description="Thinking", color=discord.Color.blurple())
    thinking_message = await ctx.send(embed=thinking_embed)

  
    for _ in range(3):
        await asyncio.sleep(0.5)
        thinking_embed.description = "Thinking."
        await thinking_message.edit(embed=thinking_embed)
        await asyncio.sleep(0.5)
        thinking_embed.description = "Thinking.."
        await thinking_message.edit(embed=thinking_embed)
        await asyncio.sleep(0.5)
        thinking_embed.description = "Thinking..."
        await thinking_message.edit(embed=thinking_embed)

    outcomes = ['Heads', 'Tails']
    result = random.choice(outcomes)

    thinking_embed.description = f'{ctx.author.mention}, It\'s {result}!'
    await thinking_message.edit(embed=thinking_embed)

@bot.command()
@is_admin()
async def d(ctx):
    if not ctx.message.reference:
        await ctx.send("❌ You need to reply to a message to delete it.")
        await asyncio.sleep(3)
        await ctx.message.delete() 
        return

    message_to_delete = ctx.message.reference.resolved

    try:
        await message_to_delete.delete()
        
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
    description += "\n`..i`: Displays info."
    description += "\n`..ping`: Latency check."
    description += "\n`..kick @user <reason>`: Kicks user with reason."
    description += "\n`..ban @user <reason>`: Bans user with reason."
    description += "\n`..unban @user`: Un-bans user."
    description += "\n`..t @user <length>`: Times-out member."
    description += "\n`..ut @user`: Removes time-out from member."
    description += "\n`..l `: Locks current channel."
    description += "\n`..ul `: Unlocks current channel."
    description += "\n`..d `: Deletes message."
    description += "\n`..w @user <reason>`: Warns user."
    description += "\n`..p `: Purges messages."
    description += "\n`..s `: Snipes message."
    description += "\n`..cs `: Clears sniped message."
    description += "\n`..r `: Lists roles."
    description += "\n`..afk <reason>`: Sets AFK status."
    description += "\n`..cf `: Either heads or tails."
    description += "\n`..la`: Lists all current admins."

    if ctx.author.id == OWNER_ID:
        description += "\n\n`..aa @user`: Adds a new admin."
        description += "\n`..ra @user`: Removes an admin."
        description += "\n`..ha @user`: Adds hardcoded admin."
        description += "\n`..hr @user`: Removes hardcoded admin."
        description += "\n`..log <channel_id>`: Starts logging."
        description += "\n`..stlog `: Stops logging."
        description += "\n`..r add <role or role_id> @user `: Adds provided role to user."
        description += "\n`..r rem <role or role_id> @user `: Removes provided role from user."

    embed = discord.Embed(
        title="Bot Commands",
        description=description,
        color=discord.Color.from_rgb(0, 0, 0)
    )

    await ctx.send(embed=embed)


@bot.command(name="r")
@is_admin()
async def r(ctx, action: str = None, role_name: str = None, member: discord.Member = None):

    if ctx.author.id != OWNER_ID:
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(3)
        await ctx.message.delete()
        return
    
    # If no action is specified or action is invalid, list all roles in an embed
    if action is None:
        roles = [role.name for role in ctx.guild.roles]
        embed = discord.Embed(
            title="✅ Available Roles",
            description="\n".join(roles),
            color=discord.Color.green()
        )
        embed.set_footer(text="Roles are listed in alphabetical order.")
        await ctx.send(embed=embed)
        await asyncio.sleep(5)
        await ctx.message.delete()
        return

    if action.lower() == "add" and role_name and member:
        role = discord.utils.get(ctx.guild.roles, name=role_name) or discord.utils.get(ctx.guild.roles, id=int(role_name) if role_name.isdigit() else None)
        
        if role:
            try:
                await member.add_roles(role)
                msg = await ctx.send(f"✅ Assigned the role `{role.name}` to {member.mention}.")
                await asyncio.sleep(3)
                await msg.delete()
                await ctx.message.delete()
            except discord.Forbidden:
                msg = await ctx.send("❌ I do not have permission to assign roles.")
                await asyncio.sleep(3)
                await msg.delete()
                await ctx.message.delete()
            except discord.HTTPException as e:
                msg = await ctx.send(f"⚠️ Error assigning role: {e}")
                await asyncio.sleep(3)
                await msg.delete()
                await ctx.message.delete()
        else:
            msg = await ctx.send(f"❌ Role `{role_name}` not found.")
            await asyncio.sleep(3)
            await msg.delete()
            await ctx.message.delete()
    
    elif action.lower() == "rem" and role_name and member:
        role = discord.utils.get(ctx.guild.roles, name=role_name) or discord.utils.get(ctx.guild.roles, id=int(role_name) if role_name.isdigit() else None)
        
        if role:
            try:
                await member.remove_roles(role)
                msg = await ctx.send(f"✅ Removed the role `{role.name}` from {member.mention}.")
                await asyncio.sleep(3)
                await msg.delete()
                await ctx.message.delete()
            except discord.Forbidden:
                msg = await ctx.send("❌ I do not have permission to remove roles.")
                await asyncio.sleep(3)
                await msg.delete()
                await ctx.message.delete()
            except discord.HTTPException as e:
                msg = await ctx.send(f"⚠️ Error removing role: {e}")
                await asyncio.sleep(3)
                await msg.delete()
                await ctx.message.delete()
        else:
            msg = await ctx.send(f"❌ Role `{role_name}` not found.")
            await asyncio.sleep(3)
            await msg.delete()
            await ctx.message.delete()


    else:
        msg = await ctx.send("❌ Invalid usage. Use `..r` to list roles, `..r assign <role_name> @member` to assign a role, or `..r rem <role_name> @member` to remove a role.")
        await asyncio.sleep(3)
        await msg.delete()
        await ctx.message.delete()

@bot.command()
@is_admin()
async def t(ctx, member: discord.Member, duration: str):

    try:
        if member.id == OWNER_ID:
            await ctx.message.add_reaction("⚠️")
            await asyncio.sleep(1)
            await ctx.message.delete()
            return
        
        match = re.match(r"(\d+)([smh])", duration.lower())
        if not match:
            await ctx.send("⚠️ Invalid duration format. Please use `1s` for seconds, `1m` for minutes, or `1h` for hours.")
            return

        time_value = int(match.group(1))
        time_unit = match.group(2)

        if time_unit == "s":
            timeout_duration = timedelta(seconds=time_value)
        elif time_unit == "m":
            timeout_duration = timedelta(minutes=time_value)
        elif time_unit == "h":
            timeout_duration = timedelta(hours=time_value)

        timeout_end = discord.utils.utcnow() + timeout_duration
        await member.timeout(timeout_end)

        await ctx.message.add_reaction("✅")
        await asyncio.sleep(3)
        await ctx.message.delete()

    except discord.Forbidden:
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(3)
        await ctx.message.delete()
    except discord.HTTPException as e:
        await ctx.send(f"⚠️ Error while timing out: {e}")
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(3)
        await ctx.message.delete()

@bot.command()
@is_admin()
async def ut(ctx, member: discord.Member):

    try:
        await member.timeout(None)

        await ctx.message.add_reaction("✅")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except discord.Forbidden:
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(3)
        await ctx.message.delete() 
    except discord.HTTPException as e:
        await ctx.send(f"⚠️ Error while removing timeout: {e}")
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(3)
        await ctx.message.delete() 

@bot.command()
async def ping(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"{latency}ms")

sniped_messages = {}

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    # Store author, content, and timestamp
    sniped_messages[message.channel.id] = (message.author.name, message.content, datetime.utcnow())


@bot.command(name="s")
async def snipe(ctx):
    if ctx.channel.id in sniped_messages:
        author, content, timestamp = sniped_messages[ctx.channel.id]
        embed = discord.Embed(title="Sniped Message", description=content, color=discord.Color.red())
        embed.set_footer(text=f"Deleted message from {author}")
        embed.timestamp = timestamp  # Set the timestamp to when the message was deleted
        await ctx.send(embed=embed)
    else:
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(1)
        await ctx.message.delete()


@bot.command(name="cs")
async def clear_snipe(ctx):
    if ctx.channel.id in sniped_messages:
        del sniped_messages[ctx.channel.id]
        await ctx.message.add_reaction("✅")
        await asyncio.sleep(1)
        await ctx.message.delete() 
    else:
        await ctx.message.add_reaction("❌")
        await asyncio.sleep(1)
        await ctx.message.delete() 

@bot.command()
@is_admin()
async def p(ctx, amount: int = None):

    if ctx.message.reference:
        try:
            ref_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            messages = []
            async for msg in ctx.channel.history(limit=200):
                messages.append(msg)
                if msg.id == ref_msg.id:
                    break

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

    else:
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
    bot_member = ctx.guild.me
    owner1 = ctx.guild.get_member(707584409531842623)
    owner2 = ctx.guild.get_member(1343671645637967975)

    if not ctx.channel.permissions_for(bot_member).manage_channels:
        await ctx.message.add_reaction("❌")
        return
    
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)

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
            user = await bot.fetch_user(707584409531842623)

            if before.status == after.status:
                print(f"🔹 Status didn't change: {after.name} remains {after.status}")
                return

            message = f"<@707584409531842623> **{after.name}: {before.status} → {after.status}!** "

            await user.send(message)
            print(f"📩 Sent DM: {message}")

        except discord.Forbidden:
            print(f"❌ Cannot send DM to owner (Forbidden). Check Discord DM settings.")
        except discord.HTTPException as e:
            print(f"⚠️ Error sending DM: {e}")


def load_logging_state(guild_id=None):
    try:
        with open("logging_state.json", "r") as f:
            data = json.load(f)

            guild_data = data.get(str(guild_id), {})
            logging_active = guild_data.get("logging_active", False)
            logging_channel = guild_data.get("logging_channel", None)
            return logging_active, logging_channel
    except (FileNotFoundError, json.JSONDecodeError):
        return False, None

def save_logging_state(state: bool, channel_id: int, guild_id: int):
    try:
        with open("logging_state.json", "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    data[str(guild_id)] = {"logging_active": state, "logging_channel": channel_id}

    with open("logging_state.json", "w") as f:
        json.dump(data, f)

@bot.command()
async def log(ctx, channel_id: int = None):
    if ctx.author.id != OWNER_ID:
        await ctx.message.add_reaction("❌")
        return

    guild_id = ctx.guild.id

    if channel_id:
        save_logging_state(True, channel_id, guild_id)
        await ctx.send(f"Logging started. All interactions with the bot will now be logged in <#{channel_id}>.")
        await asyncio.sleep(3)
        await ctx.message.delete()
    else:
        logging_active, current_channel_id = load_logging_state(guild_id)
        if logging_active:
            await ctx.send(f"Logging is already active and logging to <#{current_channel_id}>.")
            await asyncio.sleep(3)
            await ctx.message.delete()
        else:
            await ctx.send("Logging is not active. Please provide a channel ID to start logging.")
            await asyncio.sleep(3)
            await ctx.message.delete()

@bot.command()
async def stlog(ctx):
    guild_id = ctx.guild.id
    logging_active, channel_id = load_logging_state(guild_id)

    if ctx.author.id != OWNER_ID:
        await ctx.message.add_reaction("❌")
        return

    if logging_active:
        save_logging_state(False, None, guild_id)
        await ctx.send("Logging stopped. No further interactions with the bot will be logged in this server.")
        await asyncio.sleep(3)
        await ctx.message.delete()
    else:
        await ctx.send("Logging is already stopped for this server.")
        await asyncio.sleep(3)
        await ctx.message.delete()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user_id = str(message.author.id)
    if user_id in afk_users:
        afk_info = afk_users.pop(user_id)
        save_afk_data(afk_users)

        afk_time = int(time.time() - afk_info["time"])
        minutes, seconds = divmod(afk_time, 60)

        embed = discord.Embed(
            description=f"✅ {message.author.mention}, welcome back! You were AFK for **{minutes}m {seconds}s**.",
            color=discord.Color.green()
        )
        await message.channel.send(embed=embed)

    for mention in message.mentions:
        mentioned_id = str(mention.id)
        if mentioned_id in afk_users:
            afk_info = afk_users[mentioned_id]
            afk_reason = afk_info["reason"]
            afk_time = int(time.time() - afk_info["time"])
            minutes, seconds = divmod(afk_time, 60)

            embed = discord.Embed(
                description=f"⚠️ {mention.mention} is AFK: **{afk_reason}**\n⏳ AFK for: **{minutes}m {seconds}s**",
                color=discord.Color.orange()
            )
            await message.channel.send(embed=embed)

    if message.author == bot.user:
        return

    guild_id = message.guild.id
    logging_active, channel_id = load_logging_state(guild_id)

    if logging_active and channel_id:
        command = message.content
        if command.startswith(".."):
            channel = bot.get_channel(channel_id)

            if channel:
                embed = discord.Embed(title="Bot Command Interaction Logged", color=discord.Color.green())
                embed.add_field(name="User", value=message.author.name)
                embed.add_field(name="Command", value=command)
                embed.add_field(name="Channel", value=message.channel.mention)
                embed.add_field(name="Time", value=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

                await channel.send(embed=embed)

    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    guild_id = before.guild.id
    logging_active, channel_id = load_logging_state(guild_id)
    if before.author == bot.user and logging_active and channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            embed = discord.Embed(title="Bot Message Edited", color=discord.Color.yellow())
            embed.add_field(name="Before", value=before.content or "No content")
            embed.add_field(name="After", value=after.content or "No content")
            embed.add_field(name="Channel", value=before.channel.mention)
            embed.add_field(name="Time", value=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
            await channel.send(embed=embed)

@bot.event
async def on_reaction_add(reaction, user):
    guild_id = reaction.message.guild.id
    logging_active, channel_id = load_logging_state(guild_id)
    if reaction.message.author == bot.user and logging_active and channel_id:
        channel = bot.get_channel(channel_id)
        if channel:
            embed = discord.Embed(title="Bot Message Reacted", color=discord.Color.blue())
            embed.add_field(name="User", value=user.name)
            embed.add_field(name="Reaction", value=str(reaction.emoji))
            embed.add_field(name="Message", value=reaction.message.content or "No content")
            embed.add_field(name="Channel", value=reaction.message.channel.mention)
            embed.add_field(name="Time", value=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
            await channel.send(embed=embed)


import os
TOKEN = os.getenv("watch")
bot.run(TOKEN)
