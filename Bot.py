import discord # type: ignore
from discord.ext import commands # type: ignore
import asyncio
from datetime import datetime, timedelta
import json
import os

bot = commands.Bot(command_prefix='/', intents=discord.Intents.all(), help_command=None)


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
TOKEN = os.getenv("BOTTOKEN")  # Get token from environment
bot.run(TOKEN)
