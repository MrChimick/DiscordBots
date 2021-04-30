import discord
import asyncio
import random
import config


class RaffleBot:
    defaultSleepTime = config.RB_SLEEP
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
    if message.author == client.user:
        return

    hasPermission = message.channel.permissions_for(message.author).manage_roles
    guildKey = message.guild.id
    if guildKey not in RaffleBot.guildMap:
        RaffleBot.guildMap[str(guildKey)] = None

    if message.content.startswith('!rafflehelp'):
        await message.channel.send('**RaffleBot** can raffle off anything to people who react to its message\n'
                                   'Get/Set the role assignment, use "None" to blank it: _!rafflerole <optional set role name>_\n'
                                   'Commence a raffle, only does role assignment if you have those permissions: _!raffle <character name> <optional countdown time in seconds>_'
                                   )

    elif message.content.startswith('!rafflerole'):
        args = message.content.split(' ', 1)

        if len(args) < 2:
            await message.channel.send('RaffleBot role assignment currently ' + (
                'None' if RaffleBot.guildMap[str(guildKey)] is None else message.guild.get_role(RaffleBot.guildMap[str(guildKey)]).name))
            return

        if not hasPermission:
            await message.channel.send(
                'RaffleBot role assignment cannot be changed by someone without manage_roles permissions')
            return

        newRole = args[1].lower()
        if newRole == 'none':
            await message.channel.send('RaffleBot role assignment changed to None')
            return

        for x in message.guild.roles:
            if x.name.lower() == newRole:
                RaffleBot.guildMap[str(guildKey)] = x.id
                await message.channel.send(
                    'RaffleBot role assignment changed to ' + message.guild.get_role(RaffleBot.guildMap[str(guildKey)]).name)
                return

        await message.channel.send('RaffleBot could not find role named ' + args[1])

    elif message.content.startswith('!raffle'):
        args = message.content.split()
        sleepTime = RaffleBot.defaultSleepTime

        if len(args) < 2:
            await message.channel.send(
                'Syntax for raffle is _!raffle <character name> <optional countdown time in seconds>_')
            return

        if (len(args) > 2) and (args[2].isnumeric()):
            sleepTime = int(args[2])

        raffleMsg = await message.channel.send('Raffling off ' + args[1])
        await raffleMsg.add_reaction('✅')
        await asyncio.sleep(sleepTime)

        raffleMsg = await raffleMsg.channel.fetch_message(raffleMsg.id)
        raffleRea = raffleMsg.reactions[0]
        await raffleRea.remove(client.user)
        raffleUsr = raffleRea.users()

        characterRole = (
            None if (RaffleBot.guildMap[str(guildKey)] == None) or (not hasPermission) else raffleMsg.guild.get_role(RaffleBot.guildMap[str(guildKey)]))

        raffleUsrRand = await raffleUsr.flatten()
        random.shuffle(raffleUsrRand)

        raffleWin = None
        for x in raffleUsrRand:
            raffleWin = raffleMsg.guild.get_member(x.id)
            if raffleWin != None:
                if (characterRole != None) and (characterRole in raffleWin.roles):
                    raffleWin = None
                else:
                    break

        if raffleWin == None:
            await message.channel.send('No valid members for ' + args[1])
            return

        if (characterRole != None):
            await raffleWin.add_roles(characterRole)
        await message.channel.send("<@" + str(raffleWin.id) + "> won the raffle for " + args[1])


client.run(config.RB_TOKEN)