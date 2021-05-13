import requests
import discord
import CONFIG


key = CONFIG.TB_TRELLO_APIKEY
token = CONFIG.TB_TRELLO_TOKEN
base_url = "https://api.trello.com/1/"
MAX_CARDS = 2

intents = discord.Intents.none()
intents.guilds = True
intents.members = True
intents.guild_messages = True
client = discord.Client(intents=intents)


def get_all_boards(user_name):
    url = f"{base_url}members/{user_name}/boards"
    querystring = {"key": key, "token": token, "fields": "id,name"}
    response = requests.request("GET", url, params=querystring)
    all_boards = response.json()
    return all_boards


def get_board(user_name, board_name):
    all_boards = get_all_boards(user_name)
    for x in all_boards:
        if x['name'].lower() == board_name.lower():
            return x['id']
    return None


def get_all_lists(board_id):
    url = f"{base_url}boards/{board_id}/lists"
    querystring = {"key": key, "token": token, "fields": "id,name"}
    response = requests.request("GET", url, params=querystring)
    all_lists = response.json()
    return all_lists


def get_list(board_id, list_name):
    all_lists = get_all_lists(board_id)
    for x in all_lists:
        if x['name'].lower() == list_name.lower():
            return x['id']
    return None


def create_card(list_id, card_name):
    url = f"{base_url}cards"
    querystring = {"name": card_name, "idList": list_id, "key": key, "token": token}
    response = requests.request("POST", url, params=querystring)
    card_id = response.json()["id"]
    return card_id


def get_all_cards(board_id):
    url = f"{base_url}boards/{board_id}/cards"
    querystring = {"key": key, "token": token, "fields": "id,name,idList"}
    response = requests.request("GET", url, params=querystring)
    all_cards = response.json()
    return all_cards


def get_user_cards(board_id, card_name):
    all_cards = get_all_cards(board_id)
    user_cards = []
    for x in all_cards:
        if x['name'].startswith(card_name):
            user_cards.append(x)
    return user_cards


def get_user_cards_by_list(board_id, card_name):
    user_cards = get_user_cards(board_id, card_name)
    querystring = {"key": key, "token": token, "fields": "id,name"}
    cards_by_list = {}
    for x in user_cards:
        if x['idList'] not in cards_by_list:
            url = f"{base_url}lists/{x['idList']}"
            response = requests.request("GET", url, params=querystring)
            brd = response.json()
            cards_by_list[brd['id']] = {}
            cards_by_list[brd['id']]['name'] = brd['name']
            cards_by_list[brd['id']]['cards'] = []
        cards_by_list[x['idList']]['cards'].append(x)
    return cards_by_list


board = get_board(CONFIG.TB_USERNAME, CONFIG.TB_BOARDNAME)
li = get_list(board, CONFIG.TB_LISTNAME)


@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    # ignores messages by itself, cannot infinite loop
    if message.author == client.user:
        return

    # print help message
    if message.content.startswith('!trellohelp'):
        await message.channel.send('I can add request tickets to Trello, and print your ticket statuses\n'
                                   'Get the status of your requests: _!trellostatus_\n'
                                   'Create a trello request: _!trello <description of request>_'
                                   )

    # trello status action, will print all the cards associated with a member
    elif message.content.startswith('!trellostatus'):
        name = message.author.name
        lists = get_user_cards_by_list(board, name)

        msg = f"Current cards for {name}\n"
        for x in lists:
            msg += f"Cards in {lists[x]['name']}:\n"
            for c in lists[x]['cards']:
                msg += f"{c['name']}\n"

        await message.channel.send(msg)

    # trello action, will create a card with the member request
    elif message.content.startswith('!trello'):
        args = message.content.split(' ', 1)
        name = message.author.name

        # requires a message that indicates the request
        if len(args) < 2:
            await message.channel.send('Syntax for trello request is _!trello <description of request>_')
            return

        if len(get_user_cards(board, name)) >= MAX_CARDS:
            await message.channel.send(f'You cannot have more than {MAX_CARDS} active requests')
            return

        # creates card and prints result
        card_text = f"{name} - {args[1]}"
        create_card(li, card_text)
        await message.channel.send(f'Created card: {card_text}')


client.run(CONFIG.TB_DISCORD_TOKEN)
