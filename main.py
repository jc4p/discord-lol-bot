import discord
import emoji
import requests
import json
import re
import logging
import random

from datetime import datetime
from riotwatcher import RiotWatcher
from secrets import *

logging.basicConfig(level=logging.INFO)

client = discord.Client()
client.login(USERNAME, PASSWORD)

last_match_message_sent = datetime.utcnow()

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


def get_last_match(summoner, classic_only=False):
    s = riot.get_summoner(name=summoner)
    matches = riot.get_match_list(s['id'])
    if not matches:
        return None
    if not classic_only:
        return matches['matches'][0]
    classic_matches = [x for x in matches['matches'] if x['matchMode'] == 'CLASSIC']
    if not classic_matches:
        return None
    return classic_matches[0]


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
    if (datetime.utcnow() - last_match_message_sent).total_seconds() < 1800:
        pass
    summoner = "JCena4Pres"
    if random.random() > 0.50:
        summoner = "jc4p"
    last_match = get_last_match(summoner, classic_only=True)
    if not last_match:
        pass
    last_match_time = datetime.fromtimestamp(last_match['timestamp'] / 1000)
    delta = (datetime.utcnow() - last_match_time).total_seconds()
    if delta > 1800:
        pass
    match = riot.get_match(last_match['matchId'])
    player = None
    for p in match['participantIdentities']:
        if p['player']['summonerName'] == summoner:
            player = p
            break
    details = None
    for d in match['participants']:
        if p['participantId'] == player['participantId']:
            details = d
            break
    team = match['teams'][0] if match['teams']['0']['teamId'] == player['teamId'] else match['teams'][1]

    won = team['winner']
    champ = riot.static_get_champion(details['championId'])
    kills = details['kills']
    deaths = details['deaths']
    assists = details['assists']
    kda = (kills + assists) / (deaths * 1.0)
    did_most_damage = all([x['stats']['totalDamageDealtToChamps'] <= details['stats']['totalDamageDealtToChamps'] for x in match['participants']])

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
        if did_most_damage:
            message += "nice {}-{}-{} {} moves, you did the most damage too!".format(kills, deaths, assists, champ['name'])
        elif kda > 1.0:
            message += "gg {}-{}-{} sick {} {} kda bro".format(kills, deaths, assists, champ['name'], champ['kda'])
    else:
        if kda > 1.0:
            message += "gg. {}-{}-{}, you still lose. guess you can't carry as {}".format(kills, deaths, assists, champ['name'])
        elif not did_most_damage:
            message += "Guess what? YOUR :clap: {} :clap: {} : clap {} :clap: {} :clap: DOES :clap: NO :clap: DAMAGE :clap:".format(kills, deaths, assists, champ['name'])
        else:
            message += "lol nice {}-{}-{} {} loss".format(kills, deaths, assists, champ['name'])
    client.send_message(client.servers[0].channels[0], message)
    last_match_message_sent = datetime.utcnow()


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

