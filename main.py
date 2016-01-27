import discord
import emoji
import requests
import json
import re
import logging
import random

from datetime import datetime, timedelta
from riotwatcher import RiotWatcher
from secrets import *

logging.basicConfig(level=logging.INFO)

client = discord.Client()
client.login(USERNAME, PASSWORD)

last_sent = datetime.utcnow() - timedelta(1)

riot = RiotWatcher(RIOT_KEY)

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


def get_last_matches(summoner, classic_only=False):
    s = riot.get_summoner(name=summoner)
    matches = riot.get_recent_games(s['id'])
    if not matches:
        return []
    if not classic_only:
        return matches['games']
    return [x for x in matches['games'] if x['gameMode'] == 'CLASSIC']


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
def on_member_update(before, after):
    global last_sent
    if (datetime.utcnow() - last_sent).total_seconds() < 1800:
        return

    summoner = "JCena4Pres"
    if random.random() > 0.50:
        summoner = "jc4p"
    last_matches = get_last_matches(summoner, classic_only=True)
    if not last_matches:
        return

    match = last_matches[0]
    last_match_start = datetime.fromtimestamp(match['createDate'] / 1000)
    delta = (datetime.utcnow() - last_match_start).total_seconds()
    if delta > 3600:
        return

    stats = match['stats']
    won = stats['win']
    champ = riot.static_get_champion(match['championId'])
    kills = stats['championsKilled']
    deaths = stats['numDeaths']
    assists = stats['assists']
    kda = (kills + assists) / (deaths * 1.0)

    discord_user = None
    for m in client.servers[0].members:
        if summoner == "JCena4Pres" and m['name'] == 'imsteaky':
            discord_user = m
            break
        if summoner == 'jc4p' and m['name'] == 'kasra':
            discord_user = m
            break

    message = "Hey <@{}> ".format(discord_user.id)
    if won:
        if kda > 1.0:
            message += "gg. {}-{}-{} sick {} {} kda bro".format(kills, deaths, assists, champ['name'], kda)
        else:
            return
    else:
        if kda > 1.0:
            message += "gg. {}-{}-{}, you still lose. guess you can't carry as {}".format(kills, deaths, assists, champ['name'])
        elif random.random() > 0.50:
            message += "Guess what? YOUR :clap: {} :clap: {} : clap {} :clap: {} :clap: DOES :clap: NO :clap: DAMAGE :clap:".format(kills, deaths, assists, champ['name'])
        else:
            return
    client.send_message(client.servers[0].channels[0], message)
    last_sent = datetime.utcnow()


@client.event
def on_ready():
    print 'Logged in as'
    print client.user.name
    print client.user.id
    print '------'

if __name__ == "__main__":
    try:
        while True:
            client.run()
    except KeyboardInterrupt:
        pass

