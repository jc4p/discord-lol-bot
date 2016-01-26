import discord
import emoji
import requests
import json
import re

from secrets import *

client = discord.Client()
client.login(USERNAME, PASSWORD)

def get_champ_info(name):
    res = requests.get("http://api.champion.gg/champion/" + name.lower(), params={'api_key': CHAMPION_GG_KEY}).json()
    if 'error' in res:
        return "Sorry, couldn't find {}".format(name)
    res = res[0]
    skills = res['skills']['mostGames']['order']
    first_items = res['firstItems']['mostGames']['items']
    build = res['items']['mostGames']['items']
    
    response = "**" + res['key'] + '** \n'
    response += "First buy: " + ", ".join([x['name'] for x in first_items]) + "\n"
    response += "Skills: " + ", ".join(skills[:7]) + "\n"
    response += "Full build: " + ", ".join([x['name'] for x in build])

    return response


@client.event
def on_message(message):
    if message.content.startswith('!hello') and '<@140959950816935937>' in message.content:
        response = emoji.emojize(':wave: hello!')
        client.send_message(message.channel, response)
    elif message.content.startswith('!champgg'):
        champion = re.findall(r'\!champgg[\t ]+(\w+)?\D?', message.content)
        print champion
        if not champion or len(champion) > 1:
            client.send_message(message.channel, "I don't know who that is, try !champgg {Champion Name}")
        else:
            client.send_message(message.channel, get_champ_info(champion[0]))

@client.event
def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

if __name__ == "__main__":
    try:
        while True:
            client.run()
    except KeyboardInterrupt:
        pass

