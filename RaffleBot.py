import discord
import asyncio
import random
import CONFIG


# contains effectively static members, that can be referenced and changed
class RaffleBot:
    defaultSleepTime = 60 * 5  # 5 minutes
    guildMap = {}


intents = discord.Intents.none()
intents.guilds = True
intents.members = True
intents.guild_messages = True
intents.guild_reactions = True
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    # ignores messages by itself, cannot infinite loop
    if message.author == client.user:
        return

    # activator has permission to change roles for members
    has_permission = message.channel.permissions_for(message.author).manage_roles

    # initialize the role key for the guild
    guild_key = message.guild.id
    if guild_key not in RaffleBot.guildMap:
        RaffleBot.guildMap[str(guild_key)] = None

    # print help message
    if message.content.startswith('!rafflehelp'):
        await message.channel.send('I can raffle off anything to people who react to its message\n'
                                   'Get/Set the role assignment, use "None" to blank it: _!rafflerole <optional set '
                                   'role name>_\n'
                                   'Commence a raffle, only does role assignment if you have those permissions: '
                                   '_!raffle <prize name> <optional countdown time in seconds>_ '
                                   )

    # get or set the role assigned for the current guild
    elif message.content.startswith('!rafflerole'):
        # split cap means role name can have spaces
        args = message.content.split(' ', 1)

        # if no role parameter, returns the current role
        if len(args) < 2:
            role_obj = message.guild.get_role(RaffleBot.guildMap[str(guild_key)])
            await message.channel.send('RaffleBot role assignment currently ' + (
                'None' if role_obj is None else role_obj.name))
            return

        # stops execution if the activator doesn't have permission
        if not has_permission:
            await message.channel.send(
                'RaffleBot role assignment cannot be changed by someone without manage_roles permissions')
            return

        # clears the role assignment if 'None' is passed as a parameter
        new_role = args[1].lower()
        if new_role == 'none':
            await message.channel.send('RaffleBot role assignment changed to None')
            return

        # finds the role by name and sets it to the guild
        for x in message.guild.roles:
            if x.name.lower() == new_role:
                RaffleBot.guildMap[str(guild_key)] = x.id
                await message.channel.send(
                    'RaffleBot role assignment changed to ' + message.guild.get_role(x.id).name)
                return

        await message.channel.send('RaffleBot could not find role named ' + args[1])

    # raffle action, will set a role to the winner if the activator has permission
    elif message.content.startswith('!raffle'):
        args = message.content.split()
        sleep_time = RaffleBot.defaultSleepTime

        # requires a message that indicates the thing being raffled, with optional duration
        if len(args) < 2:
            await message.channel.send(
                'Syntax for raffle is _!raffle <prize name> <optional countdown time in seconds>_')
            return

        # parses for duration parameter
        if (len(args) > 2) and (args[2].isnumeric()):
            sleep_time = int(args[2])

        # creates raffle message, and waits for responses
        raffle_msg = await message.channel.send('Raffling off ' + args[1])
        await raffle_msg.add_reaction('✅')
        await asyncio.sleep(sleep_time)

        # retrieves message in order to get the updated reaction object
        raffle_msg = await raffle_msg.channel.fetch_message(raffle_msg.id)
        raffle_rea = raffle_msg.reactions[0]
        await raffle_rea.remove(client.user)
        raffle_usr = raffle_rea.users()

        # gets the current role, could have been changed during sleep period
        role_id = RaffleBot.guildMap[str(guild_key)]
        character_role = (None if (role_id is None) or (not has_permission) else raffle_msg.guild.get_role(role_id))

        # randomize possible users to find winner
        raffle_usr_rand = await raffle_usr.flatten()
        random.shuffle(raffle_usr_rand)

        # iterate through users to find valid member who doesn't have the role already
        raffle_win = None
        for x in raffle_usr_rand:
            raffle_win = raffle_msg.guild.get_member(x.id)
            if raffle_win is not None:
                if (character_role is not None) and (character_role in raffle_win.roles):
                    raffle_win = None
                else:
                    break

        # all possible users either left the guild after reacting or already have the role
        if raffle_win is None:
            await message.channel.send('No valid members for ' + args[1])
            return

        # only sets member role if rafflerole is set and activator has permission
        if character_role is not None:
            await raffle_win.add_roles(character_role)
        await message.channel.send("<@" + str(raffle_win.id) + "> won the raffle for " + args[1])


client.run(CONFIG.RB_DISCORD_TOKEN)
